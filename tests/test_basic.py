"""
Basic tests for the Traffic Management System
"""

import unittest
import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from database.connection import DatabaseManager
from ml_services.traffic_predictor import TrafficPredictor

class TestTrafficManagementSystem(unittest.TestCase):
    """Test cases for the Traffic Management System"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db_manager = DatabaseManager()
        self.ml_predictor = TrafficPredictor()
    
    def test_settings_loaded(self):
        """Test that settings are properly loaded"""
        self.assertIsNotNone(settings.APP_NAME)
        self.assertEqual(settings.APP_NAME, "Traffic Management System")
        self.assertIsNotNone(settings.KAFKA_BROKER)
        self.assertIsNotNone(settings.MQTT_BROKER)
    
    def test_database_manager_creation(self):
        """Test database manager creation"""
        self.assertIsNotNone(self.db_manager)
        self.assertIsNone(self.db_manager.influx_client)
        self.assertIsNone(self.db_manager.redis_client)
    
    def test_ml_predictor_creation(self):
        """Test ML predictor creation"""
        self.assertIsNotNone(self.ml_predictor)
        self.assertEqual(self.ml_predictor.prediction_horizon, 60)
        self.assertIsNotNone(self.ml_predictor.model_path)
    
    def test_congestion_probability_calculation(self):
        """Test congestion probability calculation"""
        test_data = {
            'vehicle_count': 50,
            'flow_rate': 1000,
            'average_speed': 30,
            'congestion_level': 3
        }
        
        probability = self.ml_predictor._calculate_congestion_probability(test_data)
        self.assertIsInstance(probability, float)
        self.assertGreaterEqual(probability, 0.0)
        self.assertLessEqual(probability, 1.0)
    
    def test_congestion_severity_classification(self):
        """Test congestion severity classification"""
        test_cases = [
            (0.2, "low"),
            (0.5, "medium"),
            (0.7, "high"),
            (0.9, "critical")
        ]
        
        for probability, expected_severity in test_cases:
            severity = self.ml_predictor._classify_congestion_severity(probability)
            self.assertEqual(severity, expected_severity)
    
    def test_route_score_calculation(self):
        """Test route score calculation"""
        test_route = {
            'distance': 5.0,
            'estimated_time': 10,
            'congestion_level': 2
        }
        
        score = self.ml_predictor._calculate_route_score(test_route, {})
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)

class TestAsyncComponents(unittest.TestCase):
    """Test cases for async components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.loop.close()
    
    def test_database_connection(self):
        """Test database connection (mock)"""
        async def test_connection():
            db_manager = DatabaseManager()
            # This would fail in test environment without actual databases
            # but we can test the structure
            self.assertIsNotNone(db_manager)
            self.assertIsNone(db_manager.influx_client)
        
        self.loop.run_until_complete(test_connection())
    
    def test_ml_predictor_initialization(self):
        """Test ML predictor initialization (mock)"""
        async def test_init():
            predictor = TrafficPredictor()
            # Test that it can be created
            self.assertIsNotNone(predictor)
            self.assertEqual(predictor.prediction_horizon, 60)
        
        self.loop.run_until_complete(test_init())

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)




















