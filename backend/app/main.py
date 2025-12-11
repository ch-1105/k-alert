from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db
from app.core.scheduler import start_scheduler, add_job
from app.services.scanner import scan_stocks
from app.services.worker import process_alarms
from app.api import stocks, strategies, notifications
import threading

app = FastAPI(title="Stock Monitor API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stocks.router, prefix="/api/stock", tags=["stocks"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])

@app.on_event("startup")
def startup_event():
    init_db()
    start_scheduler()
    # Add scanner job (every 120 seconds with randomization in scanner)
    add_job(scan_stocks, seconds=120, id="scan_stocks")
    
    # Start worker in a separate thread
    worker_thread = threading.Thread(target=process_alarms, daemon=True)
    worker_thread.start()

@app.get("/")
def read_root():
    return {"message": "Stock Monitor API is running"}
