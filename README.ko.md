# YouTube 보컬 분리기

[English](./README.md) | 한국어

YouTube 동영상에서 오디오를 다운로드하고 Demucs로 보컬과 반주를 분리한 뒤, 결과를 Tony 비주얼라이저에서 열어 주는 Windows 앱입니다. NVIDIA GPU, 특히 VRAM이 적은 환경을 고려해 설정되어 있습니다.

## 주요 기능

- 브라우저 UI에서 YouTube 동영상 링크를 입력해 보컬과 반주를 분리합니다.
- 분리가 완료되면 보컬 트랙을 Tony에서 자동으로 엽니다.
- 작업 이력에 원본 링크와 생성된 파일을 저장합니다.
- 이전 이력을 선택해 보컬 또는 반주를 Tony에서 다시 열 수 있습니다.
- NVIDIA GPU가 없으면 CPU 모드로 실행합니다.

## 요구 사항

- Windows 10 또는 11
- Python 3.11
- 오디오 변환을 위한 FFmpeg 설치 및 `PATH` 등록
- NVIDIA GPU를 사용하는 경우 CUDA 12.8을 지원하는 드라이버
- Tony 비주얼라이저 (선택 사항)

Tony는 기본적으로 `C:\Program Files\Tony\tony.exe`에서 찾습니다. 다른 경로에 설치한 경우 `TONY_EXE` 환경 변수에 `tony.exe`의 전체 경로를 지정하세요. Tony가 없어도 오디오 분리와 파일 저장은 가능합니다.

## 설치 및 실행

1. Python 3.11과 FFmpeg를 설치합니다. FFmpeg가 준비되었는지 확인하려면 명령 프롬프트에서 다음을 실행하세요.

   ```bat
   ffmpeg -version
   ```

2. 저장소를 내려받습니다.

   ```bat
   git clone https://github.com/Devleu0/yt2tony.git
   cd yt2tony
   ```

3. `run.bat`을 실행합니다. 최초 실행 시 프로젝트 폴더에 `.venv` 가상환경을 만들고 PyTorch와 필요한 패키지를 설치한 다음 브라우저 UI를 시작합니다. 이후 실행부터는 기존 환경을 재사용합니다.

   ```bat
   run.bat
   ```

## 사용 방법

1. YouTube 동영상 링크를 입력합니다.
2. Enter 키를 누르거나 **보컬 분리 후 Tony 열기** 버튼을 선택합니다.
3. 다운로드와 분리가 끝나면 보컬 트랙이 Tony에서 자동으로 열립니다.
4. **작업 이력**에서 이전 작업을 선택하고 **보컬을 Tony에서 열기** 또는 **반주를 Tony에서 열기**를 선택하면 해당 파일을 다시 열 수 있습니다.

새 작업마다 별도의 결과 폴더를 사용하므로 이전 결과를 덮어쓰지 않습니다. 최초 실행 시 기존 `output/htdemucs/input_track/` 결과가 있으면 링크 정보가 없는 이력 항목으로 가져옵니다.

## 결과 파일과 이력

```text
output/
├── history.sqlite3
└── htdemucs/
    └── <작업 ID>/
        ├── vocals.mp3
        └── no_vocals.mp3
```

- `vocals.mp3`: 분리된 보컬
- `no_vocals.mp3`: 보컬을 제거한 반주
- `history.sqlite3`: 처리한 링크, 작업 상태, 결과 파일 경로

다운로드한 오디오와 분리 결과는 로컬 프로젝트 폴더에 저장됩니다. `.venv/`, `output/`, `temp/`는 Git에서 제외됩니다.

## 문제 해결

- **FFmpeg를 찾을 수 없음**: FFmpeg의 `bin` 폴더가 시스템 `PATH`에 등록되어 있는지 확인하고, 새 명령 프롬프트에서 `ffmpeg -version`을 실행합니다.
- **GPU 메모리 부족(OOM)**: 다른 GPU 사용 프로그램을 닫은 뒤 다시 시도하세요. 분리 단계는 낮은 VRAM 사용량을 위해 Demucs `--segment 2` 옵션을 사용합니다.
- **Tony를 찾을 수 없음**: Tony 설치 경로를 확인하고 `TONY_EXE` 환경 변수를 지정하세요. 분리된 결과는 UI의 작업 이력에서도 다시 열 수 있습니다.
- **GPU를 사용할 수 없음**: NVIDIA 드라이버가 CUDA 12.8 지원 버전인지 확인하세요. GPU가 인식되지 않으면 CPU 모드로 실행됩니다.

## 라이선스

이 프로젝트는 GNU General Public License v3.0 전용(GPL-3.0-only)입니다. 자세한 조건은 [LICENSE](./LICENSE)를 확인하세요.
