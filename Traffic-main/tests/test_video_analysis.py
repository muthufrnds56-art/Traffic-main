import sys
import os
import json
import cv2
import numpy as np

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from video_analysis.video_analyzer import VideoAnalyzer

def create_mock_video(filename="mock_traffic.mp4", duration_sec=2, fps=30):
    """Create a simple mock video with moving rectangles"""
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    # Object 1 moving right
    x1, y1 = 50, 200
    # Object 2 moving left
    x2, y2 = 500, 300
    
    for _ in range(duration_sec * fps):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Draw obj 1
        cv2.rectangle(frame, (int(x1), y1), (int(x1)+40, y1+30), (255, 255, 255), -1)
        x1 += 5
        
        # Draw obj 2
        cv2.rectangle(frame, (int(x2), y2), (int(x2)+40, y2+30), (255, 255, 255), -1)
        x2 -= 3
        
        out.write(frame)
        
    out.release()
    return filename

def test_video_analysis():
    # Create a mock video since we might not want to process a large real video
    video_path = create_mock_video()
    print(f"Created mock video: {video_path}")
    
    try:
        analyzer = VideoAnalyzer(min_contour_area=100) # Lower area for mock objects
        result = analyzer.analyze(video_path, max_frames=60)
        
        print("\nAnalysis Results:")
        print(f"Total Unique Vehicles: {result['total_unique_vehicles']}")
        print(f"Avg Moving Objects: {result['avg_moving_objects']}")
        print(f"Avg Speed (px/frame): {result['avg_speed_px_per_frame']}")
        print(f"Flow Rate (veh/min): {result['estimated_flow_rate_per_min']}")
        print(f"Density Level: {result['density_level']}")
        
        # Verify new metrics exist
        assert 'avg_speed_px_per_frame' in result
        assert 'estimated_flow_rate_per_min' in result
        assert result['avg_speed_px_per_frame'] > 0
        
        print("\nTest Passed!")
        
    finally:
        # Cleanup
        if os.path.exists(video_path):
            os.remove(video_path)
            pass

if __name__ == "__main__":
    test_video_analysis()
