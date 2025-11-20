import smtplib
from email.mime.text import MIMEText
from email.header import Header
import requests
from app.core.config import settings
from loguru import logger

class NotificationService:
    @staticmethod
    def send_email(to_addr: str, subject: str, content: str):
        """
        Send email using SMTP.
        """
        if not settings.SMTP_HOST or not settings.SMTP_USER:
            logger.warning("SMTP not configured")
            return False
            
        try:
            logger.info(f"Sending email to {to_addr}")
            message = MIMEText(content, 'plain', 'utf-8')
            message['From'] = Header(settings.SMTP_USER, 'utf-8')
            message['To'] = Header(to_addr, 'utf-8')
            message['Subject'] = Header(subject, 'utf-8')

            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, [to_addr], message.as_string())
            server.quit()
            logger.success(f"Email sent to {to_addr}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    @staticmethod
    def send_telegram(chat_id: str, message: str):
        """
        Send Telegram message.
        """
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram token not configured")
            return False
            
        try:
            logger.info(f"Sending telegram to {chat_id}")
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message
            }
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                logger.success(f"Telegram sent to {chat_id}")
                return True
            else:
                logger.error(f"Telegram failed: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to send telegram: {e}")
            return False
