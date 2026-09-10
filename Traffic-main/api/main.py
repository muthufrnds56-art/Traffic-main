from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import logging

import os
import sys

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from config.settings import settings
try:
    from database.connection import db_manager
except Exception:
    db_manager = None  # type: ignore
from ml_services.traffic_predictor import TrafficPredictor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Real-time Traffic Management System API"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Global ML predictor instance
ml_predictor = None

# Pydantic models
class TrafficData(BaseModel):
    sensor_id: str
    location: str
    road_type: str
    vehicle_count: int
    flow_rate: int
    average_speed: int
    congestion_level: int
    timestamp: str

class RouteRequest(BaseModel):
    start_location: str
    end_location: str
    preferred_route_type: Optional[str] = "fastest"

class PredictionRequest(BaseModel):
    sensor_id: str
    horizon_minutes: int = 60

class AlertResponse(BaseModel):
    type: str
    sensor_id: str
    location: str
    severity: str
    message: str
    timestamp: str


def _estimate_congestion_level_from_flow(flow_rate: int) -> int:
    """Simple heuristic to map predicted flow (veh/hr) to congestion level."""
    try:
        flow_value = int(flow_rate)
    except (TypeError, ValueError):
        return 1
    
    if flow_value >= 1500:
        return 5
    if flow_value >= 1200:
        return 4
    if flow_value >= 900:
        return 3
    if flow_value >= 600:
        return 2
    return 1

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global ml_predictor
    try:
        offline_mode = os.environ.get("DISABLE_SENSORS", "0") == "1"
        # Connect to database only when available and not offline
        if not offline_mode and db_manager is not None:
            await db_manager.connect()
        
        # Initialize ML predictor
        ml_predictor = TrafficPredictor()
        await ml_predictor.initialize()
        
        logger.info("API services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize API services: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        if db_manager is not None:
            await db_manager.disconnect()
        logger.info("API services shutdown successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Traffic Management System API",
        "version": settings.APP_VERSION,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        offline_mode = os.environ.get("DISABLE_SENSORS", "0") == "1"
        db_status = "disabled" if offline_mode or db_manager is None else "connected"
        if not offline_mode and db_manager is not None:
            # Check database connection
            redis_client = await db_manager.get_redis_client()
            await redis_client.ping()
        
        return {
            "status": "healthy",
            "database": db_status,
            "ml_service": "running" if ml_predictor else "stopped",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/api/traffic/current")
async def get_current_traffic():
    """Get current traffic conditions from all sensors"""
    try:
        offline_mode = os.environ.get("DISABLE_SENSORS", "0") == "1"
        # Get current traffic data from cache
        sensor_ids = ["T001", "T002", "T003", "T004", "T005", "T006", "T007", "T008"]
        current_traffic = []
        
        if not offline_mode and db_manager is not None:
            for sensor_id in sensor_ids:
                cached_data = await db_manager.get_cached_data(f"traffic:{sensor_id}")
                if cached_data:
                    current_traffic.append(cached_data)
        else:
            # Generate mock data for offline mode
            import random
            from datetime import datetime
            
            sensor_locations = [
                "MG Road", "Hosur Road", "Indiranagar 100ft Road", "Outer Ring Road",
                "Jayanagar 4th Block", "Bellary Road", "Koramangala 80ft Road", "Bannerghatta Road"
            ]


            
            road_types = ["arterial", "highway", "collector", "arterial", "local", "highway", "collector", "arterial"]
            
            for i, sensor_id in enumerate(sensor_ids):
                # Generate realistic traffic data
                base_flow = random.randint(200, 1500)
                time_factor = 1.8 if datetime.now().hour in [7,8,9,17,18,19] else 1.2
                flow_rate = int(base_flow * time_factor * random.uniform(0.8, 1.2))
                
                mock_data = {
                    "sensor_id": sensor_id,
                    "location": sensor_locations[i],
                    "road_type": road_types[i],
                    "vehicle_count": random.randint(10, 120),
                    "flow_rate": flow_rate,
                    "average_speed": random.randint(20, 70),
                    "congestion_level": random.randint(1, 5),
                    "timestamp": datetime.now().isoformat()
                }
                current_traffic.append(mock_data)
        
        return {
            "timestamp": asyncio.get_event_loop().time(),
            "sensors_count": len(current_traffic),
            "traffic_data": current_traffic
        }
    except Exception as e:
        logger.error(f"Error getting current traffic: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve current traffic data")

@app.get("/api/traffic/sensor/{sensor_id}")
async def get_sensor_data(sensor_id: str):
    """Get traffic data for a specific sensor"""
    try:
        cached_data = await db_manager.get_cached_data(f"traffic:{sensor_id}")
        if not cached_data:
            raise HTTPException(status_code=404, detail=f"No data found for sensor {sensor_id}")
        
        return cached_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sensor data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sensor data")

@app.post("/api/traffic/predictions")
async def get_traffic_predictions(request: PredictionRequest):
    """Get traffic flow predictions for a sensor"""
    try:
        if not ml_predictor:
            raise HTTPException(status_code=503, detail="ML service not available")
        
        predictions = await ml_predictor.predict_traffic_flow(
            request.sensor_id, 
            request.horizon_minutes
        )
        
        if "error" in predictions:
            raise HTTPException(status_code=400, detail=predictions["error"])
        
        return predictions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate predictions")

@app.get("/api/traffic/predictions/map")
async def get_prediction_map():
    """Provide per-sensor prediction snapshots for map overlays."""
    try:
        if not ml_predictor:
            raise HTTPException(status_code=503, detail="ML service not available")
        
        sensor_ids = ["T001", "T002", "T003", "T004", "T005", "T006", "T007", "T008"]
        sensor_locations = [
            "MG Road", "Hosur Road", "Indiranagar 100ft Road", "Outer Ring Road",
            "Jayanagar 4th Block", "Bellary Road", "Koramangala 80ft Road", "Bannerghatta Road"
        ]


        
        predictions_payload = []
        for idx, sensor_id in enumerate(sensor_ids):
            try:
                prediction = await ml_predictor.predict_traffic_flow(sensor_id, horizon_minutes=60)
            except Exception as predict_error:
                logger.error(f"Prediction failed for {sensor_id}: {predict_error}")
                continue
            
            if not prediction or prediction.get("error"):
                continue
            
            horizon = prediction.get("predictions") or []
            if not horizon:
                continue
            
            next_point = horizon[0]
            predicted_flow = next_point.get("predicted_flow", prediction.get("current_flow", 0))
            congestion_level = _estimate_congestion_level_from_flow(predicted_flow)
            
            predictions_payload.append({
                "sensor_id": sensor_id,
                "location": sensor_locations[idx] if idx < len(sensor_locations) else sensor_id,
                "prediction_timestamp": next_point.get("timestamp"),
                "predicted_flow": predicted_flow,
                "predicted_congestion_level": congestion_level,
                "traffic_expected": congestion_level >= 4,
                "model_confidence": prediction.get("confidence", 0.0)
            })
        
        return {
            "sensors_count": len(predictions_payload),
            "predictions": predictions_payload
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prediction map: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate prediction map data")

@app.post("/api/routes/optimize")
async def optimize_route(request: RouteRequest):
    """Optimize route based on current traffic conditions"""
    try:
        if not ml_predictor:
            raise HTTPException(status_code=503, detail="ML service not available")
        
        # Get current traffic conditions
        current_traffic = await get_current_traffic()
        
        # Optimize route
        route_optimization = await ml_predictor.optimize_route(
            request.start_location,
            request.end_location,
            current_traffic,
            request.preferred_route_type
        )
        
        if "error" in route_optimization:
            raise HTTPException(status_code=400, detail=route_optimization["error"])
        
        return route_optimization
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing route: {e}")
        raise HTTPException(status_code=500, detail="Failed to optimize route")

@app.get("/api/analytics/summary")
async def get_analytics_summary():
    """Get traffic analytics summary"""
    try:
        # Get current traffic data
        current_traffic = await get_current_traffic()
        
        if not current_traffic.get("traffic_data"):
            return {"error": "No traffic data available"}
        
        traffic_data = current_traffic["traffic_data"]
        
        # Calculate summary statistics
        total_vehicles = sum(data.get("vehicle_count", 0) for data in traffic_data)
        avg_speed = sum(data.get("average_speed", 0) for data in traffic_data) / len(traffic_data)
        avg_congestion = sum(data.get("congestion_level", 0) for data in traffic_data) / len(traffic_data)
        
        # Count congestion levels
        congestion_counts = {}
        for data in traffic_data:
            level = data.get("congestion_level", 0)
            congestion_counts[level] = congestion_counts.get(level, 0) + 1
        
        # Identify problematic areas
        problematic_sensors = [
            data for data in traffic_data 
            if data.get("congestion_level", 0) >= 4
        ]
        
        return {
            "timestamp": asyncio.get_event_loop().time(),
            "summary": {
                "total_sensors": len(traffic_data),
                "total_vehicles": total_vehicles,
                "average_speed": round(avg_speed, 2),
                "average_congestion": round(avg_congestion, 2),
                "congestion_distribution": congestion_counts,
                "problematic_areas": len(problematic_sensors)
            },
            "problematic_sensors": [
                {
                    "sensor_id": data.get("sensor_id"),
                    "location": data.get("location"),
                    "congestion_level": data.get("congestion_level")
                }
                for data in problematic_sensors
            ]
        }
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate analytics summary")

@app.get("/api/alerts/current")
async def get_current_alerts():
    """Get current traffic alerts"""
    try:
        # Get current traffic data
        current_traffic = await get_current_traffic()
        
        if not current_traffic.get("traffic_data"):
            return {"alerts": []}
        
        traffic_data = current_traffic["traffic_data"]
        alerts = []
        
        # Generate alerts based on current conditions
        for data in traffic_data:
            congestion_level = data.get("congestion_level", 0)
            
            if congestion_level >= 4:
                alert = AlertResponse(
                    type="congestion_alert",
                    sensor_id=data.get("sensor_id"),
                    location=data.get("location"),
                    severity="high" if congestion_level == 5 else "medium",
                    message=f"High congestion detected at {data.get('location')}",
                    timestamp=data.get("timestamp")
                )
                alerts.append(alert.dict())
        
        return {
            "timestamp": asyncio.get_event_loop().time(),
            "alerts_count": len(alerts),
            "alerts": alerts
        }
    except Exception as e:
        logger.error(f"Error getting current alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")

@app.get("/api/sensors/list")
async def get_sensors_list():
    """Get list of all available sensors"""
    try:
        sensors = [
            {
                "sensor_id": "T001",
                "location": "MG Road",
                "road_type": "arterial",
                "coordinates": {"lat": 12.9716, "lng": 77.5946}
            },
            {
                "sensor_id": "T002",
                "location": "Hosur Road",
                "road_type": "highway",
                "coordinates": {"lat": 12.9352, "lng": 77.6245}
            },
            {
                "sensor_id": "T003",
                "location": "Indiranagar 100ft Road",
                "road_type": "collector",
                "coordinates": {"lat": 12.9784, "lng": 77.6408}
            },
            {
                "sensor_id": "T004",
                "location": "Outer Ring Road",
                "road_type": "arterial",
                "coordinates": {"lat": 12.9698, "lng": 77.7500}
            },
            {
                "sensor_id": "T005",
                "location": "Jayanagar 4th Block",
                "road_type": "local",
                "coordinates": {"lat": 12.9308, "lng": 77.5838}
            },
            {
                "sensor_id": "T006",
                "location": "Bellary Road",
                "road_type": "highway",
                "coordinates": {"lat": 13.0359, "lng": 77.5970}
            },
            {
                "sensor_id": "T007",
                "location": "Koramangala 80ft Road",
                "road_type": "collector",
                "coordinates": {"lat": 12.9591, "lng": 77.6974}
            },
            {
                "sensor_id": "T008",
                "location": "Bannerghatta Road",
                "road_type": "arterial",
                "coordinates": {"lat": 12.8452, "lng": 77.6602}
            }
        ]


        
        return {
            "sensors_count": len(sensors),
            "sensors": sensors
        }
    except Exception as e:
        logger.error(f"Error getting sensors list: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sensors list")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

