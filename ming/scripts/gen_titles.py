# -*- coding: utf-8 -*-
"""gen_titles.py - 基于 epub 章节内容, 为 srts_whisper_large-v3/ 的 608 集生成简短标题。
流程: 提取 epub 各章正文 -> 用 5-gram 重叠 + 单调 DP 将每集映射到对应章节 -> 取章节标题(去"第X章"前缀)为该集标题; 同章多集加 (n) 序号。
输出: episode_titles.json  (集号 -> 标题)
用法: python gen_titles.py
"""
import os, re, json, glob, zipfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

def _epub_path():
    for f in os.listdir(ROOT):
        if f.lower().endswith(".epub"):
            return os.path.join(ROOT, f)
    raise FileNotFoundError("未找到 epub 文件")

def extract_chapters():
    z = zipfile.ZipFile(_epub_path())
    chap_files = sorted([n for n in z.namelist() if re.match(r'OPS/chapter\d+\.html', n)],
                        key=lambda s: int(re.search(r'(\d+)', s).group(1)))
    def gettext(html):
        return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html)).strip()
    content = []
    for cf in chap_files:
        txt = gettext(z.read(cf).decode('utf-8', 'ignore'))
        if re.match(r'^[壹贰叁肆伍陆柒]\s', txt):
            continue
        m = re.match(r'((?:前言|引子|后记))', txt)
        if m:
            title = m.group(1); body = txt[len(title):].lstrip()
            if body.startswith(title): body = body[len(title):].lstrip()
            content.append({"filenum": int(re.search(r'(\d+)', cf).group(1)), "title": title, "body": body}); continue
        m = re.match(r'(第[一二三四五六七八九十百零]+章\s+\S+.*?)\s', txt)
        if m:
            title = m.group(1).strip(); idx2 = txt.find(title, len(title))
            body = txt[idx2+len(title):].lstrip() if idx2 != -1 else txt[len(title):].lstrip()
            content.append({"filenum": int(re.search(r'(\d+)', cf).group(1)), "title": title, "body": body})
    return content

def norm(s):
    return re.sub(r'[\s\u3000，。、！？：；()（）【】《》\u201c\u201d\u2018\u2019…—\-_,.!?;:0-9a-zA-Z]+', '', s)

def ngrams(s, n=5):
    s = norm(s)
    if len(s) < n: return {s} if s else set()
    return set(s[i:i+n] for i in range(len(s)-n+1))

def map_episodes(chaps, srt_dir):
    chap_list, gram_index = [], {}
    for ci, c in enumerate(chaps):
        for g in ngrams(c["body"], 5): gram_index.setdefault(g, []).append(ci)
        chap_list.append(c)
    def parse_srt(path):
        out = []
        for b in re.split(r"\r?\n\r?\n", open(path, encoding="utf-8").read().strip()):
            ls = [l for l in b.splitlines() if l.strip()]
            ti = next((i for i, l in enumerate(ls) if "-->" in l), None)
            if ti is None: continue
            out.append("".join(ls[ti+1:]))
        return "".join(out)
    files = sorted(glob.glob(os.path.join(srt_dir, "*.srt")),
                   key=lambda p: int(re.search(r'(\d+)', os.path.basename(p)).group(1)))
    NC = len(chap_list); results = []
    for p in files:
        ep = int(re.search(r'(\d+)', os.path.basename(p)).group(1))
        tg = ngrams(parse_srt(p), 5)
        votes = defaultdict(int)
        for g in tg:
            for ci in gram_index.get(g, ()): votes[ci] += 1
        L = len(tg) or 1
        results.append((ep, [votes.get(ci, 0)/L for ci in range(NC)]))
    INF = float('-inf')
    dp = list(results[0][1]); choices = []
    for ei in range(1, len(results)):
        prev = dp; dp = [INF]*NC; bp = [0]*NC; runmax = INF; runci = 0
        for ci in range(NC):
            if prev[ci] > runmax: runmax = prev[ci]; runci = ci
            dp[ci] = results[ei][1][ci] + runmax; bp[ci] = runci
        choices.append(bp)
    end = max(range(NC), key=lambda ci: dp[ci]); chosen = [0]*len(results); ci = end
    for ei in range(len(results)-1, -1, -1):
        chosen[ei] = ci
        if ei > 0: ci = choices[ei-1][ci]
    return [{"ep": results[ei][0], "filenum": chap_list[chosen[ei]]["filenum"],
             "title": chap_list[chosen[ei]]["title"]} for ei in range(len(results))]

def main():
    chaps = extract_chapters()
    mapping = map_episodes(chaps, os.path.join(ROOT, "srts_whisper_large-v3"))
    def shorten(t):
        mm = re.match(r'第[一二三四五六七八九十百零]+章\s*(.*)', t)
        return (mm.group(1).strip().rstrip('！？!?.。') or t) if mm else t
    groups = defaultdict(list)
    for x in mapping: groups[x["title"]].append(x)
    titles = {}
    for full, lst in groups.items():
        lst.sort(key=lambda z: z["ep"]); total = len(lst)
        for idx, x in enumerate(lst, 1):
            s = re.sub(r'[，。！？、：；\u201c\u201d\u2018\u2019（）【】《》…—,\.!?;:\s\\/:*?"<>|]', '', shorten(x["title"]))
            # 同章多集: 仅加序号 (n), 不带斜杠/总数
            titles[x["ep"]] = f"{s}({idx})" if total > 1 else s
    out = [{"ep": e, "title": titles[e]} for e in sorted(titles)]
    json.dump(out, open(os.path.join(DATA, "episode_titles.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Generated {len(out)} titles -> episode_titles.json")

if __name__ == "__main__":
    main()
