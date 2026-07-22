# -*- coding: utf-8 -*-
"""
merge_srts.py v2 - 句级择优, 不再要求整集干净
每段 whisper 独立评估: 是否可借鉴 (无广告/不超长/无标点幻觉/非重复)
"""
import os, re, glob, json
import fix_srt_final as FSF

ROOT = os.path.dirname(os.path.abspath(__file__))
DIR_A = os.path.join(ROOT, "srts")
DIR_B = os.path.join(ROOT, "srts_whisper_large-v3")
DIR_OUT = os.path.join(ROOT, "srts_merged")

TS_RE = re.compile(r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})")
def to_sec(s):
    h,mn,sec = s.replace(",", ".").split(":")
    return int(h)*3600+int(mn)*60+float(sec)
def sec_to_ts(x):
    x = max(0.0, x)
    h = int(x//3600); x-=h*3600
    m = int(x//60); x-=m*60
    s = int(x); ms = int(round((x-s)*1000))
    if ms==1000: ms=0; s+=1
    if s==60: s=0; m+=1
    if m==60: m=0; h+=1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def parse_srt(path):
    with open(path, "r", encoding="utf-8") as f: raw=f.read()
    blocks = re.split(r"\r?\n\r?\n", raw.strip())
    out=[]
    for b in blocks:
        lines=[l for l in b.splitlines() if l.strip()]
        if len(lines)<2: continue
        tidx=next((i for i,l in enumerate(lines) if "-->" in l), None)
        if tidx is None: continue
        m=TS_RE.search(lines[tidx])
        if not m: continue
        try: st=to_sec(m.group(1)); en=to_sec(m.group(2))
        except: continue
        text="".join(lines[tidx+1:]).strip()
        out.append({"start":st,"end":en,"text":text})
    return out

def write_srt(path, entries):
    with open(path,"w",encoding="utf-8") as f:
        for i,e in enumerate(entries,1):
            f.write(f"{i}\n{sec_to_ts(e['start'])} --> {sec_to_ts(e['end'])}\n{e['text']}\n\n")

AD_PATTERNS = ["请不吝点赞","订阅 转发","打赏支持","明镜与点点栏目","感谢您的观看","感谢观看","点赞关注"]
def text_is_ad(t): return any(p in t for p in AD_PATTERNS)

def b_seg_usable(b_entry, prev_b_text=None):
    """单个 whisper 段是否可借鉴"""
    t=b_entry["text"]
    if not t: return False
    if text_is_ad(t): return False
    dur=b_entry["end"]-b_entry["start"]
    if dur>12: return False                       # 太长 (whisper 合并条)
    if len(t)>22 and (t.count("，")+t.count(","))>=2: return False  # 标点幻觉
    if prev_b_text is not None and t==prev_b_text: return False     # 与上一B段相同 (重复幻觉)
    # 疑似标点开头/结尾的碎片
    if t.startswith(("，",",","。","!","？")): return False
    return True

def align(ea, eb):
    i=j=0; pairs=[]
    while i<len(ea) and j<len(eb):
        a=ea[i]; b=eb[j]
        ov=max(0.0, min(a["end"],b["end"])-max(a["start"],b["start"]))
        La=a["end"]-a["start"]; Lb=b["end"]-b["start"]
        L=min(La,Lb) if min(La,Lb)>0 else 1
        if ov/L>=0.5:
            pairs.append((i,j)); i+=1; j+=1
        else:
            if a["start"]<b["start"]: i+=1
            else: j+=1
    return pairs

def norm(t): return re.sub(r"[，,.。！!？?、\s]+","",t)

def pick_text(a_entry, b_entry, b_usable):
    ta=a_entry["text"]; tb=b_entry["text"]
    if not b_usable: return (ta,"A")
    if text_is_ad(ta) and not text_is_ad(tb): return (tb,"B")
    na=norm(ta); nb=norm(tb)
    # Conservative borrow: only when A is empty or near-empty fragment
    # and B is a complete short phrase. This avoids importing whisper's
    # systematic proper-noun errors while still filling genuine gaps.
    if (not na or len(na) <= 2) and 3 <= len(nb) <= 24:
        return (tb,"B")
    if na == nb:
        return (tb,"B")
    return (ta,"A")

def load_rules_from_file(path):
    if not os.path.exists(path): return []
    with open(path,"r",encoding="utf-8") as f: src=f.read()
    pairs=re.findall(r'\(\s*"((?:[^"\\]|\\.)*)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*\)', src)
    out=[]
    for w,c in pairs:
        if "PLACEHOLDER" in w or "PLACEHOLDER" in c: continue
        if w==c: continue
        out.append((w,c))
    return out

def collect_sv_rules():
    return FSF.build_replacements()

def apply_rules(text, rules):
    for w, c in rules:
        if w and w in text:
            text = text.replace(w, c)
    for pat, c in FSF.REGEX_RULES:
        text = pat.sub(c, text)
    return text

def main():
    os.makedirs(DIR_OUT, exist_ok=True)
    fa={os.path.basename(p):p for p in glob.glob(os.path.join(DIR_A,"*.srt"))}
    fb={os.path.basename(p):p for p in glob.glob(os.path.join(DIR_B,"*.srt"))}
    na={n.replace("音频",""):n for n in fa}
    nb={n.replace("音频",""):n for n in fb}
    common=sorted(set(na)&set(nb))
    sv_rules=collect_sv_rules()
    print(f"Loaded {len(sv_rules)} SV rules; files={len(common)}")

    stats={"seg_total":0,"seg_B":0,"seg_A":0,"b_usable":0,"b_unusable":0}
    log=[]
    for k in common:
        ea=parse_srt(fa[na[k]])
        eb=parse_srt(fb[nb[k]]) if k in nb else []
        out=[]
        if eb:
            pairs=align(ea,eb)
            aligned_a={ai for ai,_ in pairs}
            aligned_b={bi for _,bi in pairs}
            # 预计算每个 B 段是否 usable (需要 prev aligned B text)
            bi_list=[bi for _,bi in pairs]
            bi_set=set(bi_list)
            usable_cache={}
            prev_b_text=None
            # 按 B 出现顺序遍历, 判定重复
            for bi in sorted(bi_set):
                t=eb[bi]["text"]
                usable_cache[bi] = (
                    b_seg_usable(eb[bi], prev_b_text) and
                    # 该 B 段是否被多个 A 对齐 (一对多通常是幻觉合并)
                    sum(1 for _,b2 in pairs if b2==bi)<=2
                )
                if usable_cache[bi] and t: prev_b_text=t
            for ai,bi in pairs:
                a=ea[ai]; b=eb[bi]
                u=usable_cache.get(bi, False)
                if u: stats["b_usable"]+=1
                else: stats["b_unusable"]+=1
                text,src=pick_text(a,b,u)
                stats["seg_total"]+=1
                if src=="B":
                    stats["seg_B"]+=1
                    log.append((k,"B",a["text"],b["text"],text))
                else: stats["seg_A"]+=1
                out.append({"start":a["start"],"end":a["end"],"text":text})
            for idx,a in enumerate(ea):
                if idx not in aligned_a:
                    out.append({"start":a["start"],"end":a["end"],"text":a["text"]})
                    stats["seg_A"]+=1; stats["seg_total"]+=1
        else:
            for a in ea:
                out.append({"start":a["start"],"end":a["end"],"text":a["text"]})
            stats["seg_A"]+=len(ea); stats["seg_total"]+=len(ea)

        out.sort(key=lambda e:e["start"])
        for e in out:
            e["text"]=apply_rules(e["text"], sv_rules).strip()
        write_srt(os.path.join(DIR_OUT,k), out)

    print("\n=== STATS ===")
    for kk,vv in stats.items(): print(f"  {kk}: {vv}")
    with open(os.path.join(ROOT,"_merge_borrowed.json"),"w",encoding="utf-8") as f:
        json.dump(log[:3000], f, ensure_ascii=False, indent=1)

if __name__=="__main__":
    main()
