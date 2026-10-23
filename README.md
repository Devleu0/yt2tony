# Youtube Vocal Splitter

[한국어](./README.ko.md) | English

A pipeline tool that downloads YouTube audio, isolates vocals using Demucs, and automatically loads the result into the Tony visualizer. Optimized for NVIDIA GPUs with low VRAM (e.g., RTX 3050 4GB).

## System Requirements

- **OS**: Windows 10/11
- **Python**: 3.11
- **GPU**: NVIDIA GPU (CUDA 12.8 compatible driver)
- **External Dependencies**:
  - **FFmpeg**: Must be installed and added to the system `PATH`.
  - **Tony**: Melody transcription software. Installed at `C:\Program Files\Tony\tony.exe`. ([Download Tony](https://code.soundsoftware.ac.uk/projects/tony))

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Devleu0/yt2tony.git
   cd yt2tony
   ```

2. Install Python 3.11 and FFmpeg. Tony is optional and can be installed separately.

3. Run `run.bat` from File Explorer or a command prompt. On its first run, it creates a local `.venv`, installs CUDA-enabled PyTorch and the project dependencies, then opens the browser-based interface. Later runs reuse the environment.

   The setup uses PyTorch's CUDA 12.8 wheels; a compatible NVIDIA driver is required. If no supported NVIDIA GPU is available, the program falls back to CPU.

Verify FFmpeg is available:
```bash
ffmpeg -version
```

## Usage

Enter a YouTube video URL and press Enter or select **보컬 분리 후 Tony 열기**. Once separation finishes, the vocal track opens in Tony automatically. The history list keeps each link and its vocal/instrumental results; select an earlier item to open either track in Tony again. The existing result is also added to the history, but its original link was not recorded.

Each run saves separate files under `output/htdemucs/<run-id>/`, and the history database is stored in `output/history.sqlite3`. Tony is optional; if it is not installed at `C:\Program Files\Tony\tony.exe`, set the `TONY_EXE` environment variable to its executable path.

## License

This project is licensed under the GNU General Public License v3.0 only. See [LICENSE](./LICENSE) for the full terms.

## Architecture & Optimization

- **Audio Format**: Uses MP3 encoding instead of WAV to reduce disk I/O bottlenecks and storage requirements.
- **VRAM Constraint Management**: The Demucs parameter `--segment 2` is hardcoded to prevent Out of Memory (OOM) exceptions on 4GB VRAM environments.
- **Playlist Handling**: Hardcoded `--no-playlist` flag in `yt-dlp` prevents unintended batch downloads.

## Directory Structure

Upon successful execution, output files are stored as follows:
```text
output/
├── history.sqlite3
└── htdemucs/
    └── <run-id>/
        ├── vocals.mp3
        └── no_vocals.mp3
```

## Troubleshooting

- **OOM (Out of Memory) Error during Demucs execution**: Ensure no other VRAM-heavy applications (e.g., games, 3D software) are running in the background.
- **FFmpeg not found**: Ensure the `bin` folder of your FFmpeg installation is explicitly added to the Windows environment variables (`PATH`).