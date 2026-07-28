# -*- coding: utf-8 -*-
"""
fix_srt_whisper.py - 修正 srts_whisper_large-v3/ 的系统性 ASR 错误
针对 Whisper large-v3 的专有名词/术语系统性误识别 (已逐条上下文核验)。
原则: 长串优先 (按长度降序替换, 避免子串冲突); 仅改文本不动时间轴。
"""
import os, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (wrong, correct) — 已通过上下文核验的 Whisper 系统性错误
FIXES = [
    # ===== 科举/官职术语 =====
    ("只有树极势", "只有庶吉士"),
    ("只有树极士", "只有庶吉士"),
    ("树极士", "庶吉士"),
    ("树极势", "庶吉士"),
    ("汉林院边修", "翰林院编修"),
    ("翰林边修", "翰林编修"),
    ("汉林边修", "翰林编修"),
    ("汉林院", "翰林院"),
    ("进汉林", "进翰林"),
    ("可进汉林", "可进翰林"),
    ("这汉林", "这翰林"),
    ("汉林", "翰林"),
    ("碳化徐杰", "探花徐阶"),
    ("碳化", "探花"),
    ("头灯奖", "一甲"),
    ("三灯奖", "三甲"),
    ("建考官", "见考官"),
    # ===== 人名 =====
    ("阎师范", "严世蕃"),
    ("阎松", "严嵩"),
    ("徐杰", "徐阶"),
    ("夏严", "夏言"),
    ("杨申", "杨慎"),
    ("费洪", "费宏"),
    # ===== 地名 =====
    ("宏都", "洪都"),
    ("芦州", "庐州"),
    ("福建严平", "福建延平"),
    ("严平", "延平"),
]


def apply_fixes(text):
    for wrong, correct in sorted(FIXES, key=lambda x: -len(x[0])):
        if wrong and wrong in text:
            text = text.replace(wrong, correct)
    return text


def process_dir(srt_dir):
    files = sorted(glob.glob(os.path.join(srt_dir, "*.srt")),
                   key=lambda p: int(re.search(r'(\d+)', os.path.basename(p)).group(1)))
    print(f"Processing {len(files)} files; {len(FIXES)} fix rules")
    modified = 0
    changes = {}
    for fp in files:
        content = open(fp, encoding="utf-8").read()
        new = apply_fixes(content)
        if new != content:
            open(fp, "w", encoding="utf-8").write(new)
            modified += 1
            for wrong, correct in FIXES:
                n = content.count(wrong)
                if n:
                    changes[wrong] = changes.get(wrong, 0) + n
    print(f"Done. Modified {modified}/{len(files)} files.")
    for w, n in sorted(changes.items(), key=lambda x: -x[1]):
        correct = next(c for ww, c in FIXES if ww == w)
        print(f"  {w} -> {correct}: {n}")


if __name__ == "__main__":
    process_dir(os.path.join(ROOT, "srts_whisper_large-v3"))
