#!/usr/bin/env python3
"""
Traffic Management System Startup Script
This script helps you start all components of the traffic management system.
"""

import subprocess
import sys
import time
import os
import signal
import threading
from typing import List, Dict

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


class SystemManager:
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = False
        
    def _build_env(self) -> Dict[str, str]:
        """Ensure child processes can import project modules."""
        env = os.environ.copy()
        python_path = env.get("PYTHONPATH")
        if python_path:
            env["PYTHONPATH"] = os.pathsep.join([PROJECT_ROOT, python_path])
        else:
            env["PYTHONPATH"] = PROJECT_ROOT
        return env
        
    def start_component(self, name: str, command: List[str], cwd: str = None) -> bool:
        """Start a system component"""
        try:
            print(f"Starting {name}...")
            
            # Create the process
            process = subprocess.Popen(
                command,
                cwd=cwd or PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=self._build_env()
            )
            
            self.processes[name] = process
            
            # Wait a moment to check if it started successfully
            time.sleep(2)
            
            if process.poll() is None:
                print(f"{name} started successfully (PID: {process.pid})")
                return True
            else:
                print(f"{name} failed to start")
                return False
                
        except Exception as e:
            print(f"Error starting {name}: {e}")
            return False
    
    def stop_component(self, name: str):
        """Stop a system component"""
        if name in self.processes:
            process = self.processes[name]
            try:
                print(f"Stopping {name}...")
                process.terminate()
                process.wait(timeout=10)
                print(f"{name} stopped")
            except subprocess.TimeoutExpired:
                print(f"{name} didn't stop gracefully, forcing...")
                process.kill()
            except Exception as e:
                print(f"Error stopping {name}: {e}")
            finally:
                del self.processes[name]
    
    def start_all(self):
        """Start all system components"""
        print("Starting Traffic Management System...")
        print("=" * 50)
        
        # Import settings to check data source
        from config.settings import settings
        
        # Component configurations
        disable_sensors = os.environ.get("DISABLE_SENSORS", "0") == "1"
        components = []
        if not disable_sensors:
            # Choose data source based on configuration
            if settings.DATA_SOURCE == "kaggle_dataset":
                print(f"Using Kaggle dataset: {settings.DATASET_PATH}")
                components.extend([
                    {
                        "name": "Kaggle Data Loader",
                        "command": [sys.executable, "iot_sensors/kaggle_data_loader.py"],
                        "cwd": None
                    },
                    {
                        "name": "Data Pipeline",
                        "command": [sys.executable, "data_pipeline/kafka_consumer.py"],
                        "cwd": None
                    },
                ])
            else:
                print("Using simulated IoT sensors")
                components.extend([
                    {
                        "name": "IoT Traffic Simulator",
                        "command": [sys.executable, "iot_sensors/traffic_simulator.py"],
                        "cwd": None
                    },
                    {
                        "name": "Data Pipeline",
                        "command": [sys.executable, "data_pipeline/kafka_consumer.py"],
                        "cwd": None
                    },
                ])
        components.extend([

            {
                "name": "ML Prediction Service",
                "command": [sys.executable, "ml_services/traffic_predictor.py"],
                "cwd": None
            },
            {
                "name": "API Server",
                "command": [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"],
                "cwd": None
            },
            {
                "name": "Dashboard",
                "command": [sys.executable, "-m", "streamlit", "run", "dashboard/main.py", "--server.port", "8501"],
                "cwd": None
            }
        ])
        
        # Start components with delays to ensure proper initialization
        for i, component in enumerate(components):
            if not self.start_component(component["name"], component["command"], component["cwd"]):
                print(f"Failed to start {component['name']}. Continuing with remaining components...")
                continue
            
            # Wait between component starts
            if i < len(components) - 1:
                print(f"Waiting for {component['name']} to initialize...")
                time.sleep(5)
        
        self.running = True
        print("\nAll components started successfully!")
        print("=" * 50)
        print("Dashboard: http://localhost:8501")
        print("API: http://localhost:8000")
        print("API Docs: http://localhost:8000/docs")
        print("=" * 50)
        print("Press Ctrl+C to stop all components")
        
        return True
    
    def stop_all(self):
        """Stop all system components"""
        print("\nStopping all components...")
        
        for name in list(self.processes.keys()):
            self.stop_component(name)
        
        self.running = False
        print("All components stopped")
    
    def monitor(self):
        """Monitor running components"""
        while self.running:
            try:
                # Check if any processes have died
                dead_processes = []
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        dead_processes.append(name)
                
                # Report dead processes
                for name in dead_processes:
                    print(f"{name} has stopped unexpectedly")
                    del self.processes[name]
                
                # Wait before next check
                time.sleep(5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Monitoring error: {e}")
                break
    
    def run(self):
        """Run the system manager"""
        try:
            if self.start_all():
                self.monitor()
        except KeyboardInterrupt:
            print("\nReceived interrupt signal...")
        finally:
            self.stop_all()

def check_dependencies():
    """Check if required dependencies are available"""
    print("Checking dependencies...")
    
    required_modules = [
        'fastapi', 'uvicorn', 'streamlit', 'plotly', 'pandas',
        'numpy', 'sklearn', 'kafka', 'redis', 'influxdb_client'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"Missing required modules: {', '.join(missing_modules)}")
        print("Please install them using: pip install -r requirements.txt")
        return False
    
    print("All dependencies are available")
    return True

def main():
    """Main function"""
    print("Traffic Management System")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create and run system manager
    manager = SystemManager()
    
    # Set up signal handlers
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}")
        manager.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        manager.run()
    except Exception as e:
        print(f"System error: {e}")
        manager.stop_all()
        sys.exit(1)

if __name__ == "__main__":
    main()
