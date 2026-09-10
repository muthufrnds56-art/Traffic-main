# Real-Time Traffic Management System

A comprehensive IoT and Machine Learning-based solution for urban traffic management and mobility optimization.

## 🚦 Features

- **Real-time Traffic Monitoring**: IoT sensors collect live traffic data
- **ML-Powered Predictions**: Traffic flow prediction and congestion detection
- **Smart Route Optimization**: AI-driven route recommendations
- **Live Dashboard**: Real-time visualization of traffic conditions
- **Google Maps Overlay**: Visualize sensor congestion directly on Google Maps
- **IoT Integration**: MQTT-based sensor communication
- **Stream Processing**: Apache Kafka for real-time data handling

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   IoT Sensors   │───▶│  Data Pipeline  │───▶│  ML Models      │
│                 │    │                 │    │                 │
│ • Traffic Cam   │    │ • MQTT Broker   │    │ • Prediction    │
│ • Flow Sensors  │    │ • Kafka Stream  │    │ • Optimization  │
│ • Environment   │    │ • InfluxDB      │    │ • Anomaly Det.  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Web Dashboard  │
                       │                 │
                       │ • Real-time     │
                       │ • Analytics     │
                       │ • Management    │
                       └─────────────────┘
```

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start IoT Sensor Simulation**
   ```bash
   python iot_sensors/traffic_simulator.py
   ```

3. **Launch Data Pipeline**
   ```bash
   python data_pipeline/kafka_consumer.py
   ```

4. **Start ML Prediction Service**
   ```bash
   python ml_services/traffic_predictor.py
   ```

5. **Run Web Dashboard**
   ```bash
   streamlit run dashboard/main.py
   ```

## 📊 Using Kaggle Dataset (Bangalore Traffic Data)

Instead of simulated sensors, you can use real traffic data from Kaggle:

1. **Switch to Dataset Mode**
   
   Edit `config/settings.py` and change:
   ```python
   DATA_SOURCE: str = "kaggle_dataset"  # Change from "simulator"
   ```

2. **Download Bangalore Traffic Dataset**
   
   - Visit: https://www.kaggle.com/datasets/ravirajsinh45/real-time-traffic-data-bangalore
   - Download and extract the CSV file
   - Place it in `datasets/bangalore_traffic.csv`
   
   **OR** use the included sample dataset (already generated):
   ```bash
   # Sample dataset is already at: datasets/bangalore_traffic.csv
   # Contains 5,376 records for 8 Bangalore locations over 7 days
   ```

3. **Start the System**
   ```bash
   python start_system.py
   ```
   
   The system will automatically use the Kaggle dataset instead of the simulator!

### Dataset Configuration Options

In `config/settings.py`:
```python
DATA_SOURCE: str = "kaggle_dataset"  # or "simulator"
DATASET_PATH: str = "datasets/bangalore_traffic.csv"
DATASET_REPLAY_SPEED: float = 1.0  # Speed up/slow down replay
DATASET_LOOP: bool = True  # Loop when dataset ends
```


### 🎥 New: Video Traffic Analysis

You can now analyze traffic videos to estimate density and movement:

```bash
# Start simplified API (no external DBs needed)
python -m uvicorn api.simple_main:app --host 0.0.0.0 --port 8000

# In the dashboard (Video Analysis page):
# - Upload a video file or provide a local path
# - Run analysis to view moving-object counts and density level
```

API endpoints:

- `POST /api/video/analyze` with JSON `{ "video_path": "/path/to/video.mp4" }`
- `POST /api/video/upload` with multipart file field `file`

## 📁 Project Structure

```
traffic/
├── iot_sensors/          # IoT sensor simulation and data collection
├── data_pipeline/        # Kafka streams and data processing
├── ml_services/          # Machine learning models and predictions
├── database/             # Database schemas and connections
├── api/                  # FastAPI backend services
├── dashboard/            # Streamlit web interface
├── config/               # Configuration files
└── tests/                # Unit tests
```

## 🔧 Configuration

Create a `.env` file with:
```env
KAFKA_BROKER=localhost:9092
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_token
REDIS_URL=redis://localhost:6379
MQTT_BROKER=localhost:1883
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

## 📊 Data Flow

1. **IoT Sensors** → MQTT → **Data Pipeline**
2. **Data Pipeline** → Kafka → **ML Services**
3. **ML Services** → InfluxDB → **Web Dashboard**
4. **Web Dashboard** → API → **Traffic Management Actions**

## 🤖 Machine Learning Models

- **Traffic Flow Prediction**: LSTM-based time series forecasting
- **Congestion Detection**: Anomaly detection using Isolation Forest
- **Route Optimization**: Reinforcement learning for dynamic routing
- **Demand Forecasting**: Seasonal decomposition for traffic patterns

## 🌐 API Endpoints

- `GET /api/traffic/current` - Current traffic conditions
- `GET /api/traffic/predictions` - Traffic predictions
- `POST /api/routes/optimize` - Route optimization
- `GET /api/analytics/summary` - Traffic analytics summary

## 📈 Monitoring & Analytics

- Real-time traffic flow visualization
- Historical trend analysis
- Performance metrics dashboard
- Alert system for traffic incidents

## 🔒 Security Features

- JWT authentication for API access
- Encrypted sensor communication
- Role-based access control
- Audit logging for all operations

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test suite
python -m pytest tests/test_ml_models.py
```

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 Support

For questions and support, please open an issue in the repository.

"# traffic" 
