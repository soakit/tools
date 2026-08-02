#!/usr/bin/env python3
"""Generate A4 vocabulary PDF: intro page + dictation page per word batch."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from coca_loader import CocaEntry, CocaIndex, load_index
from collocations_loader import lookup_collocations
from examples_loader import lookup_example
from phonetic_loader import lookup_phonetic

ASSETS = Path(__file__).resolve().parent / "assets"
FONT_CN_PATH = "/System/Library/Fonts/Supplemental/Songti.ttc"
FONT_IPA_PATH = "/Library/Fonts/Arial Unicode.ttf"
FONT_CN = "Songti"
FONT_IPA = "ArialUnicode"
FONT_EN = "ArialUnicode"

PAGE_W, PAGE_H = A4
MARGIN_L = 14 * mm
MARGIN_R = 14 * mm
MARGIN_T = 12 * mm
MARGIN_B = 12 * mm
GUTTER = 5 * mm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R
COL_W = (CONTENT_W - GUTTER) / 2
FRAME_H = PAGE_H - MARGIN_T - MARGIN_B
PAGE_TOP_SPACER = 2 * mm
PACK_SAFETY = 5 * mm
MAX_COL_H = FRAME_H - PAGE_TOP_SPACER - PACK_SAFETY

COLOR_BLACK = colors.HexColor("#000000")
COLOR_INDEX = COLOR_BLACK
COLOR_WORD = COLOR_BLACK
COLOR_PHONETIC = COLOR_BLACK
COLOR_LABEL = COLOR_BLACK
COLOR_TEXT = COLOR_BLACK
COLOR_BLANK = COLOR_BLACK
COLOR_MUTED = COLOR_BLACK
COLOR_DIVIDER = COLOR_BLACK


@dataclass
class WordEntry:
    word: str
    definition: str
    coca_rank: int = 999999
    phonetic: str = ""
    coca_paraphrase: str = ""
    coca_meanings: list[str] = field(default_factory=list)
    base_word: str = ""
    inflection: str = ""
    collocations: list[tuple[str, str]] = field(default_factory=list)
    example_en: str = ""
    example_zh: str = ""
    dictation_zh: list[str] = field(default_factory=list)
    display_num: int = 0

    def finalize(self) -> None:
        self.base_word, self.inflection = split_word_forms(self.word)
        self.collocations = build_collocations(self.base_word, self.definition, self.coca_meanings)
        self.example_en, self.example_zh = build_example(self.base_word, self.definition, self.coca_meanings)
        self.dictation_zh = build_dictation_zh(self.collocations, self.coca_meanings, self.definition)


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont(FONT_CN, FONT_CN_PATH, subfontIndex=0))
    pdfmetrics.registerFont(TTFont(FONT_IPA, FONT_IPA_PATH))


def split_word_forms(word: str) -> tuple[str, str]:
    word = word.strip()
    m = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", word)
    if not m:
        return word, ""
    base = m.group(1).strip()
    forms = m.group(2).strip()
    if re.search(r"pl\.|复数|单数|bacteria", forms, re.I):
        return base, f"复数变化 {forms.replace(', ', '/').replace(',', '/')}"
    if re.search(r"[,/]|ed|en|wn|ought|ore|awn|ent|pt|un", forms, re.I):
        normalized = forms.replace(", ", "/").replace(",", "/")
        return base, f"时态变化 {normalized}"
    return base, forms


def split_meanings(definition: str) -> list[str]:
    text = re.sub(r"^(n\.|v\.|adj\.|adv\.|prep\.|conj\.|art\.|pron\.|num\.|int\.|abbr\.)\s*", "", definition)
    text = re.sub(r"\b(n\.|v\.|adj\.|adv\.|prep\.|art\.|aux\.|vi\.|vt\.)\.?\s*", "", text)
    parts = re.split(r"[;；,，]", text)
    return [p.strip() for p in parts if p.strip()]


def chinese_only(text: str) -> str:
    text = re.sub(r"[a-zA-Z]+", "", text)
    text = re.sub(r"\s+", "", text)
    return text.strip(" ;；,，/·")


def zh_from_meaning(text: str) -> list[str]:
    text = re.sub(r"^[a-z\.&\s]+", "", text, flags=re.I).strip()
    return [p.strip() for p in re.split(r"[;；,，]", text) if p.strip()]


def build_collocations(base: str, definition: str, coca_meanings: list[str]) -> list[tuple[str, str]]:
    curated = lookup_collocations(base, limit=3)
    if curated:
        return curated
    return []


def build_example(base: str, definition: str, coca_meanings: list[str]) -> tuple[str, str]:
    curated = lookup_example(base)
    if curated:
        return curated
    return "", ""


def build_dictation_zh(
    collocations: list[tuple[str, str]], coca_meanings: list[str], definition: str
) -> list[str]:
    items: list[str] = []
    for _, zh in collocations:
        for part in zh_from_meaning(zh):
            if part not in items:
                items.append(part)
    for m in coca_meanings:
        for part in zh_from_meaning(m):
            if part not in items:
                items.append(part)
    if len(items) < 5:
        for m in split_meanings(definition):
            zh = chinese_only(m)
            if zh and zh not in items:
                items.append(zh)
    return items[:6]


def enrich_with_coca(entry: WordEntry, coca: CocaEntry | None) -> None:
    if coca:
        entry.coca_rank = coca.rank
        entry.phonetic = coca.phonetic_uk or coca.phonetic_us
        entry.coca_paraphrase = coca.paraphrase
        entry.coca_meanings = coca.meanings
    if not entry.phonetic:
        entry.phonetic = lookup_phonetic(entry.word)


def translation_text(entry: WordEntry) -> str:
    if entry.coca_paraphrase:
        return entry.coca_paraphrase
    return entry.definition


def load_words(
    path: Path,
    coca_index: CocaIndex,
    limit: int | None = None,
    word_filter: str | None = None,
    start_rank: int = 1,
) -> list[WordEntry]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    entries: list[WordEntry] = []
    for section in data["words_by_letter"]:
        for item in section["words"]:
            entry = WordEntry(word=item["word"], definition=item["definition"])
            enrich_with_coca(entry, coca_index.lookup(entry.word))
            entry.finalize()
            if word_filter:
                if word_filter.lower() in entry.base_word.lower() or word_filter.lower() in entry.word.lower():
                    entries = [entry]
                    assign_display_numbers(entries)
                    return entries
                continue
            entries.append(entry)
        if word_filter and entries:
            break

    entries.sort(key=lambda e: (e.coca_rank, e.base_word.lower()))
    if start_rank > 1:
        entries = [e for e in entries if e.coca_rank >= start_rank]
    if limit:
        entries = entries[:limit]
    assign_display_numbers(entries)
    return entries


def assign_display_numbers(entries: list[WordEntry]) -> None:
    """Use COCA rank when available; otherwise continue from the last number."""
    last = 0
    for entry in entries:
        if entry.coca_rank < 999999:
            last = entry.coca_rank
            entry.display_num = last
        else:
            last += 1
            entry.display_num = last


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["Normal"]
    return {
        "header": ParagraphStyle(
            "header", parent=base, fontName=FONT_CN, fontSize=13,
            textColor=COLOR_WORD, leading=16,
        ),
        "label": ParagraphStyle(
            "label", parent=base, fontName=FONT_CN, fontSize=9.5,
            textColor=COLOR_LABEL, leading=12,
        ),
        "body": ParagraphStyle(
            "body", parent=base, fontName=FONT_CN, fontSize=9,
            textColor=COLOR_TEXT, leading=13, alignment=TA_LEFT,
        ),
        "body_en": ParagraphStyle(
            "body_en", parent=base, fontName=FONT_EN, fontSize=9,
            textColor=COLOR_TEXT, leading=13, alignment=TA_LEFT,
        ),
        "dictation_prompt": ParagraphStyle(
            "dictation_prompt", parent=base, fontName=FONT_CN, fontSize=9,
            textColor=COLOR_TEXT, leading=12,
        ),
        "dictation_title": ParagraphStyle(
            "dictation_title", parent=base, fontName=FONT_CN, fontSize=11,
            textColor=COLOR_MUTED, leading=14,
        ),
        "blank_line": ParagraphStyle(
            "blank_line", parent=base, fontName=FONT_EN, fontSize=9,
            textColor=COLOR_BLANK, leading=24,
        ),
    }


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def word_header_html(entry: WordEntry) -> str:
    word = esc(entry.base_word)
    parts = [
        f'<font name="{FONT_CN}" color="{COLOR_INDEX.hexval()}">{entry.display_num}</font>',
        f'&nbsp;&nbsp;<font name="{FONT_EN}" color="{COLOR_WORD.hexval()}"><b>{word}</b></font>',
    ]
    if entry.phonetic:
        parts.append(
            f'&nbsp;&nbsp;<font name="{FONT_IPA}" color="{COLOR_PHONETIC.hexval()}">[{esc(entry.phonetic)}]</font>'
        )
    return "".join(parts)


def labeled_block(
    label: str, content: str, styles: dict[str, ParagraphStyle], col_width: float, en: bool = False
) -> Table:
    body_style = "body_en" if en else "body"
    label_w = 8 * mm
    table = Table(
        [[Paragraph(label, styles["label"]), Paragraph(content.replace("\n", "<br/>"), styles[body_style])]],
        colWidths=[label_w, col_width - label_w - 2 * mm],
        hAlign="LEFT",
    )
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    return table


def stack_flowables(flowables: list, col_width: float) -> Table:
    if not flowables:
        flowables = [Spacer(1, 1)]
    rows = [[f] for f in flowables]
    table = Table(rows, colWidths=[col_width], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


class TwoColumnPage(Flowable):
    """Side-by-side columns drawn as one atomic block (avoids nested-table page splits)."""

    def __init__(self, left_flow: list, right_flow: list, col_w: float, gutter: float):
        super().__init__()
        self.left_flow = left_flow
        self.right_flow = right_flow
        self.col_w = col_w
        self.gutter = gutter

    def wrap(self, availW: float, availH: float) -> tuple[float, float]:
        lh = measure_block(self.left_flow, self.col_w) if self.left_flow else 0.0
        rh = measure_block(self.right_flow, self.col_w) if self.right_flow else 0.0
        self.width = availW
        self.height = max(lh, rh)
        return self.width, self.height

    def split(self, availW: float, availH: float) -> list:
        return []

    def draw(self) -> None:
        self._draw_column(self.left_flow, 0)
        self._draw_column(self.right_flow, self.col_w + self.gutter)

    def _draw_column(self, flowables: list, x: float) -> None:
        y = self.height
        for item in flowables:
            _, h = item.wrap(self.col_w, self.height)
            y -= h
            item.drawOn(self.canv, x, y)


def build_word_intro_block(entry: WordEntry, styles: dict[str, ParagraphStyle]) -> list:
    flow: list = []
    flow.append(Paragraph(word_header_html(entry), styles["header"]))
    flow.append(Spacer(1, 2 * mm))
    flow.append(labeled_block("译", esc(translation_text(entry)), styles, COL_W))
    flow.append(Spacer(1, 1.5 * mm))

    if entry.inflection:
        flow.append(labeled_block("变", esc(entry.inflection), styles, COL_W))
        flow.append(Spacer(1, 1.5 * mm))

    if entry.collocations:
        col_html = "<br/>".join(f"{esc(en)} {esc(zh)}" for en, zh in entry.collocations[:5])
        flow.append(labeled_block("配", col_html, styles, COL_W, en=True))
        flow.append(Spacer(1, 2 * mm))

    if entry.example_en and entry.example_zh:
        example = f"{esc(entry.example_en)}<br/>{esc(entry.example_zh)}"
        flow.append(labeled_block("例", example, styles, COL_W, en=True))
        flow.append(Spacer(1, 2 * mm))

    flow.append(Spacer(1, 1 * mm))
    return flow


def dictation_blank_line() -> str:
    chars = max(46, int(COL_W / (2.0 * mm)))
    return "_" * chars


def build_word_dictation_block(entry: WordEntry, styles: dict[str, ParagraphStyle]) -> list:
    flow: list = []
    flow.append(Paragraph(
        f'<font name="{FONT_CN}" color="{COLOR_INDEX.hexval()}">#{entry.display_num}</font>',
        styles["dictation_title"],
    ))
    flow.append(Spacer(1, 1.5 * mm))
    blank = dictation_blank_line()
    for i, prompt in enumerate(entry.dictation_zh[:3], 1):
        flow.append(Paragraph(f"{i}. {esc(prompt)}", styles["dictation_prompt"]))
        flow.append(Spacer(1, 1.5 * mm))
        flow.append(Paragraph(blank, styles["blank_line"]))
        flow.append(Spacer(1, 3.5 * mm))
    flow.append(Spacer(1, 3 * mm))
    return flow


def measure_block(flowables: list, width: float) -> float:
    if not flowables:
        return 0.0
    _, height = stack_flowables(flowables, width).wrap(width, FRAME_H)
    return height


def measure_flowables(flowables: list, width: float) -> float:
    return measure_block(flowables, width)


@dataclass
class PageGroup:
    left: list[WordEntry] = field(default_factory=list)
    right: list[WordEntry] = field(default_factory=list)

    @property
    def entries(self) -> list[WordEntry]:
        result: list[WordEntry] = []
        li, ri = 0, 0
        while li < len(self.left) or ri < len(self.right):
            if li < len(self.left):
                result.append(self.left[li])
                li += 1
            if ri < len(self.right):
                result.append(self.right[ri])
                ri += 1
        return result

    def __len__(self) -> int:
        return len(self.left) + len(self.right)


def pack_entry_groups(
    entries: list[WordEntry],
    styles: dict[str, ParagraphStyle],
) -> list[PageGroup]:
    """Pack entries top-to-bottom: fill left column, then right, then new page."""
    groups: list[PageGroup] = []
    current = PageGroup()
    left_h = 0.0
    right_h = 0.0

    def column_height(column: list[WordEntry]) -> float:
        if not column:
            return 0.0
        intro_flow: list = []
        dict_flow: list = []
        for entry in column:
            intro_flow.extend(build_word_intro_block(entry, styles))
            dict_flow.extend(build_word_dictation_block(entry, styles))
        return max(measure_block(intro_flow, COL_W), measure_block(dict_flow, COL_W))

    def flush_page() -> None:
        nonlocal current, left_h, right_h
        if current.left or current.right:
            groups.append(current)
            current = PageGroup()
            left_h = right_h = 0.0

    for entry in entries:
        trial_left = column_height(current.left + [entry])
        if trial_left <= MAX_COL_H:
            current.left.append(entry)
            left_h = trial_left
            continue

        trial_right = column_height(current.right + [entry])
        if trial_right <= MAX_COL_H:
            current.right.append(entry)
            right_h = trial_right
            continue

        flush_page()
        current.left.append(entry)
        left_h = column_height(current.left)

    flush_page()
    return groups


def build_page_for_group(
    group: PageGroup,
    styles: dict[str, ParagraphStyle],
    block_builder,
) -> list:
    left_flow: list = []
    for entry in group.left:
        left_flow.extend(block_builder(entry, styles))
    right_flow: list = []
    for entry in group.right:
        right_flow.extend(block_builder(entry, styles))
    return build_two_column_page(left_flow, right_flow)


def build_two_column_page(left_flow: list, right_flow: list) -> list:
    if not left_flow and not right_flow:
        return []
    return [Spacer(1, PAGE_TOP_SPACER), TwoColumnPage(left_flow, right_flow, COL_W, GUTTER), PageBreak()]


def draw_center_line(canvas, _doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(COLOR_DIVIDER)
    canvas.setLineWidth(0.6)
    x = PAGE_W / 2
    canvas.line(x, MARGIN_B, x, PAGE_H - MARGIN_T)
    canvas.restoreState()


def generate_pdf(entries: list[WordEntry], output_path: Path) -> dict:
    register_fonts()
    styles = make_styles()
    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=MARGIN_L, rightMargin=MARGIN_R,
        topMargin=MARGIN_T, bottomMargin=MARGIN_B,
        title="Vocabulary",
    )

    groups = pack_entry_groups(entries, styles)
    story: list = []
    word_counts: list[int] = []

    for group in groups:
        story.extend(build_page_for_group(group, styles, build_word_intro_block))
        story.extend(build_page_for_group(group, styles, build_word_dictation_block))
        word_counts.append(len(group))

    if story and isinstance(story[-1], PageBreak):
        story.pop()

    doc.build(story, onFirstPage=draw_center_line, onLaterPages=draw_center_line)
    page_pairs = len(groups)
    return {
        "page_pairs": page_pairs,
        "intro_pages": page_pairs,
        "dict_pages": page_pairs,
        "words_per_page": word_counts,
        "total_pages": page_pairs * 2,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate vocabulary PDF sorted by COCA frequency")
    parser.add_argument("--input", type=Path, default=ASSETS / "senior.json")
    parser.add_argument("--output", type=Path, default=ASSETS / "sample-2pages.pdf")
    parser.add_argument("--limit", type=int, default=None, help="Max number of words")
    parser.add_argument("--start-rank", type=int, default=1, help="Start from COCA rank (inclusive)")
    parser.add_argument("--word", type=str, default=None)
    parser.add_argument("--rebuild-coca", action="store_true")
    args = parser.parse_args()

    coca_index = load_index(force_rebuild=args.rebuild_coca)
    entries = load_words(
        args.input, coca_index,
        limit=args.limit, word_filter=args.word, start_rank=args.start_rank,
    )
    if not entries:
        print("没有匹配的词条")
        return

    stats = generate_pdf(entries, args.output)

    matched = sum(1 for e in entries if e.phonetic)
    counts = stats["words_per_page"]
    print(f"已生成: {args.output}")
    print(f"  词条: {len(entries)}  |  页组: {stats['page_pairs']}  |  总页: {stats['total_pages']}（介绍+默写交替）")
    if counts:
        print(f"  每组词数: 最少 {min(counts)}, 最多 {max(counts)}, 平均 {sum(counts)/len(counts):.1f}（左列→右列流式排版）")
    print(f"  COCA 音标匹配: {matched}/{len(entries)}")
    if args.start_rank > 1:
        print(f"  起始词频: #{args.start_rank}")
    e = entries[0]
    print(f"  首词: #{e.display_num} {e.base_word} [{e.phonetic}]")
    if len(entries) > 1:
        e = entries[-1]
        print(f"  末词: #{e.display_num} {e.base_word} [{e.phonetic}]")


if __name__ == "__main__":
    main()
