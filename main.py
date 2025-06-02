from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Visit, Base
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # za razvoj je * OK, v produkciji bolj restriktivno
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency za pridobivanje SQLAlchemy seje
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class VisitInput(BaseModel):
    ip: str | None = None

@app.post("/visit")
async def register_visit(request: Request, db: Session = Depends(get_db)):
# 1. Ignoriraj OPTIONS zahtevke
    if request.method == "OPTIONS":
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # 2. Pridobi IP naslov
    x_forwarded_for = request.headers.get("x-forwarded-for")
    ip = x_forwarded_for.split(",")[0] if x_forwarded_for else request.client.host

    # 3. Ignoriraj proxy IP (če je to IP tvoje virtualke / strežnika)
    if ip == "212.101.137.109":  # <- prilagodi ta IP po potrebi
        print(f"[IGNORED] {datetime.utcnow()} - Proxy IP ignored: {ip}")
        return {"message": "Proxy visit ignored", "ip": ip}

    # 4. Zabeleži obisk
    print(f"[VISIT] {datetime.utcnow()} - Visit from IP: {ip}")
    visit = Visit(ip_address=ip, timestamp=datetime.utcnow())
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return {"message": "Visit recorded", "ip": ip}

@app.get("/visits")
def list_visits(db: Session = Depends(get_db)):
    visits = db.query(Visit).order_by(Visit.timestamp.desc()).all()
    return [
        {"ip": v.ip_address, "timestamp": v.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
        for v in visits
    ]

@app.delete("/visits")
def delete_all_visits(db: Session = Depends(get_db)):
    deleted = db.query(Visit).delete()
    db.commit()
    return {"message": f"Deleted {deleted} visits"}

@app.get("/visits/count")
def visit_count(db: Session = Depends(get_db)):
    count = db.query(Visit).count()
    return {"count": count}