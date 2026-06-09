# get-media-srt

将音频或视频自动转写为 SRT 字幕文件。基于阿里 [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) 模型（通过 [FunASR](https://github.com/modelscope/FunASR) 调用），针对中文语音识别做了优化，支持长音频分段识别和字级时间戳。

## 功能特点

- 支持单文件或整个目录批量转写
- 输出标准 SRT 字幕，可直接用于播放器或剪辑软件
- 内置 VAD（`fsmn-vad`）自动切分长音频
- 根据标点与时间戳智能分段，避免整段音频只有一条字幕
- 批量模式只加载一次模型，处理多个文件更高效
- 自动跳过已有 `.srt` 的文件，方便断点续跑

## 支持的格式

| 类型 | 扩展名 |
|------|--------|
| 音频 | `.mp3` `.wav` `.m4a` `.flac` `.ogg` |
| 视频 | `.mp4` `.mkv` `.avi` |

## 环境要求

- **Python 3.11+**（SenseVoice / FunASR 依赖较新的 Python，3.8 不可用）
- Windows / macOS / Linux 均可
- 默认使用 CPU 推理；有 NVIDIA GPU 可自行改脚本中的 `device` 参数

## 安装

```powershell
# 推荐使用 Python 3.11
py -3.11 -m pip install funasr torch torchaudio
```

首次运行时会从 ModelScope 自动下载模型（约数百 MB），缓存目录：

```
C:\Users\<用户名>\.cache\modelscope\hub\
```

国内网络可设置 Hugging Face 镜像（脚本已默认启用）：

```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
```

## 使用方法

### 转写单个文件

```powershell
py -3.11 transcribe_to_srt.py "mp3\122.第122集.mp3"
```

输出文件与源文件同名，扩展名改为 `.srt`：

```
mp3\122.第122集.mp3  →  mp3\122.第122集.srt
```

### 批量转写目录

传入目录路径即可，会自动处理目录下所有支持的音频/视频文件：

```powershell
py -3.11 transcribe_to_srt.py "mp3"
```

批量规则：

- 按文件名排序依次处理
- 若同目录下已存在同名 `.srt`，则跳过该文件
- 模型只加载一次，全部文件共用

### 指定模型（可选）

默认模型为 `iic/SenseVoiceSmall`，也可手动指定：

```powershell
py -3.11 transcribe_to_srt.py "audio.mp3" iic/SenseVoiceSmall
```

## 输出示例

```srt
1
00:00:00,330 --> 00:00:04,410
我。

2
00:00:04,900 --> 00:00:20,380
道演和尚，俗家名叫姚广孝，这人呐真就是个怪圣……
```

## 目录结构

```
get-media-srt/
├── transcribe_to_srt.py   # 主脚本
├── README.md
└── mp3/                   # 示例：存放待转写的音频及生成的字幕
    ├── 122.第122集.mp3
    └── 122.第122集.srt
```

## 常见问题

**Q: 提示找不到 `funasr` 或 Python 版本不对？**

确认使用 Python 3.11 运行：

```powershell
py -3.11 --version
py -3.11 -m pip install funasr torch torchaudio
```

**Q: 模型下载很慢或失败？**

检查网络，或手动设置 ModelScope / HF 镜像。模型只需下载一次，之后会走本地缓存。

**Q: 字幕分段太长或太短？**

可在 `transcribe_to_srt.py` 的 `segments_from_words()` 中调整 `max_chars` 参数（默认 36），数值越小分段越细。

**Q: 想重新转写某个文件？**

删除对应的 `.srt` 文件后重新运行即可；批量模式会自动识别并重新处理。

## 参考

- [SenseVoice](https://github.com/FunAudioLLM/SenseVoice)
- [FunASR](https://github.com/modelscope/FunASR)
- [ModelScope - SenseVoiceSmall](https://www.modelscope.cn/models/iic/SenseVoiceSmall)
