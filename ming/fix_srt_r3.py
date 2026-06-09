# -*- coding: utf-8 -*-
"""
Round 3: Deep calibration of Ming Dynasty subtitles
Focus: misrecognized names, official titles, idioms, garbled phrases
"""

import os
import glob

SRTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "srts")


def build_replacements():
    rules = []

    # === 1. Major name fixes (Round 3) ===

    # 解缙 (Yongle Dadian compiler)
    rules.extend([
        ("小谢进", "小解缙"),
        ("这谢进", "这解缙"),
        ("谢进脑瓜", "解缙脑瓜"),
    ])
    rules.append(("谢晋", "解缙"))
    rules.append(("谢进", "解缙"))

    # 张璁 (Great Rites Controversy figure)
    rules.extend([
        ("张松集团", "张璁集团"),
        ("张松等人", "张璁等人"),
        ("张松手下", "张璁手下"),
        ("这张松也没要", "这张璁也没要"),
        ("这张松的判断", "这张璁的判断"),
        ("这张松对", "这张璁对"),
        ("打倒了张松", "打倒了张璁"),
        ("张松跟人家", "张璁跟人家"),
        ("张松带派", "张璁派"),
    ])
    rules.append(("张聪", "张璁"))
    rules.append(("张松", "张璁"))

    # 朱厚熜 (Jiajing Emperor)
    rules.append(("朱厚聪", "朱厚熜"))
    rules.append(("朱厚骢", "朱厚熜"))

    # 夏言
    rules.extend([
        ("因此上下言得楚", "因此上夏言得宠"),
        ("下言得楚", "夏言得宠"),
        ("这下言算个", "这夏言算个"),
        ("这下言仍旧", "这夏言仍旧"),
        ("这下言都是", "这夏言都是"),
        ("这下言轮番", "这夏言轮番"),
        ("这下言", "这夏言"),
        ("注意这下言", "注意这夏言"),
        ("注意下言", "注意夏言"),
        ("密切注意下言", "密切注意夏言"),
        ("要说这下言", "要说这夏言"),
        ("在下言在", "在夏言在"),
        ("就说这下言", "就说这夏言"),
        ("就说下言", "就说夏言"),
    ])
    rules.append(("夏彦", "夏言"))
    rules.append(("下言", "夏言"))

    # 孙燧
    rules.append(("孙遂", "孙燧"))

    # 桂萼
    rules.append(("桂鄂", "桂萼"))

    # 霍韬
    rules.append(("霍涛", "霍韬"))

    # 郭勋
    rules.append(("国勋", "郭勋"))

    # === 2. R1/R2 residual name fixes ===

    rules.append(("张炳", "张昺"))
    rules.append(("道演", "道衍"))
    rules.append(("道眼", "道衍"))
    rules.append(("学达", "徐达"))
    rules.append(("谢桂", "谢贵"))
    rules.append(("黄子登", "黄子澄"))
    rules.append(("张欣", "张信"))

    # ???/??? variants
    rules.append(("朱厚道", "朱厚照"))
    rules.append(("朱厚到", "朱厚照"))
    rules.append(("朱厚召", "朱厚照"))
    rules.append(("朱右堂", "朱佑堂"))
    rules.append(("朱佑堂", "朱佑樘"))

    # ?? (eunuch, commonly misrecognized as ??)
    rules.append(("张勇", "张永"))

    # === 3. Official title fixes ===

    # 阳关 -> 言官 (protect 阳关道 idiom)
    rules.append(("阳关道", "\x00YANG_GUAN_DAO\x00"))
    rules.append(("阳关", "言官"))
    rules.append(("\x00YANG_GUAN_DAO\x00", "阳关道"))

    # 杨官 -> 言官
    rules.extend([
        ("杀杨官的言官", "杀言官的言官"),
        ("杨官的首领", "言官的首领"),
        ("杨官们", "言官们"),
        ("这杨官", "这言官"),
        ("杨官为啥", "言官为啥"),
        ("杨官叫骂", "言官叫骂"),
        ("御史杨官", "御史言官"),
    ])
    rules.append(("杨官", "言官"))

    # 玉石 -> 御史 (protect real jade references)
    jade_phrases = [
        "玉石俱焚", "玉石俱三", "玉石雕刻", "玉石的貔",
        "玉石这东西", "上边是玉石", "玉石老虎",
    ]
    for jph in jade_phrases:
        tag = "\x00JADE_%d\x00" % hash(jph)
        rules.append((jph, tag))

    rules.extend([
        ("萧玉石", "萧御史"),
        ("王玉石", "王御史"),
        ("玉石大夫", "御史大夫"),
        ("13道玉石", "13道御史"),
        ("道的玉石", "道的御史"),
        ("练六部六科13到玉石", "练六部六科13道御史"),
        ("这些玉石你看", "这些御史你看"),
    ])
    rules.append(("玉石", "御史"))

    for jph in jade_phrases:
        tag = "\x00JADE_%d\x00" % hash(jph)
        rules.append((tag, jph))

    rules.append(("玉石俱三", "玉石俱焚"))

    # 检视/检事 -> proper titles
    rules.extend([
        ("兵部检视", "兵部尚书"),
        ("都督检视", "都督佥事"),
        ("都指挥检事", "都指挥佥事"),
        ("检视府", "检校府"),
        ("检事", "检校"),
    ])

    # === 4. Idiom/phrase fixes ===

    rules.extend([
        ("九囊饭袋", "酒囊饭袋"),
        ("口口应声", "口口声声"),
        ("一冲莫展", "一筹莫展"),
        ("考场失忆", "考场失利"),
        ("脑瓜一拨了", "脑瓜一拨浪"),
    ])

    # === 5. Garbled phrase fixes ===

    rules.extend([
        ("故宫大人", "布政使大人"),
        ("装绝之上", "桩子之上"),
        ("令亲拿出去", "令旗拿出去"),
        ("请令齐出去", "请令旗出去"),
        ("自帮请罪", "自绑请罪"),
        ("照单儿清且", "照单全收"),
        ("不关打家伙", "不关大伙儿"),
        ("南京中山去", "南京去"),
        ("各一往呢", "搁一旁呢"),
        ("超中第一人", "朝中第一人"),
        ("13511年", "1351年"),
        ("15011年", "1501年"),
        ("发师了", "发傻了"),
        ("下尚书大学士", "内阁尚书大学士"),
        ("征爹的这功劳", "争爹的这功劳"),
        ("体量和稳", "体悟领悟"),
    ])

    # === 6. Format fixes ===

    rules.extend([
        (",,", "，"),
        ("，，", "，"),
    ])

    return rules


def apply_replacements(text, rules):
    result = text
    for wrong, correct in rules:
        if wrong == correct:
            continue
        result = result.replace(wrong, correct)
    return result


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

    print(f"Round 3: Found {total} SRT files. Applying {len(rules)} rules...")
    print()

    for i, filepath in enumerate(srt_files, 1):
        changed = process_srt_file(filepath, rules)
        if changed:
            modified += 1
            basename = os.path.basename(filepath)
            print(f"  [{i:3d}/{total}] MODIFIED: {basename}")

    print()
    print(f"Done! Total: {total}, Modified: {modified}, Unchanged: {total - modified}")


if __name__ == "__main__":
    main()