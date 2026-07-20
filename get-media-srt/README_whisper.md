# 视频/音频转 SRT 字幕工具 (Whisper large-v3)

本工具使用 `faster-whisper` 引擎和 `large-v3` 模型，自动将视频和音频文件转写为带有精准时间戳的 SRT 字幕文件。

## 功能特点
- **高精度转写**：使用目前效果最好的开源 `large-v3` 模型。
- **硬件加速 / 自动检测**：
  - 如果检测到兼容的 GPU（CUDA），将自动使用 GPU（`cuda`）和 `float16` 运行。
  - 若无 GPU，将自动回退到 CPU（`cpu`），并使用 `int8` 量化进行高效的本地计算。
- **离线运行**：支持完全离线在本地运行。
- **抗幻觉（Anti-hallucination）**：Whisper 在「静音 / 纯背景音乐」片段上极易陷入重复循环，
  反复输出同一句话（典型现象：同一句"请不吝点赞 订阅 打赏支持明镜与点点栏目"被刷几十遍）。
  本工具做了两层防护，详见下文 [抗幻觉机制](#抗幻觉机制)。

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

## 抗幻觉机制

在某些音频上（尤其是评书、播客这类"开场白 + 大段背景音乐 / 静音"的结构），
Whisper 会陷入"重复循环幻觉"：解码器把自己上一段的输出再次喂回模型，
导致同一句广告词或口头禅被无限重复刷屏。

本脚本从两个层面解决：

### 1. 解码器层（transcribe 参数）
| 参数 | 值 | 作用 |
| --- | --- | --- |
| `condition_on_previous_text` | `False` | **最关键**。不再把上一段输出回喂给解码器，直接打断重复循环的根因。 |
| `hallucination_silence_threshold` | `2.0` | 跳过超过 2 秒的静音段（幻觉最常发生的地方）。需 `word_timestamps=True`。 |
| `no_speech_threshold` | `0.6` | 丢弃"几乎不是语音"的低概率片段。 |
| `word_timestamps` | `True` | 启用词级时间戳，让上面的静音过滤生效。 |
| `vad_parameters` | 见源码 | 调优 Silero VAD 的阈值、静音时长、填充等参数，更准确地保留真正人声。 |

### 2. 输出层（`dedup_segments` 后处理）
即便解码器仍然偶发重复，`write_srt` 写出前会调用 `dedup_segments`：
- 对每条字幕做归一化（去标点、去空白、NFKC、小写），让"请不吝点赞，订阅"
  与"请不吝点赞 订阅"被识别为同一条；
- 在一个滚动窗口（默认最近 8 条）内，若同一句文本已出现 ≥ `max_repeats`（默认 2）次，
  后续重复条目直接丢弃；
- 空白条目一律丢弃。

因此即便模型偶尔"卡壳"，最终落盘的 `.srt` 仍是干净的。
若你想更激进或更宽松，可调整 `transcribe_to_srt_whisper.py` 中
`dedup_segments(segments, max_repeats=2, window=8)` 的两个参数。

## 测试

```bash
python -m unittest test_transcribe_whisper -v
```

覆盖了设备检测、输入收集、文本归一化、以及各类重复 / 空字幕去重场景（包括
"同一句广告词循环 20 次"的真实 bug 用例）。

## 常见问题

**Q：为什么我用 `large-v3` 在 CPU 上跑很慢？**
A：`large-v3` 在 CPU 上对 10 分钟音频可能需要 10 分钟以上。本地无 GPU 时，
建议先用 `small` 或 `medium` 验证流程：
```bash
python transcribe_to_srt_whisper.py <文件路径> small
```

**Q：输出里还有少量重复怎么办？**
A：把 `dedup_segments` 的 `max_repeats` 调成 `1`（同一句在窗口内最多出现一次），
或把 `window` 调大（如 `12`）以覆盖更远的重复。