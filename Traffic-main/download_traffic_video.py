#!/usr/bin/env python3
"""
Auto-download and analyze traffic video from Kaggle dataset
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_kaggle_credentials():
    """Setup Kaggle credentials if not already done"""
    home = Path.home()
    kaggle_dir = home / ".kaggle"
    kaggle_file = kaggle_dir / "kaggle.json"
    
    if not kaggle_file.exists():
        print("Kaggle credentials not found!")
        print("Please:")
        print("1. Go to https://www.kaggle.com/account")
        print("2. Click 'Create New API Token'")
        print("3. Download kaggle.json")
        print(f"4. Place it at: {kaggle_file}")
        return False
    
    os.environ["KAGGLE_CONFIG_DIR"] = str(kaggle_dir)
    print("Kaggle credentials found")
    return True

def download_traffic_dataset():
    """Download a traffic video dataset from Kaggle"""
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        
        # Popular traffic video datasets
        datasets = [
            {
                "name": "traffic-density-surveillance-videos",
                "owner": "aayushmishra1512",
                "description": "Traffic surveillance videos with density analysis"
            },
            {
                "name": "traffic-sign-detection",
                "owner": "datasnaek",
                "description": "Traffic sign detection videos"
            },
            {
                "name": "vehicle-detection-traffic-videos",
                "owner": "datasnaek", 
                "description": "Vehicle detection in traffic videos"
            }
        ]
        
        print("Available traffic video datasets:")
        for i, dataset in enumerate(datasets, 1):
            print(f"{i}. {dataset['owner']}/{dataset['name']}")
            print(f"   {dataset['description']}")
        
        # Use first dataset by default
        selected = datasets[0]
        dataset_slug = f"{selected['owner']}/{selected['name']}"
        
        print(f"\nDownloading: {dataset_slug}")
        
        api = KaggleApi()
        api.authenticate()
        
        # Create downloads directory
        download_dir = Path("downloads")
        download_dir.mkdir(exist_ok=True)
        
        # List files in dataset
        print("Files in dataset:")
        files = api.dataset_list_files(dataset_slug)
        video_files = [f for f in files if f.name.endswith(('.mp4', '.avi', '.mov', '.mkv'))]
        
        if not video_files:
            print("No video files found in dataset")
            return None
            
        for i, file in enumerate(video_files[:5], 1):  # Show first 5 videos
            print(f"  {i}. {file.name} ({file.size} bytes)")
        
        # Download first video file
        video_file = video_files[0]
        print(f"\nDownloading: {video_file.name}")
        
        api.dataset_download_file(
            dataset=dataset_slug,
            file_name=video_file.name,
            path=str(download_dir),
            force=True,
            quiet=False
        )
        
        # Handle zip extraction
        video_path = download_dir / video_file.name
        zip_path = video_path.with_suffix(video_path.suffix + '.zip')
        
        if zip_path.exists() and not video_path.exists():
            print(f"Extracting {zip_path}")
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(download_dir)
            zip_path.unlink()  # Remove zip file
        
        if video_path.exists():
            print(f"Downloaded: {video_path}")
            return str(video_path)
        else:
            print(f"Download failed: {video_path}")
            return None
            
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        return None

def analyze_video(video_path):
    """Analyze the downloaded video"""
    try:
        print(f"\nAnalyzing video: {video_path}")
        
        # Import our video analyzer
        sys.path.append(str(Path(__file__).parent))
        from video_analysis.video_analyzer import VideoAnalyzer
        
        analyzer = VideoAnalyzer()
        result = analyzer.analyze(video_path, frame_skip=5, max_frames=200)
        
        print("\nAnalysis Results:")
        print(f"  Video: {result['video_path']}")
        print(f"  Resolution: {result['resolution']['width']}x{result['resolution']['height']}")
        print(f"  FPS: {result['fps']}")
        print(f"  Total Frames: {result['total_frames']}")
        print(f"  Analyzed Frames: {result['analyzed_frames']}")
        print(f"  Avg Moving Objects: {result['avg_moving_objects']}")
        print(f"  Peak Moving Objects: {result['peak_moving_objects']}")
        print(f"  Density Level: {result['density_level']}")
        
        return result
        
    except Exception as e:
        print(f"Error analyzing video: {e}")
        return None

def main():
    """Main function"""
    print("Traffic Video Dataset Downloader & Analyzer")
    print("=" * 50)
    
    # Setup Kaggle credentials
    if not setup_kaggle_credentials():
        return
    
    # Download dataset
    video_path = download_traffic_dataset()
    if not video_path:
        return
    
    # Analyze video
    result = analyze_video(video_path)
    if result:
        print("\nAnalysis complete!")
        print(f"Video saved at: {video_path}")
        print("Open dashboard at http://localhost:8501 to view results")
    else:
        print("Analysis failed")

if __name__ == "__main__":
    main()
