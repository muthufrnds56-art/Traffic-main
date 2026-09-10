import asyncio
import sys
import os
import pytest

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from ml_services.traffic_predictor import TrafficPredictor

async def test_route_optimization():
    predictor = TrafficPredictor()
    await predictor.initialize()
    
    # Mock traffic data
    current_traffic = {
        'traffic_data': [
            {'location': 'MG Road', 'congestion_level': 5},
            {'location': 'Hosur Road', 'congestion_level': 1},
            {'location': 'Indiranagar 100ft Road', 'congestion_level': 3}
        ]
    }
    
    print("\n--- Testing Fastest Route ---")
    result_fastest = await predictor.optimize_route(
        "MG Road", "Indiranagar 100ft Road", current_traffic, preferred_route_type="fastest"
    )
    print(f"Recommended Route (Fastest): {result_fastest['recommended_route']['route_id']}")
    print(f"Score: {result_fastest['recommended_route']['score']}")
    print(f"Path: {result_fastest['recommended_route']['path']}")
    
    print("\n--- Testing Shortest Route ---")
    result_shortest = await predictor.optimize_route(
        "MG Road", "Indiranagar 100ft Road", current_traffic, preferred_route_type="shortest"
    )
    print(f"Recommended Route (Shortest): {result_shortest['recommended_route']['route_id']}")
    print(f"Score: {result_shortest['recommended_route']['score']}")
    
    print("\n--- Testing Least Congested Route ---")
    result_least_congested = await predictor.optimize_route(
        "MG Road", "Indiranagar 100ft Road", current_traffic, preferred_route_type="least_congested"
    )
    print(f"Recommended Route (Least Congested): {result_least_congested['recommended_route']['route_id']}")
    print(f"Score: {result_least_congested['recommended_route']['score']}")
    
    # Verify scores are not all 0.0
    assert result_fastest['recommended_route']['score'] > 0.0
    assert result_shortest['recommended_route']['score'] > 0.0
    assert result_least_congested['recommended_route']['score'] > 0.0
    
    print("\nTest Passed!")

if __name__ == "__main__":
    asyncio.run(test_route_optimization())
