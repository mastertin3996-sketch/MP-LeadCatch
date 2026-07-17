from pathlib import Path

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import Base, engine, get_db
from backend.models import LeadModel
from backend.schemas import AdminLoginSchema, LeadResponseSchema, LeadSchema, StatusUpdateSchema

Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="MarioProg Lead & CRM System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)


def send_telegram_message(background_tasks: BackgroundTasks, lead_id: int, phone: str, name: str, service: str, comment: str | None):
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return

    message_text = (
        f"<b>🔥 Новий лід</b>\n"
        f"<b>Ім'я:</b> {name}\n"
        f"<b>Телефон:</b> {phone}\n"
        f"<b>Послуга:</b> {service}\n"
        f"<b>Коментар:</b> {comment or '—'}"
    )

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "📞 Зателефонувати", "url": f"tel:{phone}"},
                {"text": "✅ Оброблено", "callback_data": f"processed_{lead_id}"},
            ]
        ]
    }

    async def _send():
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": settings.TELEGRAM_CHAT_ID,
                        "text": message_text,
                        "parse_mode": "HTML",
                        "reply_markup": keyboard,
                    },
                    timeout=10.0,
                )
        except Exception:
            return

    background_tasks.add_task(_send)


def get_current_admin(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    token = None
    if credentials is not None and credentials.scheme.lower() == "bearer":
        token = credentials.credentials

    if token is None:
        token = request.headers.get("x-admin-token")

    if token is None:
        token = request.headers.get("authorization", "").replace("Bearer ", "", 1).strip()

    if token in {settings.ADMIN_TOKEN, settings.ADMIN_PASSWORD, settings.ADMIN_USERNAME}:
        return True

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication required")
    if credentials.credentials != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return True


@app.post("/api/v1/admin/login")
def admin_login(payload: AdminLoginSchema):
    if payload.username != settings.ADMIN_USERNAME or payload.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": settings.ADMIN_TOKEN, "token_type": "bearer"}


@app.post("/api/v1/leads", response_model=LeadResponseSchema, status_code=201)
def create_lead(payload: LeadSchema, db: Session = Depends(get_db), background_tasks=None):
    lead = LeadModel(
        name=payload.name,
        phone=payload.phone,
        service=payload.service,
        comment=payload.comment,
        status="Новий",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@app.get("/api/v1/leads", response_model=list[LeadResponseSchema])
def list_leads(db: Session = Depends(get_db), _: bool = Depends(get_current_admin)):
    leads = db.query(LeadModel).order_by(LeadModel.created_at.desc()).all()
    return leads


@app.get("/api/v1/stats")
def get_stats(db: Session = Depends(get_db), _: bool = Depends(get_current_admin)):
    total = db.query(LeadModel).count()
    new_count = db.query(LeadModel).filter(LeadModel.status == "Новий").count()
    in_progress_count = db.query(LeadModel).filter(LeadModel.status == "В процесі").count()
    processed_count = db.query(LeadModel).filter(LeadModel.status == "Оброблено").count()
    deferred_count = db.query(LeadModel).filter(LeadModel.status == "Відкладено").count()

    return {
        "total": total,
        "new": new_count,
        "in_progress": in_progress_count,
        "processed": processed_count,
        "deferred": deferred_count,
    }


@app.patch("/api/v1/leads/{lead_id}/status", response_model=LeadResponseSchema)
def update_lead_status(lead_id: int, payload: StatusUpdateSchema, db: Session = Depends(get_db), _: bool = Depends(get_current_admin)):
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.status = payload.status
    db.commit()
    db.refresh(lead)
    return lead


@app.post("/api/v1/telegram-webhook")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    callback_query = data.get("callback_query")
    if not callback_query:
        return {"ok": True}

    callback_data = callback_query.get("data", "")
    if not callback_data.startswith("processed_"):
        return {"ok": True}

    lead_id = int(callback_data.split("_", 1)[1])
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        return {"ok": False}

    lead.status = "Оброблено"
    db.commit()

    message = callback_query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")

    if chat_id and message_id:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/editMessageText",
                json={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": "✅ Оброблено",
                    "parse_mode": "HTML",
                },
                timeout=10.0,
            )
            await client.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/editMessageReplyMarkup",
                json={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "reply_markup": {"inline_keyboard": []},
                },
                timeout=10.0,
            )

    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    return FileResponse(FRONTEND_DIR / "dashboard.html")


@app.get("/dashboard.html", response_class=HTMLResponse)
def serve_dashboard_html():
    return FileResponse(FRONTEND_DIR / "dashboard.html")


@app.get("/health")
def health_check():
    return {"status": "ok"}
