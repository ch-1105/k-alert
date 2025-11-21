from app.core.queue import alarm_queue
from app.services.notification import NotificationService
from app.core.database import SessionLocal
from app.models import UserNotify
from app.core.config import settings
import time

def process_alarms():
    print("Processing alarms...")
    db = SessionLocal()
    try:
        # Process all pending alarms
        while True:
            alarm = alarm_queue.pop_alarm()
            if not alarm:
                time.sleep(1) # Wait 1s before next poll (prevents busy loop if Redis is down)
                continue
            
            print(f"Processing alarm: {alarm}")
            # Get user notify settings
            user_id = alarm.get("user_id")
            notify_settings = db.query(UserNotify).filter_by(user_id=user_id).first()
            
            # Prepare message
            message = f"Stock Alert: {alarm['stock_name']} ({alarm['stock_code']})\n" \
                      f"Reason: {alarm['reason']}\n" \
                      f"Value: {alarm['value']:.2f}\n" \
                      f"Price: {alarm['price']}\n" \
                      f"Time: {alarm['time']}"

            # 1. Telegram Notification
            tg_id = None
            if notify_settings and notify_settings.telegram_id:
                tg_id = notify_settings.telegram_id
            elif settings.TELEGRAM_CHAT_ID:
                tg_id = settings.TELEGRAM_CHAT_ID
            
            if tg_id:
                NotificationService.send_telegram(tg_id, message)
            else:
                print(f"No Telegram ID configured for user {user_id} or global fallback")

            # 2. Email Notification
            if notify_settings and notify_settings.email:
                NotificationService.send_email(notify_settings.email, "Stock Alert", message)
            
    except Exception as e:
        print(f"Worker failed: {e}")
    finally:
        db.close()
