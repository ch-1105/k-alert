from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import UserNotify
from pydantic import BaseModel

router = APIRouter()

class NotifyUpdate(BaseModel):
    email: str = None
    telegram_id: str = None

@router.get("/")
def get_notify(db: Session = Depends(get_db)):
    notify = db.query(UserNotify).filter(UserNotify.user_id == 1).first()
    if not notify:
        return {}
    return notify

@router.get("/settings")
def get_notify_settings(db: Session = Depends(get_db)):
    """Alias for get_notify for better API semantics"""
    return get_notify(db)

@router.post("/update")
def update_notify(notify: NotifyUpdate, db: Session = Depends(get_db)):
    db_notify = db.query(UserNotify).filter(UserNotify.user_id == 1).first()
    if not db_notify:
        db_notify = UserNotify(user_id=1, email=notify.email, telegram_id=notify.telegram_id)
        db.add(db_notify)
    else:
        db_notify.email = notify.email
        db_notify.telegram_id = notify.telegram_id
    
    db.commit()
    return {"status": "ok"}
