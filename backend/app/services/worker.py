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
                continue
            
            print(f"Processing alarm: {alarm}")
            # Get user notify settings
            user_id = alarm.get("user_id")
            notify_settings = db.query(UserNotify).filter_by(user_id=user_id).first()
            
            if notify_settings:
                message = f"Stock Alert: {alarm['stock_name']} ({alarm['stock_code']})\n" \
                          f"Reason: {alarm['reason']}\n" \
                          f"Value: {alarm['value']:.2f}\n" \
                          f"Price: {alarm['price']}\n" \
                          f"Time: {alarm['time']}"
                
                if notify_settings.email:
                    NotificationService.send_email(notify_settings.email, "Stock Alert", message)
                
                if notify_settings.telegram_id:
                    NotificationService.send_telegram(notify_settings.telegram_id, message)
                elif settings.TELEGRAM_CHAT_ID:
                    # Fallback to global chat_id from env
                    NotificationService.send_telegram(settings.TELEGRAM_CHAT_ID, message)
            else:
                print(f"No notify settings for user {user_id}")
            
    except Exception as e:
        print(f"Worker failed: {e}")
    finally:
        db.close()
