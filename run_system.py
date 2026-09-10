#!/usr/bin/env python3
"""
Simple Traffic Management System Launcher
This script sets up the Python path and runs the system components.
"""

import sys
import os
import subprocess
import time

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def run_component(name, script_path, delay=2):
    """Run a system component"""
    print(f"Starting {name}...")
    try:
        # Run the component
        process = subprocess.Popen([sys.executable, script_path], 
                                 cwd=project_root,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        
        # Wait a moment to check if it started successfully
        time.sleep(delay)
        
        if process.poll() is None:
            print(f"{name} started successfully (PID: {process.pid})")
            return process
        else:
            print(f"{name} failed to start")
            return None
            
    except Exception as e:
        print(f"Error starting {name}: {e}")
        return None

def main():
    """Main function"""
    print("Traffic Management System - Simple Launcher")
    print("=" * 50)
    
    # Check if we can import the modules
    try:
        from config.settings import settings
        print("Configuration loaded successfully")
    except ImportError as e:
        print(f"Failed to load configuration: {e}")
        return
    
    try:
        from iot_sensors.traffic_simulator import TrafficSimulator
        print("IoT simulator module loaded")
    except ImportError as e:
        print(f"Failed to load IoT simulator: {e}")
        return
    
    try:
        from api.main import app
        print("API module loaded")
    except ImportError as e:
        print(f"Failed to load API: {e}")
        return
    
    try:
        from dashboard.main import main as dashboard_main
        print("Dashboard module loaded")
    except ImportError as e:
        print(f"Failed to load dashboard: {e}")
        return
    
    print("\nAll modules loaded successfully!")
    print("=" * 50)
    print("Dashboard: http://localhost:8501")
    print("API: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("=" * 50)
    
    # Start the API server
    print("\nStarting API server...")
    api_process = run_component("API Server", "api/main.py", delay=3)
    
    if api_process:
        print("API server started successfully!")
        print("API is running at http://localhost:8000")
        print("API documentation at http://localhost:8000/docs")
        
        # Start the dashboard
        print("\nStarting Dashboard...")
        dashboard_process = run_component("Dashboard", "dashboard/main.py", delay=3)
        
        if dashboard_process:
            print("Dashboard started successfully!")
            print("Dashboard is running at http://localhost:8501")
            
            print("\nSystem is running!")
            print("Press Ctrl+C to stop all components...")
            
            try:
                # Keep the system running
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping system...")
                if api_process:
                    api_process.terminate()
                if dashboard_process:
                    dashboard_process.terminate()
                print("System stopped")
        else:
            print("Failed to start dashboard")
            if api_process:
                api_process.terminate()
    else:
        print("Failed to start API server")

if __name__ == "__main__":
    main()




















