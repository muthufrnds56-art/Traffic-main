import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List
import logging

from aiomqtt import Client, MqttError
import sys
import os

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrafficSensor:
    def __init__(self, sensor_id: str, location: str, road_type: str):
        self.sensor_id = sensor_id
        self.location = location
        self.road_type = road_type
        self.base_flow_rate = self._get_base_flow_rate(road_type)
        self.peak_hours = [7, 8, 9, 17, 18, 19]  # Rush hours
        
    def _get_base_flow_rate(self, road_type: str) -> int:
        """Get base flow rate based on road type"""
        rates = {
            "highway": 2000,
            "arterial": 1200,
            "collector": 800,
            "local": 400
        }
        return rates.get(road_type, 800)
    
    def _calculate_time_factor(self) -> float:
        """Calculate time-based factor for traffic flow"""
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        
        # Base factor
        factor = 0.3
        
        # Rush hour multiplier
        if hour in self.peak_hours:
            factor = 1.8
        elif hour in [10, 11, 12, 13, 14, 15, 16]:  # Mid-day
            factor = 1.2
        elif hour in [20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6]:  # Night
            factor = 0.4
            
        # Weekend adjustment
        if now.weekday() >= 5:  # Saturday/Sunday
            factor *= 0.7
            
        return factor
    
    def _calculate_weather_factor(self) -> float:
        """Simulate weather impact on traffic"""
        # Simulate weather conditions (sunny, rainy, snowy)
        weather_conditions = ["sunny", "rainy", "snowy"]
        current_weather = random.choice(weather_conditions)
        
        weather_factors = {
            "sunny": 1.0,
            "rainy": 0.8,
            "snowy": 0.6
        }
        
        return weather_factors.get(current_weather, 1.0)
    
    def generate_traffic_data(self) -> Dict:
        """Generate realistic traffic data"""
        time_factor = self._calculate_time_factor()
        weather_factor = self._calculate_weather_factor()
        
        # Calculate flow rate with variations
        flow_rate = int(self.base_flow_rate * time_factor * weather_factor * random.uniform(0.8, 1.2))
        
        # Calculate vehicle count (vehicles per minute)
        vehicle_count = int(flow_rate / 60)
        
        # Calculate average speed based on congestion
        congestion_level = min(5, max(1, int((flow_rate / self.base_flow_rate) * 3)))
        
        speed_factors = {1: 1.0, 2: 0.9, 3: 0.7, 4: 0.5, 5: 0.3}
        base_speed = 60 if self.road_type == "highway" else 40
        average_speed = int(base_speed * speed_factors[congestion_level] * random.uniform(0.9, 1.1))
        
        # Add some randomness to congestion level
        congestion_level = max(1, min(5, congestion_level + random.randint(-1, 1)))
        
        return {
            "sensor_id": self.sensor_id,
            "location": self.location,
            "road_type": self.road_type,
            "timestamp": datetime.now().isoformat(),
            "vehicle_count": vehicle_count,
            "flow_rate": flow_rate,
            "average_speed": average_speed,
            "congestion_level": congestion_level,
            "weather_factor": weather_factor,
            "time_factor": time_factor
        }

class TrafficSimulator:
    def __init__(self):
        self.sensors = self._create_sensors()
        self.client = None
        
    def _create_sensors(self) -> List[TrafficSensor]:
        """Create a network of traffic sensors"""
        sensor_configs = [
            {"sensor_id": "T001", "location": "MG Road", "road_type": "arterial"},
            {"sensor_id": "T002", "location": "Hosur Road", "road_type": "highway"},
            {"sensor_id": "T003", "location": "Indiranagar 100ft Road", "road_type": "collector"},
            {"sensor_id": "T004", "location": "Outer Ring Road", "road_type": "arterial"},
            {"sensor_id": "T005", "location": "Jayanagar 4th Block", "road_type": "local"},
            {"sensor_id": "T006", "location": "Bellary Road", "road_type": "highway"},
            {"sensor_id": "T007", "location": "Koramangala 80ft Road", "road_type": "collector"},
            {"sensor_id": "T008", "location": "Bannerghatta Road", "road_type": "arterial"}
        ]


        
        return [TrafficSensor(**config) for config in sensor_configs]
    
    async def connect_mqtt(self):
        """Compatibility stub (not used)."""
        pass
    
    async def publish_traffic_data(self):
        """Publish traffic data from all sensors"""
        try:
            while True:
                for sensor in self.sensors:
                    # Generate traffic data
                    traffic_data = sensor.generate_traffic_data()
                    
                    # Publish to MQTT
                    topic = f"{settings.MQTT_TOPIC_TRAFFIC}/{sensor.sensor_id}"
                    payload = json.dumps(traffic_data)
                    
                    await self.client.publish(topic, payload)
                    logger.debug(f"Published traffic data from {sensor.sensor_id}: {traffic_data['congestion_level']}/5")
                
                # Wait before next update
                await asyncio.sleep(settings.UPDATE_INTERVAL)
                
        except MqttError as e:
            logger.error(f"MQTT error: {e}")
        except Exception as e:
            logger.error(f"Error publishing traffic data: {e}")
    
    async def publish_environmental_data(self):
        """Publish environmental sensor data"""
        try:
            while True:
                env_data = {
                    "timestamp": datetime.now().isoformat(),
                    "temperature": random.uniform(15, 35),
                    "humidity": random.uniform(30, 80),
                    "visibility": random.uniform(0.5, 1.0),
                    "wind_speed": random.uniform(0, 20),
                    "precipitation": random.uniform(0, 10)
                }
                
                payload = json.dumps(env_data)
                await self.client.publish(settings.MQTT_TOPIC_ENVIRONMENT, payload)
                
                await asyncio.sleep(60)  # Update every minute
                
        except Exception as e:
            logger.error(f"Error publishing environmental data: {e}")
    
    async def run(self):
        """Run the traffic simulator"""
        try:
            try:
                async with Client(
                    hostname=settings.MQTT_BROKER,
                    port=settings.MQTT_PORT,
                    keepalive=settings.MQTT_KEEPALIVE
                ) as client:
                    self.client = client
                    logger.info(f"Connected to MQTT broker at {settings.MQTT_BROKER}:{settings.MQTT_PORT}")
                    logger.info("Traffic simulator started")

                    # Run both publishing tasks concurrently
                    await asyncio.gather(
                        self.publish_traffic_data(),
                        self.publish_environmental_data()
                    )
            except (OSError, MqttError) as e:
                logger.warning(f"Failed to connect to MQTT broker: {e}. Running in simulation mode (console only).")
                self.client = DummyClient()
                logger.info("Traffic simulator started (Simulation Mode)")
                await asyncio.gather(
                    self.publish_traffic_data(),
                    self.publish_environmental_data()
                )

        except KeyboardInterrupt:
            logger.info("Traffic simulator stopped by user")
        except Exception as e:
            logger.error(f"Traffic simulator error: {e}")

class DummyClient:
    """Dummy MQTT client for simulation mode"""
    async def publish(self, topic, payload):
        logger.info(f"[SIMULATION] Published to {topic}: {payload[:50]}...")

async def main():
    """Main function to run the traffic simulator"""
    simulator = TrafficSimulator()
    await simulator.run()

if __name__ == "__main__":
    asyncio.run(main())
