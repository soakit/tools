#!/usr/bin/env python3
"""Generate spoken-style example sentences for top-frequency words."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from coca_loader import normalize_key as coca_normalize_key

ASSETS = Path(__file__).resolve().parent / "assets"
TOP500_PATH = ASSETS / "_top500_words.json"
OUTPUT_PATH = ASSETS / "examples-top500.json"

# Hand-crafted overrides for function words and words Tatoeba handles poorly.
MANUAL: dict[str, tuple[str, str]] = {
    "be": ("I'm gonna be late.", "我要迟到了。"),
    "say": ("What did you say?", "你说什么？"),
    "not": ("No, I'm not.", "不，我不是。"),
    "or": ("Tea or coffee?", "茶还是咖啡？"),
    "as": ("Do as I say.", "按我说的做。"),
    "go": ("I've gotta go now.", "我得走了。"),
    "get": ("I didn't get it.", "我没听懂。"),
    "make": ("Can you make me a sandwich?", "能给我做个三明治吗？"),
    "do": ("What are you doing?", "你在干嘛？"),
    "have": ("I've got no idea.", "我不知道。"),
    "will": ("I'll call you later.", "待会儿给你打电话。"),
    "would": ("Would you like some tea?", "要来杯茶吗？"),
    "can": ("Can I help you?", "需要帮忙吗？"),
    "could": ("Could you wait a minute?", "能等一下吗？"),
    "should": ("You should go home.", "你该回家了。"),
    "may": ("May I come in?", "我可以进来吗？"),
    "might": ("It might rain later.", "待会儿可能会下雨。"),
    "must": ("You must be tired.", "你一定累了。"),
    "shall": ("Shall we go?", "我们走吧？"),
    "the": ("Close the door, please.", "请把门关上。"),
    "a": ("I need a pen.", "我需要一支笔。"),
    "an": ("That's an apple.", "那是个苹果。"),
    "to": ("Nice to meet you.", "很高兴认识你。"),
    "of": ("A cup of tea, please.", "请来杯茶。"),
    "in": ("I'm in the kitchen.", "我在厨房。"),
    "on": ("It's on the table.", "在桌子上。"),
    "at": ("See you at school.", "学校见。"),
    "for": ("This is for you.", "这是给你的。"),
    "with": ("Come with me.", "跟我来。"),
    "by": ("I'll be there by five.", "五点前到。"),
    "from": ("Where are you from?", "你哪儿来的？"),
    "about": ("What are you talking about?", "你在说什么？"),
    "but": ("I tried, but I failed.", "我试了，但失败了。"),
    "if": ("Let me know if you need help.", "需要帮助告诉我。"),
    "so": ("I'm tired, so I'm going to bed.", "我累了，要睡了。"),
    "than": ("She's taller than me.", "她比我高。"),
    "that": ("That's a good idea.", "这主意不错。"),
    "this": ("What's this?", "这是什么？"),
    "these": ("These are my keys.", "这是我的钥匙。"),
    "those": ("Those look nice.", "那些看起来不错。"),
    "there": ("There's no way.", "不可能。"),
    "here": ("Come here.", "过来。"),
    "where": ("Where are you?", "你在哪？"),
    "when": ("When did you get here?", "你什么时候到的？"),
    "why": ("Why not?", "为什么不呢？"),
    "how": ("How are you doing?", "最近怎么样？"),
    "what": ("What's up?", "怎么了？"),
    "who": ("Who's there?", "谁啊？"),
    "which": ("Which one do you want?", "你要哪个？"),
    "all": ("That's all for now.", "就这些。"),
    "no": ("No way!", "不可能！"),
    "yes": ("Yes, please.", "好的，谢谢。"),
    "very": ("Thanks very much.", "非常感谢。"),
    "too": ("Me too.", "我也是。"),
    "also": ("I like it too.", "我也喜欢。"),
    "just": ("Just a minute.", "等一下。"),
    "only": ("Only one left.", "只剩一个了。"),
    "even": ("Even I know that.", "连我都知道。"),
    "well": ("Well, I don't know.", "嗯，我不知道。"),
    "now": ("Do it now.", "现在就做。"),
    "then": ("See you then.", "到时候见。"),
    "still": ("I'm still waiting.", "我还在等。"),
    "already": ("I'm already here.", "我已经到了。"),
    "always": ("She always smiles.", "她总是笑。"),
    "never": ("I never said that.", "我从没说过。"),
    "ever": ("Have you ever been there?", "你去过那儿吗？"),
    "again": ("Say that again.", "再说一遍。"),
    "more": ("I need more time.", "我需要更多时间。"),
    "most": ("Most people agree.", "大多数人都同意。"),
    "much": ("Thanks so much.", "太谢谢了。"),
    "many": ("How many do you need?", "你需要多少？"),
    "some": ("Want some water?", "要喝点水吗？"),
    "any": ("Any questions?", "有问题吗？"),
    "each": ("Each one is different.", "每个都不一样。"),
    "both": ("I like both.", "两个我都喜欢。"),
    "other": ("What about the other one?", "另一个呢？"),
    "another": ("Can I have another?", "能再来一个吗？"),
    "such": ("I've never seen such a thing.", "我从没见过这种事。"),
    "own": ("On my own.", "我自己来。"),
    "same": ("Same here.", "我也是。"),
    "different": ("That's different.", "那不一样。"),
    "like": ("I like your shirt.", "我喜欢你的衬衫。"),
    "know": ("I don't know.", "我不知道。"),
    "think": ("I think so.", "我觉得是。"),
    "see": ("See you tomorrow.", "明天见。"),
    "look": ("Look at this.", "看这个。"),
    "want": ("I want to go home.", "我想回家。"),
    "need": ("I need your help.", "我需要你帮忙。"),
    "use": ("Can I use your phone?", "能用一下你的手机吗？"),
    "try": ("Just try it.", "试试看。"),
    "tell": ("Tell me the truth.", "跟我说实话。"),
    "ask": ("Don't be afraid to ask.", "别害怕问。"),
    "give": ("Give me a hand.", "帮把手。"),
    "take": ("Take your time.", "慢慢来。"),
    "come": ("Come on in.", "进来吧。"),
    "leave": ("I've gotta leave.", "我得走了。"),
    "put": ("Put it here.", "放这儿。"),
    "keep": ("Keep it.", "留着吧。"),
    "let": ("Let me think.", "让我想想。"),
    "mean": ("What do you mean?", "什么意思？"),
    "feel": ("I feel great.", "我感觉很好。"),
    "seem": ("You seem tired.", "你看起来累了。"),
    "become": ("It's getting dark.", "天黑了。"),
    "find": ("I can't find my keys.", "我找不到钥匙。"),
    "call": ("Call me tonight.", "今晚给我打电话。"),
    "work": ("Does this work?", "这行吗？"),
    "help": ("Can you help me?", "能帮我吗？"),
    "play": ("Wanna play?", "想玩吗？"),
    "run": ("I run every morning.", "我每天早上跑步。"),
    "move": ("Don't move.", "别动。"),
    "live": ("Where do you live?", "你住哪？"),
    "believe": ("I can't believe it.", "我不敢相信。"),
    "bring": ("Bring your friend.", "把你朋友带来。"),
    "happen": ("What happened?", "怎么了？"),
    "write": ("Write it down.", "写下来。"),
    "provide": ("Can you provide more info?", "能提供更多信息吗？"),
    "sit": ("Have a seat.", "请坐。"),
    "stand": ("Stand up, please.", "请站起来。"),
    "lose": ("I lost my wallet.", "我钱包丢了。"),
    "pay": ("I'll pay.", "我来付。"),
    "meet": ("Nice to meet you.", "很高兴认识你。"),
    "include": ("Does it include tax?", "含税吗？"),
    "continue": ("Please continue.", "请继续。"),
    "set": ("Set the table.", "摆好桌子。"),
    "learn": ("I'm still learning.", "我还在学。"),
    "change": ("Things change.", "事情会变。"),
    "lead": ("You lead the way.", "你带路。"),
    "understand": ("I don't understand.", "我不明白。"),
    "watch": ("Watch out!", "小心！"),
    "follow": ("Follow me.", "跟我来。"),
    "stop": ("Stop it.", "别闹了。"),
    "create": ("Let's create something new.", "咱们弄点新东西吧。"),
    "speak": ("Do you speak English?", "你会说英语吗？"),
    "read": ("I love reading.", "我喜欢阅读。"),
    "spend": ("Don't spend too much.", "别花太多。"),
    "grow": ("Kids grow so fast.", "孩子长得真快。"),
    "open": ("Open the window.", "把窗户打开。"),
    "walk": ("Let's go for a walk.", "去散个步吧。"),
    "win": ("We won!", "我们赢了！"),
    "offer": ("Can I offer you a drink?", "请你喝一杯？"),
    "remember": ("Remember to call me.", "记得给我打电话。"),
    "love": ("I love this song.", "我爱这首歌。"),
    "consider": ("I'll consider it.", "我考虑一下。"),
    "appear": ("He didn't appear.", "他没出现。"),
    "buy": ("I wanna buy this.", "我想买这个。"),
    "wait": ("Wait for me!", "等等我！"),
    "serve": ("How can I serve you?", "有什么能帮您？"),
    "die": ("Plants die without water.", "植物没水会死。"),
    "send": ("Send me a message.", "给我发条消息。"),
    "expect": ("I didn't expect that.", "我没想到。"),
    "build": ("They're building a new mall.", "他们在建新商场。"),
    "stay": ("Stay here.", "待在这儿。"),
    "fall": ("Be careful — don't fall!", "小心，别摔了！"),
    "cut": ("Cut it in half.", "切成两半。"),
    "reach": ("We finally reached home.", "我们终于到家了。"),
    "kill": ("Smoking kills.", "吸烟有害健康。"),
    "remain": ("Please remain seated.", "请坐好。"),
    "suggest": ("I suggest we leave early.", "我建议早点走。"),
    "raise": ("Raise your hand.", "举手。"),
    "pass": ("Pass me the salt.", "把盐递给我。"),
    "sell": ("They're selling it cheap.", "卖得很便宜。"),
    "require": ("What do you require?", "您需要什么？"),
    "report": ("I gotta report to work.", "我得去上班了。"),
    "decide": ("You decide.", "你决定吧。"),
    "pull": ("Pull the door.", "拉门。"),
    "return": ("When will you return?", "你什么时候回来？"),
    "explain": ("Can you explain that?", "能解释一下吗？"),
    "hope": ("I hope so.", "希望如此。"),
    "develop": ("Things are developing fast.", "事情发展很快。"),
    "carry": ("Can you carry this?", "能帮我拿一下吗？"),
    "break": ("Don't break it.", "别弄坏了。"),
    "receive": ("Did you receive my text?", "收到我短信了吗？"),
    "agree": ("I agree with you.", "我同意你的看法。"),
    "support": ("I'll support you.", "我会支持你的。"),
    "hit": ("Don't hit me.", "别打我。"),
    "produce": ("This factory produces cars.", "这家工厂生产汽车。"),
    "eat": ("Let's eat.", "吃饭吧。"),
    "cover": ("Cover your mouth.", "捂住嘴。"),
    "catch": ("Catch the ball!", "接住球！"),
    "draw": ("Draw a picture.", "画幅画。"),
    "choose": ("You choose.", "你来选。"),
    "cause": ("What caused the problem?", "什么问题引起的？"),
    "point": ("Point at it.", "指着它。"),
    "listen": ("Listen to me.", "听我说。"),
    "plan": ("What's the plan?", "什么计划？"),
    "pick": ("Pick one.", "选一个。"),
    "save": ("Save me a seat.", "给我留个座。"),
    "add": ("Add some sugar.", "加点糖。"),
    "allow": ("Smoking is not allowed.", "禁止吸烟。"),
    "drop": ("Drop it.", "放下。"),
    "push": ("Push the button.", "按按钮。"),
    "close": ("Close your eyes.", "闭上眼睛。"),
    "join": ("Wanna join us?", "要一起吗？"),
    "reduce": ("We need to reduce costs.", "得降低成本。"),
    "establish": ("They established a new rule.", "他们定了新规矩。"),
    "concern": ("Don't worry about it.", "别担心。"),
    "their": ("It's their problem.", "那是他们的问题。"),
    "year": ("Happy New Year!", "新年快乐！"),
    "them": ("I know them.", "我认识他们。"),
    "people": ("Lots of people came.", "来了很多人。"),
    "into": ("Come on in.", "进来吧。"),
    "him": ("I told him.", "我告诉他了。"),
    "its": ("The cat licked its paw.", "猫舔了舔爪子。"),
    "way": ("Which way?", "哪边？"),
    "because": ("Because I said so.", "因为我这么说的。"),
    "man": ("That man's my dad.", "那是我爸。"),
    "thing": ("What's that thing?", "那是什么东西？"),
    "back": ("I'll be back soon.", "我很快回来。"),
    "good": ("That's good.", "那很好。"),
    "woman": ("Who's that woman?", "那个女人是谁？"),
    "through": ("We're almost through.", "我们快完成了。"),
    "life": ("That's life.", "生活就是这样。"),
    "down": ("Calm down.", "冷静点。"),
    "after": ("See you after class.", "下课后见。"),
    "over": ("It's over.", "结束了。"),
    "last": ("This is the last one.", "这是最后一个。"),
    "state": ("State your name.", "报上名字。"),
    "between": ("Between you and me.", "你知我知。"),
    "high": ("Prices are too high.", "价格太高了。"),
    "really": ("Really?", "真的吗？"),
    "something": ("I need something to eat.", "我得吃点东西。"),
    "old": ("How old are you?", "你多大了？"),
    "while": ("Wait a while.", "等一会儿。"),
    "group": ("We're in the same group.", "我们一组。"),
    "begin": ("Let's begin.", "开始吧。"),
    "country": ("Which country are you from?", "你来自哪个国家？"),
    "turn": ("Your turn.", "轮到你了。"),
    "every": ("Every day.", "每天。"),
    "start": ("Ready, start!", "预备，开始！"),
    "hand": ("Give me a hand.", "帮把手。"),
    "part": ("That's part of the plan.", "那是计划的一部分。"),
    "place": ("This is a nice place.", "这地方不错。"),
    "few": ("Just a few.", "就几个。"),
    "week": ("See you next week.", "下周见。"),
    "company": ("Keep me company.", "陪陪我。"),
    "right": ("You're right.", "你说得对。"),
    "question": ("Any questions?", "有问题吗？"),
    "number": ("What's your number?", "你号码多少？"),
    "off": ("Take it off.", "把它脱掉。"),
    "hold": ("Hold on.", "等一下。"),
    "next": ("Who's next?", "下一个是谁？"),
    "without": ("I can't live without you.", "我不能没有你。"),
    "before": ("I've been here before.", "我来过这儿。"),
    "large": ("Extra large, please.", "请加大号。"),
    "home": ("I'm going home.", "我回家了。"),
    "under": ("Under the table.", "在桌子下面。"),
    "water": ("Can I get some water?", "能给我点水吗？"),
    "money": ("I don't have enough money.", "钱不够。"),
    "story": ("Tell me a story.", "给我讲个故事。"),
    "young": ("When I was young.", "我年轻的时候。"),
    "month": ("See you next month.", "下个月见。"),
    "book": ("I booked a table.", "我订了位。"),
    "job": ("Good job!", "干得好！"),
    "word": ("In other words.", "换句话说。"),
    "though": ("Even though.", "即使如此。"),
    "business": ("None of your business.", "不关你事。"),
    "side": ("Side by side.", "肩并肩。"),
    "far": ("So far, so good.", "目前还不错。"),
    "little": ("Just a little.", "就一点点。"),
    "house": ("Welcome to my house.", "欢迎来我家。"),
    "friend": ("You're my best friend.", "你是我最好的朋友。"),
    "important": ("That's important.", "这很重要。"),
    "away": ("Go away.", "走开。"),
    "power": ("The power's out.", "停电了。"),
    "hour": ("An hour ago.", "一小时前。"),
    "game": ("Good game!", "好球！"),
    "often": ("How often?", "多经常？"),
    "yet": ("Not yet.", "还没有。"),
    "end": ("At the end of the day.", "到头来。"),
    "however": ("However you like.", "随你怎么。"),
    "car": ("Nice car.", "好车。"),
    "city": ("I love this city.", "我爱这座城市。"),
    "almost": ("Almost there.", "快到了。"),
    "real": ("For real?", "真的假的？"),
    "team": ("Our team won.", "我们队赢了。"),
    "minute": ("Wait a minute.", "等一下。"),
    "idea": ("Good idea!", "好主意！"),
    "kid": ("When I was a kid.", "我小时候。"),
    "body": ("Mind and body.", "身心。"),
    "nothing": ("Nothing much.", "没什么。"),
    "ago": ("Long time ago.", "很久以前。"),
    "parent": ("My parents are coming.", "我父母要来。"),
    "sure": ("Are you sure?", "你确定吗？"),
    "oh": ("Oh, I see.", "哦，我明白了。"),
    "phone": ("I'll phone you.", "我给你打电话。"),
    "easy": ("Take it easy.", "放轻松。"),
    "baby": ("Don't be a baby.", "别撒娇了。"),
    "wrong": ("Something's wrong.", "出问题了。"),
    "fire": ("There's a fire!", "着火了！"),
    "future": ("In the near future.", "在不久的将来。"),
    "deal": ("It's a deal.", "成交。"),
    "bed": ("Time for bed.", "该睡了。"),
    "enter": ("Don't enter.", "别进来。"),
    "common": ("That's common sense.", "那是常识。"),
    "poor": ("Poor thing.", "可怜的人。"),
    "natural": ("That's natural.", "那很自然。"),
    "race": ("It's a race against time.", "和时间赛跑。"),
}

TATOEBA_URL = "https://tatoeba.org/en/api_v0/search?from=eng&to=cmn&orphans=no&sort=relevance&limit=10&query="

FORMAL_MARKERS = re.compile(
    r"\b(however|therefore|moreover|nevertheless|furthermore|consequently|"
    r"whereas|notwithstanding|accordingly)\b",
    re.I,
)
COLLOQUIAL_MARKERS = re.compile(
    r"\b(gonna|wanna|gotta|kinda|sorta|yeah|nope|okay|ok|hey|hi|thanks|please)\b|'|\?",
    re.I,
)


def base_word(word: str) -> str:
    w = word.strip()
    w = re.sub(r"\s*\([^)]*\)", "", w)
    w = re.sub(r"\s*=.*$", "", w)
    w = re.sub(r"\s+modal\s*$", "", w, flags=re.I)
    return coca_normalize_key(w)


def split_meanings(definition: str) -> list[str]:
    text = re.sub(r"^(n\.|v\.|adj\.|adv\.|prep\.|conj\.|art\.|pron\.|num\.|int\.|abbr\.)\s*", "", definition)
    parts = re.split(r"[;；,，]", text)
    return [p.strip() for p in parts if p.strip()]


def chinese_only(text: str) -> str:
    text = re.sub(r"[a-zA-Z]+", "", text)
    text = re.sub(r"\s+", "", text)
    return text.strip(" ;；,，/·")


def fallback_example(base: str, definition: str, coca_meanings: list[str]) -> tuple[str, str]:
    zh = chinese_only(coca_meanings[0] if coca_meanings else split_meanings(definition)[0] if split_meanings(definition) else "……")
    if "n." in definition or any("n." in m for m in coca_meanings):
        return f"I like this {base}.", f"我喜欢这个{zh}。"
    if "adj." in definition or any("adj." in m for m in coca_meanings):
        return f"That's pretty {base}.", f"那挺{zh}的。"
    if "adv." in definition:
        return f"She said it {base}.", f"她{zh}地说了。"
    if "prep." in definition or "conj." in definition:
        return f"Just like {base} this.", f"就像这样{zh}。"
    return f"Let's {base}.", f"咱们{zh}吧。"


def score_sentence(sentence: str, base: str) -> int:
    words = sentence.split()
    n = len(words)
    if n < 3 or n > 14:
        return -100
    if not re.search(rf"\b{re.escape(base)}\b", sentence, re.I):
        return -100
    if FORMAL_MARKERS.search(sentence):
        return -50
    if re.search(r"[0-9]", sentence):
        return -20

    score = 20
    if 5 <= n <= 10:
        score += 15
    if COLLOQUIAL_MARKERS.search(sentence):
        score += 10
    if sentence.endswith(("?", "!")):
        score += 5
    if "'" in sentence:
        score += 5
    if sentence[0].isupper() and not sentence.isupper():
        score += 3
    if len(sentence) > 80:
        score -= 15
    return score


def fetch_tatoeba(base: str) -> list[tuple[str, str]]:
    url = TATOEBA_URL + urllib.parse.quote(base)
    req = urllib.request.Request(url, headers={"User-Agent": "words-tool/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())

    results: list[tuple[str, str, int]] = []
    for item in data.get("results", []):
        en = item.get("text", "").strip()
        if not en:
            continue
        zh = ""
        for group in item.get("translations", []):
            for tr in group:
                if tr.get("lang") in ("cmn", "cmn-Hans", "zh"):
                    zh = tr.get("text", "").strip()
                    break
            if zh:
                break
        if not zh:
            continue
        s = score_sentence(en, base)
        if s > 0:
            results.append((en, zh, s))

    results.sort(key=lambda x: -x[2])
    return [(en, zh) for en, zh, _ in results]


def pick_example(item: dict, tatoeba_cache: dict[str, list[tuple[str, str]]] | None = None) -> tuple[str, str, str]:
    base = base_word(item["word"])
    if base in MANUAL:
        en, zh = MANUAL[base]
        return en, zh, "manual"

    candidates = (tatoeba_cache or {}).get(base)
    if candidates is None:
        try:
            candidates = fetch_tatoeba(base)
        except Exception:
            candidates = []
    if candidates:
        return candidates[0][0], candidates[0][1], "tatoeba"

    return "", "", "skipped"


def fetch_tatoeba_batch(bases: list[str], workers: int = 8) -> dict[str, list[tuple[str, str]]]:
    cache: dict[str, list[tuple[str, str]]] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_tatoeba, b): b for b in bases}
        for fut in as_completed(futures):
            base = futures[fut]
            try:
                cache[base] = fut.result()
            except Exception:
                cache[base] = []
    return cache


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate example sentences for top-500 words")
    parser.add_argument("--input", type=Path, default=TOP500_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.0, help="Unused; kept for compatibility")
    parser.add_argument("--workers", type=int, default=8, help="Concurrent Tatoeba fetch workers")
    args = parser.parse_args()

    words: list[dict] = json.loads(args.input.read_text(encoding="utf-8"))
    if args.limit:
        words = words[: args.limit]

    tatoeba_bases = sorted({
        base_word(item["word"])
        for item in words
        if base_word(item["word"]) not in MANUAL
    })
    print(f"Fetching Tatoeba for {len(tatoeba_bases)} words ({args.workers} workers)...")
    tatoeba_cache = fetch_tatoeba_batch(tatoeba_bases, workers=args.workers)

    examples: dict[str, dict] = {}
    stats = {"manual": 0, "tatoeba": 0, "skipped": 0}

    for i, item in enumerate(words, 1):
        base = base_word(item["word"])
        en, zh, source = pick_example(item, tatoeba_cache)
        if source == "skipped":
            stats["skipped"] += 1
            print(f"[{i}/{len(words)}] {base:20s} ({source:8s})")
            continue
        examples[base] = {
            "en": en,
            "zh": zh,
            "rank": item["rank"],
            "word": item["word"],
            "source": source,
        }
        stats[source] += 1
        print(f"[{i}/{len(words)}] {base:20s} ({source:8s}) {en}")

    payload = {
        "meta": {
            "total": len(examples),
            "source": "top500-curated",
            "stats": stats,
        },
        "examples": examples,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved {args.output}")
    print(f"  manual: {stats['manual']}, tatoeba: {stats['tatoeba']}, skipped: {stats['skipped']}")


if __name__ == "__main__":
    main()
