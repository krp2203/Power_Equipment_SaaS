# FFmpeg Video Thumbnail Deployment Strategy

This document outlines the strategy for deploying FFmpeg for video thumbnail generation, based on the resource constraints identified during the February 21, 2026 session.

---

## 1. THE PROBLEM: RESOURCE EXHAUSTION
Adding FFmpeg directly to the primary `Dockerfile` currently causes build failure or system instability:
- **Build Context:** The current codebase is ~2.5GB.
- **Disk Usage:** Building the image with `apt-get install ffmpeg` consumes ~99% of available disk space (16GB total).
- **RAM Usage:** Building and running consumes ~94% of memory (4GB total).
- **Result:** Data loss and container crashes.

---

## 2. RECOMMENDED DEPLOYMENT STRATEGIES

### Strategy A: Pre-built Docker Image (PREFERRED)
Build the image on a machine with more resources (min 8GB RAM, 50GB Disk) and push to a registry (e.g., Docker Hub or GitHub Packages).
- Avoids building locally on the production server.
- Reduces production downtime.

### Strategy B: Separate Microservice
Deploy FFmpeg in a lightweight separate container (e.g., `jrottenberg/ffmpeg`) that handles only the thumbnail extraction.
- Keeps the main `web` container small.
- Isolates resource-heavy processing.

### Strategy C: Lazy Installation
Only install FFmpeg if it's actually detected as missing, or use a "Binary-only" approach to save disk space.

---

## 3. IMPLEMENTATION DETAILS

### Video Thumbnail Function
The following logic has been prepared for `app/modules/marketing/routes.py`:

```python
import subprocess
import os

def generate_video_thumbnail(video_path, output_path, timestamp='00:00:01'):
    """
    Extracts a frame from a video at a specific timestamp using FFmpeg.
    """
    try:
        # Extract 1 frame at the 1-second mark
        # Output as 400x300 JPEG with low quality (save space)
        cmd = [
            'ffmpeg', '-ss', timestamp, 
            '-i', video_path, 
            '-vframes', '1', 
            '-q:v', '5', 
            '-s', '400x300', 
            '-y', output_path
        ]
        
        # 30-second timeout to prevent hung processes
        subprocess.run(cmd, check=True, timeout=30, capture_output=True)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"FFmpeg Error: {e}")
        return False
```

### Gracious Fallback
If FFmpeg is not available, the system falls back to a PIL-generated placeholder:
- **Design:** Dark top half + white bottom half.
- **Icon:** Red play button circle with white triangle.
- **Text:** Overlays the video title.

---

## 4. SYSTEM REQUIREMENTS FOR DEPLOYMENT
- **CPU:** 2+ Cores recommended.
- **RAM:** 8GB+ (for stable builds and concurrent processing).
- **Disk:** 50GB+ (to handle temp files and large Docker layers).
