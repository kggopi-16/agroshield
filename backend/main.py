import sys
import os
# Add the project root to sys.path to ensure 'from backend' imports work during deployment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, UploadFile, File, WebSocket, HTTPException
from datetime import datetime
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
from sqlalchemy import func
import uvicorn

# DB
from backend.database import Base, engine, get_db

# Models
from backend.models.inventory import InventoryItem
from backend.models.farmer import Farmer

# Services
from backend.services.gemini_service import chat
from backend.pest_detection.predict import load_model, predict

from backend.models.pest_history import PestHistory
from backend.models.sensor_reading import SensorReading
import shutil

UPLOAD_DIR = os.path.join(os.path.abspath("backend"), "data", "pests")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

# -------------------------------
# INIT
# -------------------------------
Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def startup():
    load_model()

# -------------------------------
# FRONTEND SERVE
# -------------------------------
FRONTEND_PATH = os.path.abspath("frontend")

app.mount("/static", StaticFiles(directory=FRONTEND_PATH), name="static")

@app.get("/")
def serve_ui():
    return FileResponse(os.path.join(FRONTEND_PATH, "agri-officer-portal.html"))

# -------------------------------
# SCHEMAS
# -------------------------------
class InventoryCreate(BaseModel):
    name: str
    quantity: int

class FarmerCreate(BaseModel):
    name: str
    location: str
    acres: float
    crop_type: str
    aadhaar: str

class ChatRequest(BaseModel):
    message: str

# -------------------------------
# INVENTORY
# -------------------------------
@app.post("/api/inventory")
def add_item(item: InventoryCreate, db: Session = Depends(get_db)):
    db_item = InventoryItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/api/inventory")
def get_items(db: Session = Depends(get_db)):
    return db.query(InventoryItem).all()

# -------------------------------
# FARMERS
# -------------------------------
@app.post("/api/farmers")
def add_farmer(farmer: FarmerCreate, db: Session = Depends(get_db)):
    f = Farmer(**farmer.dict())
    db.add(f)
    db.commit()
    db.refresh(f)
    return f

@app.get("/api/farmers")
def get_farmers(search: str = None, crop: str = None, db: Session = Depends(get_db)):
    query = db.query(Farmer)
    if search:
        query = query.filter((Farmer.name.ilike(f"%{search}%")) | (Farmer.location.ilike(f"%{search}%")))
    if crop:
        query = query.filter(Farmer.crop_type == crop)
    return query.all()

# -------------------------------
# GEMINI CHAT
# -------------------------------
@app.post("/api/chat")
def gemini_chat(req: ChatRequest):
    try:
        return {"response": chat(req.message)}
    except Exception as e:
        return {"error": str(e)}

# -------------------------------
# PEST DETECTION (ONNX FAST)
# -------------------------------
@app.post("/api/pest-detect")
async def pest_detect(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        
        # Save Image to Disk
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as buffer:
            buffer.write(contents)

        # Run Prediction
        try:
            result = predict(contents)
        except Exception as pe:
            print(f"PREDICTION ERROR: {str(pe)}")
            return {"pest": "Detection Error", "confidence": 0, "advice": "Model inference failed. Please try again."}

        # Save to DB
        history = PestHistory(
            pest=result["pest"],
            confidence=result["confidence"],
            advice=result["advice"],
            image_name=filename
        )

        db.add(history)
        db.commit()
        db.refresh(history)

        return result
    except Exception as e:
        print(f"DETECTION ERROR: {str(e)}")
        return {"error": str(e)}, 500

# -------------------------------
# SENSOR DATA
# -------------------------------
latest_data = {
    "humidity": 0,
    "moisture": 0,
    "temperature": 0,
    "ph": 0
}

@app.get("/api/sensor")
def get_sensor():
    return latest_data

@app.get("/api/sensor-history")
def get_sensor_history(db: Session = Depends(get_db)):
    return db.query(SensorReading).order_by(SensorReading.timestamp.desc()).limit(20).all()

@app.post("/api/sensor")
async def update_sensor(data: dict, db: Session = Depends(get_db)):
    global latest_data
    print(f"DEBUG: Received Sensor Data: {data}")
    latest_data.update(data)

    # Persist sensor reading
    reading = SensorReading(
        humidity=float(latest_data.get("humidity", 0)),
        moisture=float(latest_data.get("moisture", 0)),
        temperature=float(latest_data.get("temperature", 25)),
        ph=float(latest_data.get("ph", 6.5))
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    # BROADCAST to all live WebSocket users
    for client in clients:
        try:
            await client.send_json(latest_data)
        except:
            if client in clients:
                clients.remove(client)

    return {"status": "updated"}

# -------------------------------
# WEBSOCKET (ESP32 LIVE)
# -------------------------------
clients = []

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.append(ws)
    print(f"DEBUG: New WebSocket connection. Total clients: {len(clients)}")

    try:
        while True:
            data = await ws.receive_json()

            global latest_data
            latest_data.update(data)

            for client in clients:
                await client.send_json(latest_data)

    except:
        clients.remove(ws)

# -------------------------------
# HEALTH
# -------------------------------
@app.get("/api/health")
def health():
    return {"status": "running"}



@app.get("/api/pest-analytics")
def pest_analytics(db: Session = Depends(get_db)):
    total = db.query(PestHistory).count()

    most_common = (
        db.query(PestHistory.pest, func.count(PestHistory.pest))
        .group_by(PestHistory.pest)
        .order_by(func.count(PestHistory.pest).desc())
        .first()
    )

    avg_conf = db.query(func.avg(PestHistory.confidence)).scalar()

    return {
        "total_detections": total,
        "most_common_pest": most_common[0] if most_common else None,
        "average_confidence": round(avg_conf or 0, 2)
    }

@app.get("/api/dashboard-stats")
def dashboard_stats(db: Session = Depends(get_db)):
    # REAL COUNTS from DB
    farmer_count = db.query(Farmer).count()
    pest_count = db.query(PestHistory).count()
    inventory_count = db.query(InventoryItem).count()
    avg_ph = db.query(func.avg(SensorReading.ph)).scalar() or 6.5
    
    # Fake critical for demo effect if low moisture detected recently
    latest_moisture = db.query(SensorReading.moisture).order_by(SensorReading.timestamp.desc()).first()
    critical = 1 if latest_moisture and latest_moisture[0] < 30 else 0

    return {
        "active_farms": farmer_count,
        "pest_alerts": pest_count,
        "inventory_count": inventory_count,
        "avg_ph": round(avg_ph, 1),
        "critical_alerts": critical
    }

@app.get("/api/sensor-history")
def get_sensor_history(limit: int = 30, db: Session = Depends(get_db)):
    # Returns last x readings for chart
    return db.query(SensorReading).order_by(SensorReading.timestamp.desc()).limit(limit).all()

@app.get("/api/pests/{filename}")
def get_pest_image(filename: str):
    return FileResponse(os.path.join(UPLOAD_DIR, filename))


@app.get("/api/pest-history")
def get_history(db: Session = Depends(get_db)):
    return db.query(PestHistory).order_by(PestHistory.created_at.desc()).all()



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run AgroShield Backend")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    args = parser.parse_args()
    
    uvicorn.run(app, host="0.0.0.0", port=args.port)