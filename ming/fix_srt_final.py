# -*- coding: utf-8 -*-
"""
fix_srt_final.py - 合并后字幕的综合文本修复
整合 fix_srt.py / r2 / r3 / r4 + 本轮新发现
原则: 长串优先; 上下文敏感短词用条件/正则; 仅改文本不动时间轴
"""

import os
import re
import glob


def build_replacements():
    rules = []

    # ====================================================================
    # A. 本轮新发现 (上下文敏感, 长串优先)
    # ====================================================================

    # --- 郑通飞 (嘉靖方士, 第488-500集) ---
    # SenseVoice: 正通飞/正通/正通妃 ; Whisper: 郑通飞
    # 两个 AI 一致识别 "通飞/通" 音, 保留 "郑通飞" 为完整人名
    rules.extend([
        ("正通飞一琢磨", "郑通飞一琢磨"),
        ("正通飞着一瓶子", "郑通飞这一瓶子"),
        ("这正通飞呀", "这郑通飞呀"),
        ("这正通飞", "这郑通飞"),
        ("无赖正通飞", "无赖郑通飞"),
        ("正通飞", "郑通飞"),
        ("正通妃呀", "郑通飞呀"),
        ("正通妃", "郑通飞"),
        ("叫正通", "叫郑通飞"),
        ("这正通", "这郑通"),
        ("他叫正通", "他叫郑通飞"),
    ])

    # --- 翟鸾 (嘉靖首辅, 第599-600集) ---
    rules.extend([
        ("老宅鸾", "老翟鸾"),
        ("这宅鸾呐", "这翟鸾呐"),
        ("这宅鸾的脑袋", "这翟鸾的脑袋"),
        ("这宅鸾一琢磨", "这翟鸾一琢磨"),
        ("宅鸾外出", "翟鸾外出"),
        ("宅鸾", "翟鸾"),
        ("翟伦很好奇", "翟鸾很好奇"),
        ("翟伦", "翟鸾"),
    ])

    # --- 刘瑾 (正德太监, "刘锦" 误识; 用正则排除 刘锦绣/刘坚 等) ---
    # 见 REGEX_RULES

    # --- 内阁首辅 ("首府" 在内阁/宰辅语境 -> "首辅") ---
    rules.extend([
        ("夏首府", "夏首辅"),
        ("内阁首府", "内阁首辅"),
        ("当朝首府", "当朝首辅"),
        ("当朝的首府", "当朝的首辅"),
        ("老首府", "老首辅"),
        ("这首府大臣", "这首辅大臣"),
        ("首府大人", "首辅大人"),
        ("首府家的亲戚", "首辅家的亲戚"),
        ("首府衙门", "首辅衙门"),
        ("你家首府", "你家首辅"),
        ("我们家首府", "我们家首辅"),
        ("这毕竟是首府的府", "这毕竟是首辅的府"),
        ("这首府多好啊", "这首辅多好啊"),
        # 首府 -> 首辅 的更多上下文 (嘉靖/夏言/张璁 语境)
        ("而如今他是首府", "而如今他是首辅"),
        ("想用这首府的势力", "想用这首辅的势力"),
        ("张首府", "张首辅"),
        ("这张首府", "这张首辅"),
        ("虽说呢还是首府", "虽说呢还是首辅"),
        ("换成别的首府", "换成别的首辅"),
        ("我这首府的面子", "我这首辅的面子"),
        ("当首府", "当首辅"),
        ("这下首府的", "这下首辅的"),
        ("夏言那是首府", "夏言那是首辅"),
    ])

    # --- 都督挥使 (明代官职 "都指挥使") ---
    rules.extend([
        ("都督挥斧", "都督挥使"),
        ("都督挥府", "都督挥使"),
    ])

    # --- 援军 -> 元军 (元末/明初语境, 第7-31集等打北元) ---
    # 仅在明确的元末/王保保语境替换 (长串条件)
    rules.extend([
        ("南边是援军", "南边是元军"),
        ("抵抗百万援军", "抵抗百万元军"),
        ("援军动用了", "元军动用了"),
        ("援军就达到了", "元军就达到了"),
        ("援军的部队", "元军的部队"),
        ("横扫援军", "横扫元军"),
        ("王保保这阵的援军", "王保保这阵的元军"),
        ("云南那边还有十来万的援军", "云南那边还有十来万元的军"),
        ("援军精心设计", "元军精心设计"),
        ("援军那边已经做好了迎战的准备", "元军那边已经做好了迎战的准备"),
        ("援军这才得以攻入", "元军这才得以攻入"),
        ("在援军溃败之后", "在元军溃败之后"),
        ("援军不由得非常高兴", "元军不由得非常高兴"),
    ])

    # ====================================================================
    # B. 合并已有 fix_srt*.py 的全部规则
    # ====================================================================
    rules.extend(_load_existing_rules())
    return rules


def _load_existing_rules():
    out = []
    ROOT = os.path.dirname(os.path.abspath(__file__))
    for fn in ["fix_srt.py", "fix_srt_r2.py", "fix_srt_r3.py", "fix_srt_r4.py"]:
        p = os.path.join(ROOT, fn)
        if not os.path.exists(p):
            continue
        src = open(p, encoding="utf-8").read()
        pairs = re.findall(
            r'\(\s*"((?:[^"\\]|\\.)*)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*\)',
            src,
        )
        for w, c in pairs:
            if "PLACEHOLDER" in w or "PLACEHOLDER" in c:
                continue
            if w == c:
                continue
            out.append((w, c))
    return out


# 正则上下文替换
REGEX_RULES = [
    # 刘锦 -> 刘瑾, 排除 刘锦绣/刘坚/刘锦堂/刘锦华/刘锦衣
    (re.compile(r"刘锦(?!绣|坚|衣|堂|华)"), "刘瑾"),
]


def apply_replacements(text, rules):
    for wrong, correct in rules:
        if wrong and wrong in text:
            text = text.replace(wrong, correct)
    for pat, correct in REGEX_RULES:
        text = pat.sub(correct, text)
    return text


def process_dir(srt_dir):
    files = sorted(glob.glob(os.path.join(srt_dir, "*.srt")))
    rules = build_replacements()
    print(f"Processing {len(files)} files; {len(rules)} literal + {len(REGEX_RULES)} regex rules")
    modified = 0
    for fp in files:
        content = open(fp, encoding="utf-8").read()
        new = apply_replacements(content, rules)
        if new != content:
            open(fp, "w", encoding="utf-8").write(new)
            modified += 1
    print(f"Done. Modified {modified}/{len(files)} files.")


if __name__ == "__main__":
    ROOT = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(ROOT, "srts_merged")
    if not os.path.isdir(target):
        target = os.path.join(ROOT, "srts")
    process_dir(target)
