from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

scheduler = BackgroundScheduler()

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())

def add_job(func, seconds=60, args=None, id=None, jitter=3):
    """
    Add a scheduled job with jitter to avoid pattern detection.
    
    Args:
        func: Function to execute
        seconds: Base interval in seconds
        args: Arguments to pass to the function
        id: Unique job identifier
        jitter: Random variation in seconds (±jitter). Default is 3 seconds.
                For example, with seconds=15 and jitter=3, actual interval will be 12-18 seconds.
    """
    scheduler.add_job(
        func,
        trigger=IntervalTrigger(seconds=seconds, jitter=jitter),
        args=args,
        id=id,
        replace_existing=True,
        max_instances=3  # Allow up to 3 overlapping instances to prevent skipping
    )
