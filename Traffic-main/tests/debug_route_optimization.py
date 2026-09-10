import asyncio
import sys
import os
import json

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from ml_services.traffic_predictor import TrafficPredictor

async def debug_route_optimization():
    predictor = TrafficPredictor()
    await predictor.initialize()
    
    current_traffic = {
        'traffic_data': [
            {'location': 'MG Road', 'congestion_level': 5},
            {'location': 'Indiranagar 100ft Road', 'congestion_level': 3},
        ]
    }
    
    start = "MG Road"
    end = "Indiranagar 100ft Road"
    
    preferences = ["fastest", "shortest", "least_congested"]
    results = {}
    
    for pref in preferences:
        result = await predictor.optimize_route(start, end, current_traffic, preferred_route_type=pref)
        all_routes = [result['recommended_route']] + result['alternative_routes']
        
        results[pref] = [
            {
                'id': r['route_id'],
                'dist': r['distance'],
                'time': r['estimated_time'],
                'cong': r['congestion_level'],
                'score': r['score']
            }
            for r in all_routes
        ]
    
    with open('debug_results.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(debug_route_optimization())
