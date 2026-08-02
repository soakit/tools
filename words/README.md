# 英语词汇工具

整理小学三年级词汇与高中 3500 词表，并生成可打印的 A4 PDF 学习材料（介绍页 + 默写页）。

## 目录结构

```
words/
├── README.md              # 本说明
├── build_senior.py        # 从 3500.docx 生成 senior.json
├── generate_pdf.py        # PDF 生成脚本
├── coca_loader.py         # COCA 词频 / 音标 / 释义加载
├── assets/                # 词表与输出文件
│   ├── 3500.docx          # 原始高中 3500 词表
│   ├── 三年级.json         # 三年级上下册合并词表
│   ├── 三年级上.json / 三年级下.json
│   ├── senior.json        # 3500 剔除三年级后的词汇（约 3210 词）
│   ├── coca-index.json    # COCA 索引缓存
│   └── *.pdf              # 生成的 PDF
└── vendor/
    └── coca-vocabulary-20000/   # COCA 词频参考库（git clone）
```

## 词表说明

| 文件 | 说明 |
|------|------|
| `三年级.json` | 上册 165 词 + 下册 182 词，共 347 词 |
| `senior.json` | 从 `3500.docx` 提取，剔除已在三年级出现的词，剩约 3210 词 |
| `coca-index.json` | COCA 全量索引：`by_rank` 20200 条（按词频排名）+ `by_word` 17634 条（去重便于查词） |

### coca-index.json 结构

```json
{
  "meta": { "total": 20200, "unique_words": 17634 },
  "by_rank": {
    "1": { "rank": 1, "word": "the", "phonetic_us": "...", "phonetic_uk": "...", "paraphrase": "...", "meanings": [] },
    "20200": { ... }
  },
  "by_word": {
    "the": { "rank": 1, ... }
  }
}
```

- **by_rank**：20200 条，与 COCA 词频排名一一对应（同形异义词会占多个 rank，如 `to` 在 #7 和 #9）
- **by_word**：17634 条，按单词去重，查词时用最高频（最小 rank）那条

**三年级**（按单元分组）：

```json
{
  "上": [{ "unit": "Unit 1", "words": [{ "word": "happy", "meaning": "开心的", "level2": true }] }],
  "下": [...]
}
```

**senior**（按字母分组）：

```json
{
  "words_by_letter": [{
    "letter": "A",
    "words": [{ "word": "abandon", "definition": "v. 放弃, 遗弃" }]
  }]
}
```

## 环境准备

```bash
pip3 install reportlab
```

PDF 生成依赖系统字体：

- 中文：宋体（`/System/Library/Fonts/Supplemental/Songti.ttc`）
- 英文 / IPA 音标：Arial Unicode（`/Library/Fonts/Arial Unicode.ttf`）

首次使用需拉取 COCA 参考库：

```bash
cd words
git clone --depth 1 https://github.com/llt22/coca-vocabulary-20000.git vendor/coca-vocabulary-20000
```

## 更新词表

`3500.docx` 更新后，重新生成 `senior.json`：

```bash
cd words
python3 build_senior.py
```

## 生成 PDF

```bash
cd words

# 生成全部词汇（约 3210 词，按 COCA 词频排序）
python3 generate_pdf.py --output assets/senior-full.pdf

# 从指定词频开始
python3 generate_pdf.py --start-rank 2600 --output assets/from-2600.pdf

# 限制词数（试打样例）
python3 generate_pdf.py --limit 30 --output assets/sample.pdf

# 只生成某个词
python3 generate_pdf.py --word arise --output assets/arise.pdf

# 重建 COCA 索引缓存
python3 generate_pdf.py --rebuild-coca --output assets/out.pdf
```

### 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--input` | `assets/senior.json` | 输入词表 |
| `--output` | `assets/sample-2pages.pdf` | 输出 PDF 路径 |
| `--start-rank` | `1` | 从 COCA 词频排名开始（含该排名） |
| `--limit` | 无限制 | 最多生成多少个词 |
| `--word` | 无 | 只生成指定单词 |
| `--rebuild-coca` | — | 强制重建 `coca-index.json` |

## PDF 版式

每组词占 **2 页**，交替输出：

1. **介绍页** — 双列，中间竖线，含词频、音标、译 / 变 / 配 / 例  
2. **默写页** — 同一批词，只显示中文释义，供填写英文  

页组大小按介绍页与默写页中较高的块动态计算，保证成对页面都能排下。每组约 **4–6** 个词。

```
[介绍页 第1组] → [默写页 第1组] → [介绍页 第2组] → [默写页 第2组] → …
```

## 数据来源

- **3500 词表**：`assets/3500.docx`（山东高考英语词汇）
- **三年级词表**：上海教育出版社教材 Word list 整理
- **COCA 词频 / 音标 / 释义**：[llt22/coca-vocabulary-20000](https://github.com/llt22/coca-vocabulary-20000)

## 常见问题

**音标显示为空白或缺字？**  
确认系统已安装 Arial Unicode 字体；音标必须用支持 IPA 的字体，不能用宋体。

**COCA 索引找不到词？**  
部分词（短语、缩写、带括号变体）可能匹配不到，此时音标留空，词频显示为 `—`，并排在列表末尾。

**默写页和介绍页词数不一致？**  
现在介绍页与默写页成对出现，同一组词页内容一致；每组词数按两种页面中较高的块统一计算。
