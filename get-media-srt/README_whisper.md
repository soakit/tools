# 视频/音频转 SRT 字幕工具 (Whisper large-v3)

本工具使用 `faster-whisper` 引擎和 `large-v3` 模型，自动将视频和音频文件转写为带有精准时间戳的 SRT 字幕文件。

## 功能特点
- **高精度转写**：使用目前效果最好的开源 `large-v3` 模型。
- **硬件加速 / 自动检测**：
  - 如果检测到兼容的 GPU（CUDA），将自动使用 GPU（`cuda`）和 `float16` 运行。
  - 若无 GPU，将自动回退到 CPU（`cpu`），并使用 `int8` 量化进行高效的本地计算。
- **离线运行**：支持完全离线在本地运行。

## 环境要求
安装依赖：
```bash
pip install faster-whisper torch ctranslate2
```

## 使用说明
在命令行中运行脚本，并传入视频或音频文件路径：
```bash
python transcribe_to_srt_whisper.py <音视频文件路径> [model_name]
```
- `<音视频文件路径>`：输入的音视频文件（例如 `.mp3`, `.wav`, `.mp4` 等）。
- `[model_name]`：可选参数，使用的 Whisper 模型。默认为 `large-v3`。可选值包括：`tiny`, `base`, `small`, `medium`, `large-v3`。

### 离线模式
要完全离线使用本地下载缓存的模型，请设置环境变量：
- Windows (PowerShell):
  ```powershell
  $env:HF_HUB_OFFLINE="1"
  python transcribe_to_srt_whisper.py <文件路径>
  ```
- Linux/macOS:
  ```bash
  HF_HUB_OFFLINE=1 python transcribe_to_srt_whisper.py <文件路径>
  ```
