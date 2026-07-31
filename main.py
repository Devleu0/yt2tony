import os
import subprocess
import sys
import shutil

try:
    import torch
except ImportError:
    print("[Error] PyTorch module not found. Execute via run.bat.")
    sys.exit(1)

def main():
    print("==================================================")
    
    # Check GPU availability
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        print(f"[Info] CUDA Device detected: {gpu_name}")
        device = "cuda"
    else:
        print("[Warning] CUDA Device not found. Falling back to CPU mode.")
        device = "cpu"
    
    print("==================================================")
    url = input("Youtube URL: ").strip()
    
    if not url:
        print("[Error] URL cannot be empty. Exiting.")
        sys.exit(1)

    output_dir = os.path.abspath("output")
    temp_dir = os.path.abspath("temp")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)

    # 1. Download & convert to MP3 via yt-dlp
    print("[Process 1/3] Extracting audio to MP3 format...")
    temp_audio_path = os.path.join(temp_dir, "input_track.mp3")

    ytdlp_cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--no-playlist",
        "--force-overwrite",
        "-o", temp_audio_path,
        url
    ]

    try:
        subprocess.run(ytdlp_cmd, check=True)
        print("[Info] Audio extraction completed.")
    except subprocess.CalledProcessError:
        print("[Error] yt-dlp execution failed. Check URL or network connection.")
        sys.exit(1)

    # 2. Vocal separation via Demucs
    print("[Process 2/3] Separating vocals using Demucs...")
    
    demucs_cmd = [
        "demucs",
        "--two-stems", "vocals",
        "--mp3",
        "-d", device,
        "--segment", "2",    # Avoid OOM on 4GB VRAM GPUs (e.g., RTX 3050)
        "-o", output_dir,
        temp_audio_path
    ]

    try:
        subprocess.run(demucs_cmd, check=True)
        print("[Info] Vocal separation completed.")
        
        # Cleanup temporary files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            
    except subprocess.CalledProcessError:
        print("[Error] Demucs execution failed. Verify FFmpeg installation and system memory.")
        sys.exit(1)

    # 3. Load result in Tony Visualizer
    print("[Process 3/3] Launching Tony visualizer...")
    
    vocal_path = os.path.join(output_dir, "htdemucs", "input_track", "vocals.mp3")
    tony_exe_path = r"C:\Program Files\Tony\tony.exe" 
    
    if os.path.exists(tony_exe_path) and os.path.exists(vocal_path):
        subprocess.Popen([tony_exe_path, vocal_path])
        print("[Info] Process finished successfully.")
    else:
        print(f"[Warning] Tony executable not found at: {tony_exe_path}")
        print("[Info] Opening output directory instead.")
        
        result_dir = os.path.join(output_dir, "htdemucs", "input_track")
        if os.path.exists(result_dir) and os.name == 'nt':
            os.startfile(result_dir)

if __name__ == "__main__":
    main()