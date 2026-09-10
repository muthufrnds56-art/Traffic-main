import cv2
import os
import numpy as np
from typing import Dict, Any, List
from .tracker import CentroidTracker

class VideoAnalyzer:
    def __init__(self, min_contour_area: int = 200, history: int = 500, var_threshold: float = 25.0):
        self.min_contour_area = min_contour_area
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=history, varThreshold=var_threshold, detectShadows=True)
        self.tracker = CentroidTracker(max_disappeared=40)
        self.object_paths = {}
        self.object_speeds = {}
        self.object_directions = {}

    def analyze(self, video_path: str, frame_skip: int = 2, max_frames: int = 300) -> Dict[str, Any]:
        if not os.path.exists(video_path):
            return {"error": f"Video not found: {video_path}"}

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"error": f"Unable to open video: {video_path}"}

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

        # Output video setup
        output_dir = os.path.join(os.path.dirname(video_path), "processed")
        os.makedirs(output_dir, exist_ok=True)
        output_filename = f"processed_{os.path.basename(video_path)}"
        output_path = os.path.join(output_dir, output_filename)
        
        # Use mp4v codec for compatibility
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_index = 0
        processed = 0
        moving_objects_per_frame: List[int] = []
        unique_objects = set()

        while processed < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            # Process every frame for smoother video, but only update stats on skipped frames if needed
            # Actually, for tracking to work well, we should process every frame or skip very few
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            fg_mask = self.bg_subtractor.apply(gray)
            _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
            fg_mask = cv2.dilate(fg_mask, None, iterations=2)

            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            rects = []
            
            for cnt in contours:
                if cv2.contourArea(cnt) < self.min_contour_area:
                    continue
                (x, y, w, h) = cv2.boundingRect(cnt)
                rects.append((x, y, x + w, y + h))
                
                # Draw bounding box
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Update tracker
            objects = self.tracker.update(rects)
            
            # Calculate speed and direction
            for (object_id, centroid) in objects.items():
                if object_id not in self.object_paths:
                    self.object_paths[object_id] = []
                self.object_paths[object_id].append(centroid)
                
                # Keep only recent history
                if len(self.object_paths[object_id]) > 30:
                    self.object_paths[object_id].pop(0)

                # Calculate speed (pixels per frame)
                if len(self.object_paths[object_id]) >= 2:
                    prev_c = self.object_paths[object_id][-2]
                    curr_c = self.object_paths[object_id][-1]
                    # Euclidean distance
                    speed_px = np.sqrt((curr_c[0] - prev_c[0])**2 + (curr_c[1] - prev_c[1])**2)
                    self.object_speeds[object_id] = speed_px
                    
                    # Determine direction
                    dx = curr_c[0] - prev_c[0]
                    dy = curr_c[1] - prev_c[1]
                    if abs(dx) > abs(dy):
                        direction = "Right" if dx > 0 else "Left"
                    else:
                        direction = "Down" if dy > 0 else "Up"
                    self.object_directions[object_id] = direction

                unique_objects.add(object_id)
                
                # Visualization
                text = f"ID {object_id}"
                if object_id in self.object_speeds:
                    text += f" {int(self.object_speeds[object_id])}px/f"
                
                cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 255, 0), -1)
                
                # Draw trail
                if len(self.object_paths[object_id]) > 1:
                    for i in range(1, len(self.object_paths[object_id])):
                        cv2.line(frame, tuple(self.object_paths[object_id][i-1]), 
                               tuple(self.object_paths[object_id][i]), (0, 255, 255), 1)

            # Write frame to output video
            out.write(frame)

            moving_objects_per_frame.append(len(objects))
            processed += 1
            frame_index += 1

        cap.release()
        out.release()

        analyzed_frames = len(moving_objects_per_frame)
        avg_moving = float(sum(moving_objects_per_frame) / analyzed_frames) if analyzed_frames > 0 else 0.0
        peak_moving = max(moving_objects_per_frame) if analyzed_frames > 0 else 0
        total_unique = len(unique_objects)
        
        # Calculate average speed across all objects
        avg_speed_px = 0
        if self.object_speeds:
            avg_speed_px = sum(self.object_speeds.values()) / len(self.object_speeds)
            
        # Estimate flow rate (vehicles per minute)
        video_duration_sec = analyzed_frames / fps if fps > 0 else 0
        flow_rate_per_min = (total_unique / video_duration_sec) * 60 if video_duration_sec > 0 else 0

        # Improved Density estimate based on average moving objects (occupancy)
        # Adjust thresholds based on resolution (assuming standard 720p/1080p roughly)
        density_level = "low"
        if avg_moving >= 15:
            density_level = "high"
        elif avg_moving >= 5:
            density_level = "medium"

        return {
            "video_path": os.path.abspath(video_path),
            "processed_video_path": os.path.abspath(output_path),
            "fps": float(fps),
            "resolution": {"width": width, "height": height},
            "total_frames": total_frames,
            "analyzed_frames": analyzed_frames,
            "total_unique_vehicles": total_unique,
            "avg_moving_objects": round(avg_moving, 2),
            "peak_moving_objects": int(peak_moving),
            "avg_speed_px_per_frame": round(avg_speed_px, 2),
            "estimated_flow_rate_per_min": round(flow_rate_per_min, 1),
            "density_level": density_level,
            "moving_objects_per_frame": moving_objects_per_frame[:100],
        }

if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Analyze a traffic video")
    parser.add_argument("video_path", help="Path to a local video file")
    args = parser.parse_args()

    analyzer = VideoAnalyzer()
    result = analyzer.analyze(args.video_path)
    print(json.dumps(result, indent=2))



