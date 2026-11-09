"""生成站内示意图（SVG）和社交分享卡片（PNG），简体、繁体、日语各一份。

用法（在仓库根目录）：
    python scripts/make_figures.py

依赖：Flask、opencc-python-reimplemented（同 requirements.txt），外加 Pillow（只在本脚本里用，线上不需要）。
分享卡片的字体用 Noto Sans SC（SIL OFL 授权），默认在 C:/Windows/Fonts 里找，也可以用环境变量 CALMY_FONT 指定路径。

输出：
    static/img/<name>.svg、<name>.hant.svg、<name>.ja.svg —— 页面里用 <img> 引用的示意图
    static/og/<key>.png、<key>.hant.png、<key>.ja.png      —— og:image 分享卡片（1200×630）
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import BMI_STANDARDS, BODYFAT_BANDS, BODYFAT_COLORS, TOOLS, band_color  # noqa: E402
from articles import ARTICLES, HANT_OVERRIDES  # noqa: E402
from i18n_hant import to_hant_text  # noqa: E402
from i18n_ja import JA_TOOLS  # noqa: E402
from articles_ja import JA_ARTICLES  # noqa: E402

IMG_DIR = ROOT / "static" / "img"
OG_DIR = ROOT / "static" / "og"

FONT_HANS = "'PingFang SC','Microsoft YaHei','Noto Sans SC','Noto Sans CJK SC',sans-serif"
FONT_HANT = "'PingFang TC','Microsoft JhengHei','Noto Sans TC','Noto Sans CJK TC',sans-serif"
FONT_JA = "'Hiragino Sans','Hiragino Kaku Gothic ProN','Noto Sans JP','Yu Gothic','Meiryo',sans-serif"
LANGS = ("hans", "hant", "ja")

# 日语版图片里的文字（键为简体原文）。没有登记的文字原样输出，例如本来就是日语的 BMI 分级名称。
JA_FIG = {
    "肋骨下缘": "肋骨の下端",
    "髂嵴（髋骨最高点）": "腸骨の上端（腰骨）",
    "中点": "中間",
    "颈围": "首囲",
    "喉结下方，软尺略向前下方倾斜": "のどぼとけの下、やや前下がりに",
    "腰围（WHO 标准位置）": "ウエスト（WHO の位置）",
    "肋骨下缘与髂嵴连线的中点": "肋骨の下端と腸骨の上端の中間",
    "自然站立，呼气结束时读数，不要收腹": "立って力を抜き、息を吐き終えて測る",
    "肚脐水平": "おへその高さ",
    "美国海军体脂公式：男性腰围在此测量": "メタボ健診の腹囲・米海軍式（男性）",
    "臀围": "ヒップ",
    "臀部最突出处，软尺保持水平": "お尻のいちばん出ているところを水平に",
    "围度测量位置": "周囲径の測り方",
    "颈围 · 腰围 · 臀围怎么量": "首囲・ウエスト・ヒップの位置",
    "软尺贴合皮肤但不勒紧，": "メジャーは肌に沿わせ、締めつけない。",
    "每次固定同一位置、同一时间测量。": "毎回同じ位置・同じ時間帯に測る。",
    "围度测量位置：颈围、腰围、臀围怎么量": "周囲径の測り方：首囲・ウエスト・ヒップ",
    "人体正面示意图，标出颈围、腰围（肋骨下缘与髂嵴连线中点）、肚脐水平和臀围的测量位置。":
        "体の正面図に、首囲、ウエスト（肋骨の下端と腸骨の上端の中間）、おへその高さ、ヒップの測る位置を示した図。",
    "BMI 身高体重对照表": "BMI早見表",
    "身高": "身長",
    "BMI = 体重（kg）÷ 身高（m）²。区间含下限、不含上限；仅适用于成人。": "BMI＝体重（kg）÷ 身長（m）²。各区分は下限を含み、上限を含みません。成人が対象です。",
    "男女体脂率参考范围": "男女別・体脂肪率の目安",
    "美国运动委员会（ACE）分级 · 单位：体脂率 %": "米国運動協議会（ACE）の区分・単位：体脂肪率 %",
    "必需脂肪": "必須脂肪",
    "运动员": "アスリート",
    "健身良好": "引き締まり",
    "一般水平": "標準",
    "偏高": "高め",
    "低于必需脂肪的水平不宜长期维持；同一体重下，年龄越大体脂率通常越高。": "必須脂肪を下回る状態を長く続けるのは避けましょう。同じ体重でも、年齢が上がると体脂肪率は高めになりがちです。",
    "男女体脂率参考范围（ACE 分级）": "男女別・体脂肪率の目安（ACEの区分）",
    "男性和女性体脂率分级条形图：必需脂肪、运动员、健身良好、一般水平、偏高。": "男性と女性の体脂肪率の区分を示した帯グラフ：必須脂肪、アスリート、引き締まり、標準、高め。",
}
INK = "#1f2937"
SOFT = "#6b7280"
LINE = "#e5e7eb"
BRAND = "#198754"


def t(text: str, lang: str) -> str:
    if lang == "hant":
        return to_hant_text(text)
    if lang == "ja":
        return JA_FIG.get(text, text)
    return text


def svg_doc(w: int, h: int, body: list[str], lang: str, title: str, desc: str) -> str:
    font = {"hans": FONT_HANS, "hant": FONT_HANT, "ja": FONT_JA}[lang]
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'font-family="{font}" role="img">',
        f"<title>{escape(t(title, lang))}</title>",
        f"<desc>{escape(t(desc, lang))}</desc>",
        f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
        *body,
        f'<text x="{w - 16}" y="{h - 14}" text-anchor="end" font-size="12" fill="#9ca3af">calmyhealth.com</text>',
        "</svg>",
        "",
    ])


def text(x, y, s, lang, size=14, fill=INK, anchor="start", weight="normal") -> str:
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}">{escape(t(s, lang))}</text>')


# ---------------------------------------------------------------------------
# 1. 围度测量位置（颈围 / 腰围 / 臀围）
# ---------------------------------------------------------------------------
def fig_body_measurement(lang: str) -> str:
    cx = 230
    b: list[str] = []
    skin, edge = "#f3e3d3", "#c9a98a"
    # 手臂（画在躯干后面）
    for sx in (-1, 1):
        x0, x1 = cx + sx * 82, cx + sx * 118
        b.append(f'<path d="M {x0} 170 Q {x1} 270 {cx + sx * 122} 400" stroke="{edge}" stroke-width="32" '
                 f'stroke-linecap="round" fill="none"/>')
        b.append(f'<path d="M {x0} 170 Q {x1} 270 {cx + sx * 122} 400" stroke="{skin}" stroke-width="28" '
                 f'stroke-linecap="round" fill="none"/>')

    def mx(x):  # 以中线镜像
        return 2 * cx - x

    d = (f"M 212 132 Q 212 150 150 158 Q 128 164 140 205 Q 166 252 183 300 "
         f"Q 158 342 160 385 Q 162 440 175 525 L 222 525 L 230 452 L 238 525 "
         f"L {mx(175)} 525 Q {mx(162)} 440 {mx(160)} 385 Q {mx(158)} 342 {mx(183)} 300 "
         f"Q {mx(166)} 252 {mx(140)} 205 Q {mx(128)} 164 {mx(150)} 158 Q {mx(212)} 150 {mx(212)} 132 Z")
    b.append(f'<path d="{d}" fill="{skin}" stroke="{edge}" stroke-width="2"/>')
    b.append(f'<rect x="212" y="100" width="36" height="40" fill="{skin}"/>')
    b.append(f'<line x1="212" y1="104" x2="212" y2="134" stroke="{edge}" stroke-width="2"/>')
    b.append(f'<line x1="248" y1="104" x2="248" y2="134" stroke="{edge}" stroke-width="2"/>')
    b.append(f'<ellipse cx="{cx}" cy="64" rx="38" ry="46" fill="{skin}" stroke="{edge}" stroke-width="2"/>')
    # 肚脐
    b.append(f'<circle cx="{cx}" cy="318" r="3" fill="{edge}"/>')

    # 骨性标志：肋骨下缘、髂嵴
    for y, label in ((268, "肋骨下缘"), (330, "髂嵴（髋骨最高点）")):
        b.append(f'<line x1="150" y1="{y}" x2="200" y2="{y}" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="3 3"/>')
        b.append(text(146, y + 5, label, lang, 13, SOFT, "end"))
    b.append(f'<path d="M 156 272 L 156 326" stroke="#94a3b8" stroke-width="1.5" fill="none"/>')
    b.append(text(146, 304, "中点", lang, 13, SOFT, "end"))

    tapes = [
        # (y, 半宽, 颜色, 标签y, 标题, 说明行)
        (121, 22, "#2563eb", 104, "颈围", ["喉结下方，软尺略向前下方倾斜"]),
        (299, 52, "#dc2626", 238, "腰围（WHO 标准位置）", ["肋骨下缘与髂嵴连线的中点", "自然站立，呼气结束时读数，不要收腹"]),
        (318, 50, "#f59e0b", 330, "肚脐水平", ["美国海军体脂公式：男性腰围在此测量"]),
        (385, 74, "#7c3aed", 422, "臀围", ["臀部最突出处，软尺保持水平"]),
    ]
    for y, hw, color, ly, title, lines in tapes:
        dash = ' stroke-dasharray="6 4"' if color == "#f59e0b" else ""
        b.append(f'<ellipse cx="{cx}" cy="{y}" rx="{hw + 4}" ry="7" fill="none" stroke="{color}" stroke-width="3"{dash}/>')
        x_start = cx + hw + 6
        b.append(f'<path d="M {x_start} {y} L 380 {y} L 400 {ly - 5}" stroke="{color}" stroke-width="1.5" fill="none"/>')
        b.append(f'<circle cx="{x_start}" cy="{y}" r="3.5" fill="{color}"/>')
        b.append(text(410, ly, title, lang, 17, color, weight="bold"))
        for i, line in enumerate(lines):
            b.append(text(410, ly + 22 + i * 20, line, lang, 14, INK))

    b.append(text(410, 44, "围度测量位置", lang, 24, INK, weight="bold"))
    b.append(text(410, 70, "颈围 · 腰围 · 臀围怎么量", lang, 15, SOFT))
    b.append(text(410, 496, "软尺贴合皮肤但不勒紧，", lang, 13, SOFT))
    b.append(text(410, 516, "每次固定同一位置、同一时间测量。", lang, 13, SOFT))
    return svg_doc(720, 560, b, lang, "围度测量位置：颈围、腰围、臀围怎么量",
                   "人体正面示意图，标出颈围、腰围（肋骨下缘与髂嵴连线中点）、肚脐水平和臀围的测量位置。")


# ---------------------------------------------------------------------------
# 2. BMI 身高体重对照表（简体：中国标准；繁体：台湾国健署标准）
# ---------------------------------------------------------------------------
def fig_bmi_chart(lang: str) -> str:
    std = BMI_STANDARDS[{"hans": "cn", "hant": "tw", "ja": "jp"}[lang]]
    heights = list(range(150, 191, 5))
    weights = list(range(40, 116, 5))
    x0, y0, cw, ch = 86, 112, 42, 34
    w = x0 + cw * len(weights) + 24
    h = y0 + ch * len(heights) + 110
    b: list[str] = []
    title = "BMI 身高体重对照表"
    b.append(text(24, 40, title, lang, 24, INK, weight="bold"))
    sub = (f"{std['name']}で色分け・マス内の数字がBMI" if lang == "ja" else f"按{std['name']}着色 · 格内数字为 BMI")
    b.append(text(24, 66, sub, lang, 14, SOFT))
    b.append(text(x0 + cw * len(weights) / 2, y0 - 26, "体重（kg）", lang, 13, SOFT, "middle"))
    b.append(text(24, y0 - 8, "身高", lang, 13, SOFT))
    b.append(text(24, y0 + 8, "（cm）", lang, 12, SOFT))
    for j, wt in enumerate(weights):
        b.append(text(x0 + j * cw + cw / 2, y0 - 8, str(wt), lang, 13, INK, "middle", "bold"))
    for i, ht in enumerate(heights):
        y = y0 + i * ch
        b.append(text(x0 - 12, y + ch / 2 + 5, str(ht), lang, 13, INK, "end", "bold"))
        for j, wt in enumerate(weights):
            bmi = wt / (ht / 100) ** 2
            idx = next(k for k, band in enumerate(std["bands"])
                       if (band["lo"] is None or bmi >= band["lo"]) and (band["hi"] is None or bmi < band["hi"]))
            fill, ink = band_color(std, idx)
            x = x0 + j * cw
            b.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" fill="{fill}" stroke="#ffffff" stroke-width="1.5"/>')
            b.append(text(x + cw / 2, y + ch / 2 + 4, f"{bmi:.1f}", lang, 12, ink, "middle"))
    # 图例
    ly = y0 + ch * len(heights) + 34
    lx = 24
    for k, band in enumerate(std["bands"]):
        fill, _ = band_color(std, k)
        rng = (f"<{band['hi']:g}" if band["lo"] is None else
               f"≥{band['lo']:g}" if band["hi"] is None else f"{band['lo']:g}–{band['hi']:g}")
        label = f"{band['label']} {rng}"
        item_w = 22 + int(len(label) * 13 * 0.85) + 24
        if lx + item_w > w - 16:
            lx, ly = 24, ly + 26
        b.append(f'<rect x="{lx}" y="{ly - 13}" width="16" height="16" rx="3" fill="{fill}"/>')
        b.append(text(lx + 22, ly, label, lang, 13, INK))
        lx += item_w
    h = max(h, ly + 70)
    b.append(text(24, ly + 30, "BMI = 体重（kg）÷ 身高（m）²。区间含下限、不含上限；仅适用于成人。", lang, 12, SOFT))
    if lang == "ja":
        desc = f"身長150〜190cm・体重40〜115kgのBMIを、{std['name']}で色分けした早見表。"
        return svg_doc(w, h, b, lang, f"BMI早見表・{std['name']}", desc)
    desc = f"身高 150–190 cm、体重 40–115 kg 的 BMI 数值对照表，按{std['name']}的分级着色。"
    return svg_doc(w, h, b, lang, f"BMI 身高体重对照表 · {std['name']}", desc)


# ---------------------------------------------------------------------------
# 3. 男女体脂率参考范围（ACE 分级）
# ---------------------------------------------------------------------------
# 分级数据与工具页共用（app.BODYFAT_BANDS）；图上“必需脂肪”从男 2%、女 10% 画起
BODYFAT_FLOOR = {"male": 2, "female": 10}


def fig_bodyfat_ranges(lang: str) -> str:
    w, h = 760, 330
    x0, x1, vmax = 90, 730, 45
    sx = (x1 - x0) / vmax
    b: list[str] = []
    b.append(text(24, 40, "男女体脂率参考范围", lang, 24, INK, weight="bold"))
    b.append(text(24, 66, "美国运动委员会（ACE）分级 · 单位：体脂率 %", lang, 14, SOFT))
    for row, (sex, label) in enumerate((("male", "男性"), ("female", "女性"))):
        y = 104 + row * 92
        b.append(text(x0 - 14, y + 30, label, lang, 17, INK, "end", "bold"))
        b.append(f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="46" rx="6" fill="#f3f4f6"/>')
        for k, (name, lo, hi) in enumerate(BODYFAT_BANDS[sex]):
            lo = BODYFAT_FLOOR[sex] if lo is None else lo
            hi = vmax if hi is None else hi
            bx, bw = x0 + lo * sx, (hi - lo) * sx
            b.append(f'<rect x="{bx:.1f}" y="{y}" width="{bw:.1f}" height="46" fill="{BODYFAT_COLORS[k]}" '
                     f'stroke="#ffffff" stroke-width="2"/>')
            b.append(text(f"{bx + bw / 2:.1f}", y + 28, name, lang, 13 if bw > 60 else 11, INK, "middle"))
            b.append(text(f"{bx:.1f}", y + 64, f"{lo}%", lang, 12, SOFT, "middle"))
    b.append(text(24, 292, "低于必需脂肪的水平不宜长期维持；同一体重下，年龄越大体脂率通常越高。", lang, 12, SOFT))
    return svg_doc(w, h, b, lang, "男女体脂率参考范围（ACE 分级）",
                   "男性和女性体脂率分级条形图：必需脂肪、运动员、健身良好、一般水平、偏高。")


# ---------------------------------------------------------------------------
# 4. 分享卡片（og:image，1200×630 PNG）
# ---------------------------------------------------------------------------
def find_font(ja: bool = False) -> str:
    env = os.environ.get("CALMY_FONT_JA" if ja else "CALMY_FONT", "")
    name = "NotoSansJP-VF.ttf" if ja else "NotoSansSC-VF.ttf"
    cand = [env, f"C:/Windows/Fonts/{name}", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]
    for p in cand:
        if p and Path(p).exists():
            return p
    raise SystemExit("找不到中文字体，请用环境变量 CALMY_FONT 指定 Noto Sans SC 的路径")


def og_cards() -> list[tuple[str, str, str, str]]:
    """(key, 简体标题, 繁体标题, 分类) 列表。key 对应页面路径的最后一段，首页等用 default。"""
    tools = {tl["path"]: tl for tl in TOOLS}
    cards = [("default", "免费健康计算器与生活指南", "免費健康計算機與生活指南", "BMI · 热量 · 营养 · 步数 · 睡眠")]
    for path, title in (("/bmi", "BMI 计算器：身高体重指数与正常体重范围"),
                        ("/waist", "腰围身高比（WHtR）计算器"),
                        ("/whr", "腰臀比（WHR）计算器：WHO 标准"),
                        ("/bodyfat", "体脂率计算器：用软尺估算体脂率")):
        if path in tools:
            cards.append((path.strip("/"), title, to_hant_text(title), "健康计算器"))
    for a in ARTICLES:
        hant_h1 = HANT_OVERRIDES.get(a["slug"], {}).get("h1") or a["h1"]
        cards.append((a["slug"], a["h1"], to_hant_text(hant_h1), "健康指南 · " + a["category"]))
    return cards


def og_cards_ja() -> list[tuple[str, str, str]]:
    """日语版分享卡片：(key, 标题, 小标题)。"""
    cards = [("default", "無料の健康計算ツールと健康ガイド", "BMI・基礎代謝・カロリー・歩数・睡眠")]
    cards += [(tl["path"].strip("/"), tl["name"], "健康計算ツール") for tl in JA_TOOLS]
    cards += [(a["slug"], a["h1"], "健康ガイド・" + a["category"]) for a in JA_ARTICLES]
    return cards


def draw_card(font_path: str, title: str, kicker: str, out: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1200, 630
    img = Image.new("RGB", (W, H), "#f5f7fb")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 14], fill=BRAND)
    d.rounded_rectangle([60, 70, W - 60, H - 70], radius=28, fill="#ffffff", outline="#e7edf5", width=2)

    def font(size, weight="Regular"):
        f = ImageFont.truetype(font_path, size)
        try:
            f.set_variation_by_name(weight)
        except Exception:
            pass
        return f

    f_brand, f_kicker, f_title, f_foot = font(34, "Bold"), font(28), font(64, "Bold"), font(26)
    d.ellipse([110, 118, 146, 154], fill=BRAND)
    d.text((162, 114), "CalmyHealth", font=f_brand, fill=INK)
    d.text((112, 196), kicker, font=f_kicker, fill=BRAND)

    # 中文按字符折行，最多 3 行
    maxw, lines, cur = W - 230, [], ""
    for ch in title:
        if d.textlength(cur + ch, font=f_title) > maxw:
            lines.append(cur)
            cur = ch.lstrip()
        else:
            cur += ch
    lines.append(cur)
    if len(lines) > 3:
        lines = lines[:3]
        lines[2] = lines[2][:-1] + "…"
    y = 262
    for line in lines:
        d.text((110, y), line, font=f_title, fill=INK)
        y += 86
    d.text((112, H - 132), "calmyhealth.com", font=f_foot, fill=SOFT)
    img.quantize(colors=64, method=Image.Quantize.MEDIANCUT).save(out, optimize=True)


def main() -> None:
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    OG_DIR.mkdir(parents=True, exist_ok=True)
    figs = {
        "body-measurement": fig_body_measurement,
        "bmi-chart": fig_bmi_chart,
        "bodyfat-ranges": fig_bodyfat_ranges,
    }
    for name, fn in figs.items():
        for lang in LANGS:
            out = IMG_DIR / f"{name}{'' if lang == 'hans' else '.' + lang}.svg"
            out.write_text(fn(lang), encoding="utf-8", newline="\n")
            print("wrote", out.relative_to(ROOT))

    font_path = find_font()
    for key, hans_title, hant_title, kicker in og_cards():
        draw_card(font_path, hans_title, kicker, OG_DIR / f"{key}.png")
        draw_card(font_path, hant_title, to_hant_text(kicker), OG_DIR / f"{key}.hant.png")
    font_ja = find_font(ja=True)
    for key, title, kicker in og_cards_ja():
        draw_card(font_ja, title, kicker, OG_DIR / f"{key}.ja.png")
    print("wrote", len(og_cards()) * 2 + len(og_cards_ja()), "og cards")


if __name__ == "__main__":
    main()
