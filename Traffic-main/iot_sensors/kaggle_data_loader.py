import asyncio
import json
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import sys
import os

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from config.settings import settings
from aiomqtt import Client, MqttError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KaggleDataLoader:
    """Load and stream traffic data from Kaggle dataset"""
    
    def __init__(self, dataset_path: str, replay_speed: float = 1.0, loop: bool = True):
        """
        Initialize the Kaggle data loader
        
        Args:
            dataset_path: Path to the CSV dataset file
            replay_speed: Speed multiplier for replaying data (1.0 = real-time)
            loop: Whether to loop the dataset when it ends
        """
        self.dataset_path = Path(dataset_path)
        self.replay_speed = replay_speed
        self.loop = loop
        self.client = None
        self.data = None
        self.current_index = 0
        
    def load_dataset(self) -> pd.DataFrame:
        """Load the dataset from CSV"""
        try:
            logger.info(f"Loading dataset from {self.dataset_path}")
            
            if not self.dataset_path.exists():
                raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")
            
            # Load CSV
            df = pd.read_csv(self.dataset_path)
            logger.info(f"Loaded {len(df)} records from dataset")
            logger.info(f"Columns: {list(df.columns)}")
            
            # Normalize column names (handle different naming conventions)
            df.columns = df.columns.str.lower().str.strip()
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            raise
    
    def map_to_traffic_format(self, row: pd.Series) -> Dict:
        """
        Map dataset row to the expected traffic data format
        
        Handles different column naming conventions
        """
        # Try to extract timestamp
        timestamp = None
        for col in ['timestamp', 'date_time', 'datetime', 'date', 'time']:
            if col in row.index:
                timestamp = row[col]
                break
        
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        elif isinstance(timestamp, str):
            # Keep as is if already a string
            pass
        else:
            # Convert to ISO format
            timestamp = pd.to_datetime(timestamp).isoformat()
        
        # Extract location/sensor ID
        location = None
        sensor_id = None
        for col in ['location', 'area', 'road_name', 'intersection', 'sensor_id', 'road']:
            if col in row.index:
                location = str(row[col])
                # Generate sensor ID from location
                sensor_id = f"BLR_{hash(location) % 1000:03d}"
                break
        
        if location is None:
            location = "Unknown Location"
            sensor_id = "BLR_000"
        
        # Extract traffic volume/vehicle count
        vehicle_count = 0
        for col in ['traffic_volume', 'vehicle_count', 'volume', 'count', 'vehicles']:
            if col in row.index:
                vehicle_count = int(row[col]) if pd.notna(row[col]) else 0
                break
        
        # Extract average speed
        average_speed = 0
        for col in ['average_speed', 'avg_speed', 'speed', 'speed_kmph']:
            if col in row.index:
                average_speed = int(row[col]) if pd.notna(row[col]) else 0
                break
        
        # Extract congestion level
        congestion_level = 1
        for col in ['congestion_level', 'congestion', 'traffic_level', 'density']:
            if col in row.index:
                val = row[col]
                if pd.notna(val):
                    # Handle different formats
                    if isinstance(val, str):
                        # Map text to numbers
                        congestion_map = {
                            'low': 1, 'free-flow': 1, 'light': 1,
                            'moderate': 2, 'medium': 2,
                            'high': 3, 'heavy': 4,
                            'gridlock': 5, 'severe': 5
                        }
                        congestion_level = congestion_map.get(val.lower(), 1)
                    else:
                        congestion_level = int(val)
                        # Normalize to 1-5 scale
                        if congestion_level > 5:
                            congestion_level = min(5, max(1, congestion_level // 2))
                break
        
        # Calculate flow rate (vehicles per hour)
        flow_rate = vehicle_count * 4  # Assuming 15-minute intervals
        
        # Determine road type based on location name
        road_type = "arterial"
        location_lower = location.lower()
        if any(word in location_lower for word in ['highway', 'expressway', 'nh', 'sh']):
            road_type = "highway"
        elif any(word in location_lower for word in ['main', 'road', 'mg road', 'brigade']):
            road_type = "arterial"
        elif any(word in location_lower for word in ['street', 'lane', 'cross']):
            road_type = "local"
        else:
            road_type = "collector"
        
        return {
            "sensor_id": sensor_id,
            "location": location,
            "road_type": road_type,
            "timestamp": timestamp,
            "vehicle_count": vehicle_count,
            "flow_rate": flow_rate,
            "average_speed": average_speed,
            "congestion_level": congestion_level,
            "weather_factor": 1.0,  # Default
            "time_factor": 1.0,  # Default
            "data_source": "kaggle_dataset"
        }
    
    async def publish_traffic_data(self):
        """Publish traffic data from dataset"""
        try:
            while True:
                # Get current row
                if self.current_index >= len(self.data):
                    if self.loop:
                        logger.info("Dataset ended, looping back to start")
                        self.current_index = 0
                    else:
                        logger.info("Dataset ended, stopping")
                        break
                
                row = self.data.iloc[self.current_index]
                self.current_index += 1
                
                # Map to traffic format
                traffic_data = self.map_to_traffic_format(row)
                
                # Publish to MQTT
                topic = f"{settings.MQTT_TOPIC_TRAFFIC}/{traffic_data['sensor_id']}"
                payload = json.dumps(traffic_data)
                
                await self.client.publish(topic, payload)
                logger.debug(f"Published data from {traffic_data['location']}: "
                           f"Congestion {traffic_data['congestion_level']}/5, "
                           f"Speed {traffic_data['average_speed']} km/h")
                
                # Wait before next update (adjusted by replay speed)
                await asyncio.sleep(settings.UPDATE_INTERVAL / self.replay_speed)
                
        except Exception as e:
            logger.error(f"Error publishing traffic data: {e}")
    
    async def publish_environmental_data(self):
        """Publish environmental sensor data (simulated)"""
        try:
            import random
            while True:
                env_data = {
                    "timestamp": datetime.now().isoformat(),
                    "temperature": random.uniform(20, 32),  # Bangalore typical temps
                    "humidity": random.uniform(40, 80),
                    "visibility": random.uniform(0.7, 1.0),
                    "wind_speed": random.uniform(0, 15),
                    "precipitation": random.uniform(0, 5)
                }
                
                payload = json.dumps(env_data)
                await self.client.publish(settings.MQTT_TOPIC_ENVIRONMENT, payload)
                
                await asyncio.sleep(60)  # Update every minute
                
        except Exception as e:
            logger.error(f"Error publishing environmental data: {e}")
    
    async def run(self):
        """Run the data loader"""
        try:
            # Load dataset
            self.data = self.load_dataset()
            
            # Connect to MQTT
            try:
                async with Client(
                    hostname=settings.MQTT_BROKER,
                    port=settings.MQTT_PORT,
                    keepalive=settings.MQTT_KEEPALIVE
                ) as client:
                    self.client = client
                    logger.info(f"Connected to MQTT broker at {settings.MQTT_BROKER}:{settings.MQTT_PORT}")
                    logger.info(f"Kaggle data loader started (replay speed: {self.replay_speed}x)")
                    
                    # Run both publishing tasks concurrently
                    await asyncio.gather(
                        self.publish_traffic_data(),
                        self.publish_environmental_data()
                    )
            except (OSError, MqttError) as e:
                logger.warning(f"Failed to connect to MQTT broker: {e}. Running in simulation mode.")
                self.client = DummyClient()
                logger.info("Kaggle data loader started (Simulation Mode)")
                await asyncio.gather(
                    self.publish_traffic_data(),
                    self.publish_environmental_data()
                )
                
        except KeyboardInterrupt:
            logger.info("Data loader stopped by user")
        except Exception as e:
            logger.error(f"Data loader error: {e}")


class DummyClient:
    """Dummy MQTT client for simulation mode"""
    async def publish(self, topic, payload):
        logger.info(f"[SIMULATION] Published to {topic}: {payload[:100]}...")


async def main():
    """Main function to run the data loader"""
    # Get dataset path from settings or use default
    dataset_path = getattr(settings, 'DATASET_PATH', 'datasets/bangalore_traffic.csv')
    replay_speed = getattr(settings, 'DATASET_REPLAY_SPEED', 1.0)
    loop = getattr(settings, 'DATASET_LOOP', True)
    
    loader = KaggleDataLoader(
        dataset_path=dataset_path,
        replay_speed=replay_speed,
        loop=loop
    )
    await loader.run()


if __name__ == "__main__":
    asyncio.run(main())
