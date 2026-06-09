# -*- coding: utf-8 -*-
"""
Round 4: Deep calibration of Ming Dynasty subtitles
Focus: residual variants + individual garbled phrases
"""

import os, glob

SRTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "srts")


def build_replacements():
    rules = []

    # === A. ?? variants (long strings first) ===
    rules.extend([
        ("张从简历", "张璁的简历"),
        ("张从根贵恶", "张璁和桂萼"),
        ("张从景", "张璁的"),
        ("张从", "张璁"),
        ("张冲", "张璁"),
        ("张充", "张璁"),
        ("张村", "张璁"),
        ("张崇", "张璁"),
        ("张通", "张璁"),
    ])

    # === B. ?? variants ===
    rules.extend([
        ("贵恶", "桂萼"),
        ("跪恶", "桂萼"),
        ("龟恶", "桂萼"),
    ])
    # ?? -> ?? only in person-name contexts (long strings first)
    rules.extend([
        ("一谈这罪恶就把张璁", "一谈这桂萼就把张璁"),
        ("这张璁罪恶万没想到", "这张璁桂萼万没想到"),
        ("但这罪恶始终", "但这桂萼始终"),
        ("很快把这罪恶这就给", "很快把这桂萼这就给"),
        ("这罪恶是惊魂未定的", "这桂萼是惊魂未定的"),
        ("这罪恶就跟兔子", "这桂萼就跟兔子"),
        ("这罪恶跑到了", "这桂萼跑到了"),
        ("把这罪恶怎么的", "把这桂萼怎么的"),
        ("那就是罪恶", "那就是桂萼"),
        ("罪恶一出现", "桂萼一出现"),
        ("这罪恶呀", "这桂萼呀"),
        ("这罪恶", "这桂萼"),
    ])

    # === C. ?? variants (protect ??????) ===
    rules.extend([
        ("夏延冲牙相迎", "夏言出衙相迎"),
        ("甘肃宁夏延绥", "PLACEHOLDER_XYZ"),
        ("夏延", "夏言"),
        ("PLACEHOLDER_XYZ", "甘肃宁夏延绥"),
        ("夏阳", "夏言"),
    ])

    # === D. ??? ===
    rules.extend([
        ("张艳玲宴", "张延龄案"),
        ("撞到张彦霖的壮志", "状告张延龄的状纸"),
        ("张艳玲", "张延龄"),
        ("张彦霖", "张延龄"),
    ])

    # === E. Individual garbled phrases ===
    rules.extend([
        ("公鸡这可就开始了", "攻击这可就开始了"),
        ("14421", "1442年"),
        ("世王镇国村之路", "人世 王振从此之路"),
        ("在阳之中", "在朝之中"),
        ("杨龙已经去世", "杨荣已经去世"),
        ("稍显杨氏及杨宇也是年郎作宾", "少师杨士奇和杨荣也是年老体衰"),
        ("希腊科之谷里", "锡兰柯枝之古里"),
        ("赞成伯尼", "占城浦泥"),
        ("鹿比一剑", "一路比一见"),
        ("卓就业", "国舅爷"),
        ("我在明晃晃的住过", "我在这明处住着"),
        ("正中把这酒杯", "正经把这酒杯"),
        ("半难抵赖", "百般抵赖"),
        ("那阵就王振等了多少机会", "那阵儿王振等了多少机会"),
        ("这就是夏延夏首府", "这就是夏言夏首辅"),
        ("但是见到了夏延夏首府之后", "但是见到了夏言夏首辅之后"),
        ("夏延是个班的老头子", "夏言是个半的老头子"),
    ])

    return [(w, c) for w, c in rules if w != c]


def apply_replacements(text, rules):
    for wrong, correct in rules:
        text = text.replace(wrong, correct)
    return text


def process_srt_file(filepath, rules):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = apply_replacements(content, rules)
    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    return False


def main():
    rules = build_replacements()
    srt_files = sorted(glob.glob(os.path.join(SRTS_DIR, "*.srt")))
    total = len(srt_files)
    modified = 0
    print(f"Round 4: {total} SRT files, {len(rules)} rules")
    for i, fp in enumerate(srt_files, 1):
        if process_srt_file(fp, rules):
            modified += 1
            print(f"  [{i:3d}/{total}] {os.path.basename(fp)}")
    print(f"Done! Modified: {modified}/{total}")


if __name__ == "__main__":
    main()
