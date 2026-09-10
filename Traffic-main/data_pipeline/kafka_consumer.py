import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

from kafka import KafkaConsumer, KafkaProducer
from aiomqtt import Client
import sys
import os

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from config.settings import settings
from database.connection import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrafficDataPipeline:
    def __init__(self):
        self.mqtt_client = None
        self.kafka_producer = None
        self.kafka_consumer = None
        self.running = False
        
    async def connect_mqtt(self):
        """Connect to MQTT broker to receive sensor data"""
        try:
            self.mqtt_client = Client(
                hostname=settings.MQTT_BROKER,
                port=settings.MQTT_PORT,
                keepalive=settings.MQTT_KEEPALIVE
            )
            await self.mqtt_client.connect()
            logger.info("Connected to MQTT broker")
        except Exception as e:
            logger.warning(f"Failed to connect to MQTT broker: {e}. MQTT processing disabled.")
            self.mqtt_client = None
    
    def connect_kafka(self):
        """Connect to Kafka broker"""
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=[settings.KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            
            self.kafka_consumer = KafkaConsumer(
                settings.KAFKA_TOPIC_TRAFFIC,
                bootstrap_servers=[settings.KAFKA_BROKER],
                group_id=settings.KAFKA_GROUP_ID,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            
            logger.info("Connected to Kafka broker")
        except Exception as e:
            logger.warning(f"Failed to connect to Kafka broker: {e}. Data pipeline will be disabled.")
            self.kafka_producer = None
            self.kafka_consumer = None
    
    async def subscribe_to_sensors(self):
        """Subscribe to all traffic sensor topics"""
        try:
            # Subscribe to traffic data topics
            await self.mqtt_client.subscribe(f"{settings.MQTT_TOPIC_TRAFFIC}/#")
            await self.mqtt_client.subscribe(settings.MQTT_TOPIC_ENVIRONMENT)
            logger.info("Subscribed to sensor topics")
        except Exception as e:
            logger.error(f"Failed to subscribe to sensor topics: {e}")
            raise
    
    async def process_mqtt_messages(self):
        """Process incoming MQTT messages and forward to Kafka"""
        try:
            async with self.mqtt_client.messages() as messages:
                async for message in messages:
                    try:
                        # Parse message payload
                        payload = json.loads(message.payload.decode())
                        topic = message.topic.value
                        
                        # Add metadata
                        payload['mqtt_topic'] = topic
                        payload['received_at'] = datetime.now().isoformat()
                        
                        # Forward to Kafka
                        if 'traffic' in topic:
                            await self.forward_to_kafka(settings.KAFKA_TOPIC_TRAFFIC, payload)
                        elif 'environment' in topic:
                            await self.forward_to_kafka('environmental_data', payload)
                            
                        logger.debug(f"Processed MQTT message from {topic}")
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in MQTT message: {e}")
                    except Exception as e:
                        logger.error(f"Error processing MQTT message: {e}")
                        
        except Exception as e:
            logger.error(f"Error in MQTT message processing: {e}")
    
    async def forward_to_kafka(self, topic: str, data: Dict[str, Any]):
        """Forward data to Kafka topic"""
        try:
            # Send to Kafka
            future = self.kafka_producer.send(topic, value=data)
            await asyncio.get_event_loop().run_in_executor(None, future.get)
            
            # Store in database
            if topic == settings.KAFKA_TOPIC_TRAFFIC:
                await db_manager.write_traffic_data(data)
                await db_manager.cache_traffic_data(f"traffic:{data.get('sensor_id')}", data)
            
            logger.debug(f"Forwarded data to Kafka topic: {topic}")
            
        except Exception as e:
            logger.error(f"Error forwarding to Kafka: {e}")
    
    async def process_kafka_messages(self):
        """Process messages from Kafka for real-time analytics"""
        try:
            for message in self.kafka_consumer:
                try:
                    data = message.value
                    topic = message.topic
                    
                    # Process traffic data for real-time analytics
                    if topic == settings.KAFKA_TOPIC_TRAFFIC:
                        await self.analyze_traffic_data(data)
                    elif topic == 'environmental_data':
                        await self.analyze_environmental_data(data)
                        
                except Exception as e:
                    logger.error(f"Error processing Kafka message: {e}")
                    
        except Exception as e:
            logger.error(f"Error in Kafka message processing: {e}")
    
    async def analyze_traffic_data(self, data: Dict[str, Any]):
        """Analyze traffic data for real-time insights"""
        try:
            sensor_id = data.get('sensor_id')
            congestion_level = data.get('congestion_level', 0)
            flow_rate = data.get('flow_rate', 0)
            
            # Check for congestion alerts
            if congestion_level >= 4:
                alert = {
                    'type': 'congestion_alert',
                    'sensor_id': sensor_id,
                    'location': data.get('location'),
                    'congestion_level': congestion_level,
                    'timestamp': datetime.now().isoformat(),
                    'severity': 'high' if congestion_level == 5 else 'medium'
                }
                
                # Send alert to Kafka
                await self.forward_to_kafka(settings.KAFKA_TOPIC_ALERTS, alert)
                logger.warning(f"Congestion alert: {sensor_id} at level {congestion_level}")
            
            # Check for unusual flow patterns
            if flow_rate > 0:
                avg_flow = await self.get_average_flow_rate(sensor_id)
                if avg_flow > 0 and abs(flow_rate - avg_flow) / avg_flow > 0.5:
                    logger.info(f"Unusual flow pattern detected at {sensor_id}")
                    
        except Exception as e:
            logger.error(f"Error analyzing traffic data: {e}")
    
    async def analyze_environmental_data(self, data: Dict[str, Any]):
        """Analyze environmental data for traffic impact"""
        try:
            visibility = data.get('visibility', 1.0)
            precipitation = data.get('precipitation', 0)
            
            # Check for weather-related traffic impacts
            if visibility < 0.7 or precipitation > 5:
                weather_alert = {
                    'type': 'weather_alert',
                    'visibility': visibility,
                    'precipitation': precipitation,
                    'timestamp': datetime.now().isoformat(),
                    'impact': 'reduced_visibility' if visibility < 0.7 else 'heavy_precipitation'
                }
                
                await self.forward_to_kafka(settings.KAFKA_TOPIC_ALERTS, weather_alert)
                logger.info("Weather alert generated")
                
        except Exception as e:
            logger.error(f"Error analyzing environmental data: {e}")
    
    async def get_average_flow_rate(self, sensor_id: str) -> float:
        """Get average flow rate for a sensor from cache"""
        try:
            cached_data = await db_manager.get_cached_data(f"traffic:{sensor_id}")
            if cached_data:
                return cached_data.get('flow_rate', 0)
            return 0
        except Exception:
            return 0
    
    async def run(self):
        """Run the data pipeline"""
        try:
            # Connect to databases
            await db_manager.connect()
            
            # Connect to MQTT and Kafka
            await self.connect_mqtt()
            self.connect_kafka()
            
            # Subscribe to sensor topics
            if self.mqtt_client:
                await self.subscribe_to_sensors()
            
            self.running = True
            logger.info("Traffic data pipeline started")
            
            # Run both processing tasks concurrently
            if self.mqtt_client and self.kafka_consumer:
                await asyncio.gather(
                    self.process_mqtt_messages(),
                    self.process_kafka_messages()
                )
            else:
                logger.info("Kafka or MQTT not available. Running in idle mode.")
                while self.running:
                    await asyncio.sleep(10)
            
        except KeyboardInterrupt:
            logger.info("Data pipeline stopped by user")
        except Exception as e:
            logger.error(f"Data pipeline error: {e}")
        finally:
            self.running = False
            if self.mqtt_client:
                try:
                    await self.mqtt_client.disconnect()
                except Exception:
                    pass
            if self.kafka_producer:
                self.kafka_producer.close()
            if self.kafka_consumer:
                self.kafka_consumer.close()
            await db_manager.disconnect()

async def main():
    """Main function to run the data pipeline"""
    pipeline = TrafficDataPipeline()
    await pipeline.run()

if __name__ == "__main__":
    asyncio.run(main())
