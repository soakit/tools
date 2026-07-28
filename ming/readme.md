# 大明王朝

根据著名历史作品《明朝那些事儿》改编的国产历史动画。从朱元璋出生讲起，到崇祯皇帝自缢、明朝灭亡，以史料为基础，以年代和具体人物为主线，以动画评书的形式，对明朝十七帝及王公权贵、小人物的命运进行全景展示，尤其侧重官场政治、战争、帝王心术，并加入对当时政治经济制度、人伦道德的演义。

| 项目 | 信息 |
|------|------|
| 导演 | 王建、王玉 |
| 编剧 | 赵璐 |
| 类型 | 动画 / 历史 |
| 制片国家/地区 | 中国大陆 |
| 语言 | 汉语普通话 |
| 首播 | 2009（中国大陆） |
| 单集片长 | 约 12 分钟 |

## 观看链接

- [豆瓣 · 大明王朝](https://movie.douban.com/subject/35083148/)
- [哔哩哔哩 · 大明王朝 第八季](https://www.bilibili.com/bangumi/play/ss44424)（全 60 话，2023，已完结）
- [哔哩哔哩 · 大明王朝 第九季](https://www.bilibili.com/bangumi/play/ss44425)（全 60 话，2023，已完结）
- [哔哩哔哩 · 608集 ](https://www.bilibili.com/video/BV1Bp411Z71q/?spm_id_from=333.337.search-card.all.click)

B 站可搜索「大明王朝」查看完整系列，各季分集上线。

## 项目结构

```
ming/
├── readme.md                      本说明
├── 明朝那些事儿 (全7册).epub        原著电子书（标题生成的章节来源）
│
├── scripts/                       处理脚本（按功能分类）
│   ├── merge_srts.py              字幕合并：SenseVoice + Whisper 逐句择优
│   ├── fix_srt_final.py           文本修正：500+ 条专名/术语替换规则（被 merge_srts 引用）
│   ├── fix_srt_whisper.py         Whisper 专属修正：系统性 ASR 误识别（如 徐杰→徐阶）
│   └── gen_titles.py              标题生成：基于 epub 章节为各集匹配简短标题
│
├── data/                          生成的数据与缓存
│   ├── _episode_titles_clean.json  清洗后的集标题（merge_srts 用于输出文件名）
│   ├── episode_titles.json         gen_titles 直接输出的集标题
│   ├── _merge_borrowed.json        merge_srts 借鉴 Whisper 的句段调试日志
│   └── _chapters.json              从 epub 抽取的章节正文缓存
│
├── docs/                          文档
│   └── WHISPER_NOTES.md           Whisper 字幕修正工作笔记
│
├── srts/                          SenseVoice 识别字幕（原始）
├── srts_whisper_large-v3/         Whisper large-v3 识别字幕（原始）
├── srts_merged/                   合并优化后的最终字幕（输出）
└── srts_continued/                AI 基于原著续写的后续集文本
```

> 脚本统一用 `__file__` 定位项目根，因此在任意目录下执行均可。

## 脚本说明

### 1. 字幕合并 — `scripts/merge_srts.py`

在 `srts/`（SenseVoice）与 `srts_whisper_large-v3/`（Whisper large-v3）两套 AI 识别结果基础上，逐句择优并修复文本错误，得到更优版本。

#### 两套原始字幕的特点

| 来源 | 优点 | 缺点 |
|------|------|------|
| `srts/`（SenseVoice） | 时间轴稳定、断句细致、专有名词（人名/年号/官职/地名）识别准确、无幻觉 | 个别句子漏识别、少量同音错字 |
| `srts_whisper_large-v3/`（Whisper） | 句意更完整、语气词齐全 | **专有名词系统性错误**（如 谭渊→台渊、朱能→朱囊、耿炳文→钢饼纹、刘瑾→刘锦），且约 62% 的集存在严重幻觉（30 秒长条、重复"请不吝点赞订阅"广告段、整段标点拼接） |

#### 合并策略

1. **基底采用 SenseVoice**：时间轴与结构稳定，专名可靠。
2. **句级择优借鉴 Whisper**：仅当某段 Whisper 满足以下全部条件时，才用其文本替换对应 SenseVoice 段（仍保留 SenseVoice 时间轴）：
   - 该段无广告幻觉（"请不吝点赞订阅"等）、非 30 秒长条、无连续重复、无标点幻觉；
   - 该段未被合并成一对多（避免借鉴被 Whisper 拼接的超长段）；
   - Whisper 归一化文本**包含** SenseVoice 归一化文本为子串（仅补全句尾/语气词），防止 Whisper 把 SenseVoice 中正确的人名替换成错误人名。
3. **统一文本修复**：调用 `fix_srt_final.py` 的替换规则，纠正两套识别共同的残留错误（人名错形、官职误识、年号错字等）。

#### 运行方式

```powershell
python scripts/merge_srts.py
```

- 输入：`srts/`、`srts_whisper_large-v3/`、`data/_episode_titles_clean.json`
- 输出：`srts_merged/`（608 集，约 108,000 段）、`data/_merge_borrowed.json`（借鉴日志）
- 文本修复规则：`scripts/fix_srt_final.py`

### 2. 文本修正 — `scripts/fix_srt_final.py`

合并后字幕的综合文本修正，提供字面替换规则（`build_replacements()`）与正则规则（`REGEX_RULES`）。既被 `merge_srts.py` 在合并流程中调用，也可独立运行直接修正某个字幕目录。

```powershell
# 独立运行：默认修正 srts_merged/（若不存在则修正 srts/）
python scripts/fix_srt_final.py
```

已修复的典型错误（节选）：

- 人名：正通飞→郑通飞、宅鸾/翟伦→翟鸾、刘锦→刘瑾（排除"刘锦绣"等）
- 官职：夏首府/张首府→夏首辅/张首辅、都督挥斧→都督挥使
- 军事：援军→元军（仅元末/北元语境，如第 7-8 集；明中期"等待援军"保留）
- 大量历史专名见 `fix_srt_final.py` 词表

### 3. Whisper 专属修正 — `scripts/fix_srt_whisper.py`

针对 `srts_whisper_large-v3/` 的 Whisper 系统性 ASR 误识别做单独修正（如 徐杰→徐阶、阎松→严嵩、夏严→夏言、宏都→洪都、汉林→翰林 等）。详见 `docs/WHISPER_NOTES.md`。

```powershell
python scripts/fix_srt_whisper.py
```

### 4. 标题生成 — `scripts/gen_titles.py`

基于 epub 章节内容，用 5-gram 重叠 + 单调 DP 将每集字幕映射到对应章节，取章节标题（去"第X章"前缀）为该集标题；同章多集加序号。

```powershell
python scripts/gen_titles.py
```

- 输入：`明朝那些事儿 (全7册).epub`、`srts_whisper_large-v3/`
- 输出：`data/episode_titles.json`

## 字幕（srts/）

`srts/` 下存放各集 SRT 字幕文件，命名格式为 `第XXX集.srt`。

**这些字幕由 AI 语音识别自动生成**（使用 [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) 模型，详见仓库内 [`get-media-srt`](../get-media-srt/) 工具），并非官方字幕。可能存在识别错误、断句不当或与画面不同步等问题，仅供学习参考。

生成方式示例：

```powershell
cd ..\get-media-srt
py -3.11 transcribe_to_srt.py "mp3"
```

## 局限

仍是 AI 自动识别字幕，非人工官方校对；专有名词已大幅修正，但偶发的断句不当或漏句难以完全避免，仅供学习参考。
