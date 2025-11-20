from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

scheduler = BackgroundScheduler()

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())

def add_job(func, seconds=60, args=None, id=None):
    scheduler.add_job(
        func,
        trigger=IntervalTrigger(seconds=seconds),
        args=args,
        id=id,
        replace_existing=True
    )
