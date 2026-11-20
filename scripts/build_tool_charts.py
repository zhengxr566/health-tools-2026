"""工具页的对照图（SVG，简/繁/日），数值全部用 app.py 里各工具的同一套公式计算。

用法（在仓库根目录）：
    python scripts/build_tool_charts.py

输出：
    static/img/<key>.svg、<key>.hant.svg、<key>.ja.svg
    data/tool_chart_figures.json —— 尺寸、alt、说明文字和所在页面，app.py 读取后并入 FIGURES / PAGE_FIGURES
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from i18n_hant import to_hant_text  # noqa: E402

IMG = ROOT / "static" / "img"
FONT = {
    "hans": "'PingFang SC','Microsoft YaHei','Noto Sans SC','Noto Sans CJK SC',sans-serif",
    "hant": "'PingFang TC','Microsoft JhengHei','Noto Sans TC','Noto Sans CJK TC',sans-serif",
    "ja": "'Hiragino Sans','Hiragino Kaku Gothic ProN','Noto Sans JP','Yu Gothic','Meiryo',sans-serif",
}
LANGS = ("hans", "hant", "ja")
INK, SOFT, GRID = "#1f2937", "#6b7280", "#e5e7eb"
C3 = ("#4f7fe0", "#198754", "#e8833a")          # 三条线 / 三个系列
MAC = {"p": "#d1495b", "c": "#e8b23a", "f": "#4f7fe0"}


def L(lang, hans, ja):
    return ja if lang == "ja" else to_hant_text(hans) if lang == "hant" else hans


def tx(x, y, s, size=13, fill=INK, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}">{escape(str(s))}</text>')


def doc(w, h, lang, title, desc, body):
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="{FONT[lang]}" role="img">',
        f"<title>{escape(title)}</title>", f"<desc>{escape(desc)}</desc>",
        f'<rect width="{w}" height="{h}" fill="#ffffff"/>', *body,
        f'<text x="{w - 14}" y="{h - 12}" text-anchor="end" font-size="12" fill="#9ca3af">calmyhealth.com</text>',
        "</svg>", ""])


def hms(sec):
    sec = int(round(sec))
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def line_chart(lang, title, sub, xs, series, xlab, ylab, note, ymax=None, xfmt=str, yfmt=str, label_at=None):
    """series: [(name, color, [y...])]"""
    W, H = 760, 470
    l, r, t, b = 74, 150, 92, 78
    ymax = ymax or max(max(s[2]) for s in series) * 1.08
    x0, x1 = xs[0], xs[-1]
    X = lambda v: l + (v - x0) / (x1 - x0) * (W - l - r)
    Y = lambda v: H - b - v / ymax * (H - t - b)
    body = [tx(24, 40, title, 21, weight="bold"), tx(24, 64, sub, 12.5, SOFT)]
    step = _nice(ymax)
    v = 0
    while v <= ymax + 1e-9:
        body.append(f'<line x1="{l}" y1="{Y(v):.1f}" x2="{W - r}" y2="{Y(v):.1f}" stroke="{GRID}"/>')
        body.append(tx(l - 8, Y(v) + 4, yfmt(v), 11.5, SOFT, "end"))
        v += step
    for xv in xs:
        body.append(tx(X(xv), H - b + 18, xfmt(xv), 11.5, SOFT, "middle"))
    body.append(tx((l + W - r) / 2, H - b + 40, xlab, 12.5, SOFT, "middle"))
    body.append(tx(l - 8, t - 14, ylab, 12, SOFT, "end"))
    for name, color, ys in series:
        pts = " ".join(f"{X(a):.1f},{Y(c):.1f}" for a, c in zip(xs, ys))
        body.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="3"/>')
        for a, c in zip(xs, ys):
            body.append(f'<circle cx="{X(a):.1f}" cy="{Y(c):.1f}" r="3.2" fill="{color}"/>')
        body.append(tx(X(xs[-1]) + 10, Y(ys[-1]) + 4, name, 12.5, color, weight="bold"))
        if label_at is not None:
            i = xs.index(label_at)
            body.append(tx(X(xs[i]), Y(ys[i]) - 9, yfmt(ys[i]), 11.5, color, "middle", "bold"))
    body.append(tx(24, H - 14, note, 11, SOFT))
    return W, H, body


def _nice(vmax):
    for s in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000):
        if vmax / s <= 7:
            return s
    return 2000


# ---------------------------------------------------------------------------
def chart_pace(lang):
    paces = [240 + 30 * i for i in range(9)]     # 4:00–8:00 /km
    dists = [(5, "5K"), (10, "10K"), (21.0975, L(lang, "半程马拉松", "ハーフ")), (42.195, L(lang, "全程马拉松", "フル"))]
    W, rowh, top = 760, 38, 118
    H = top + rowh * len(paces) + 64
    cols = [190, 310, 430, 565, 700]
    body = [tx(24, 40, L(lang, "配速与完赛时间对照表", "ペース別・完走タイム早見表"), 21, weight="bold"),
            tx(24, 64, L(lang, "按全程匀速计算（与本站配速计算器相同）；距离越长，实际成绩通常越慢",
                         "全区間を同じペースで走った場合（当サイトの計算機と同じ方法）。長い距離ほど実際はこれより遅くなりがちです"), 12.5, SOFT)]
    hdr = [L(lang, "配速（/km）", "ペース（/km）"), L(lang, "时速", "時速")] + [d[1] for d in dists]
    xs = [24, 140] + cols[1:]
    body.append(f'<rect x="16" y="{top - 30}" width="{W - 32}" height="30" fill="#f3f4f6"/>')
    for x, hname in zip([28, 150, 290, 410, 540, 670], hdr):
        body.append(tx(x, top - 10, hname, 13, INK, weight="bold"))
    for i, p in enumerate(paces):
        y = top + i * rowh
        if i % 2 == 0:
            body.append(f'<rect x="16" y="{y}" width="{W - 32}" height="{rowh}" fill="#fafafa"/>')
        body.append(tx(28, y + 25, f"{p // 60}'{p % 60:02d}\"", 15, INK, weight="bold"))
        body.append(tx(150, y + 25, f"{3600 / p:.1f} km/h", 13, SOFT))
        for x, (d, _) in zip([290, 410, 540, 670], dists):
            body.append(tx(x, y + 25, hms(p * d), 14))
    body.append(tx(24, H - 22, L(lang, "例：配速 6'00\"/km，10K 约 1:00:00，半马约 2:06:35。",
                                   "例：キロ6分00秒なら、10Kは約1:00:00、ハーフは約2:06:35。"), 11.5, SOFT))
    t = L(lang, "跑步配速与完赛时间对照表（5K、10K、半马、全马）", "ランニングのペース別完走タイム早見表（5K・10K・ハーフ・フル）")
    return W, H, doc(W, H, lang, t, t, body)


def chart_steps_time(lang):
    xs = [2000, 4000, 6000, 8000, 10000, 12000, 15000, 20000]
    series = [(L(lang, f"慢 {s} 步/分", f"ゆっくり {s}歩/分") if s == 80 else
               L(lang, f"常速 {s} 步/分", f"ふつう {s}歩/分") if s == 100 else
               L(lang, f"快 {s} 步/分", f"速歩き {s}歩/分"), c, [x / s for x in xs])
              for s, c in zip((80, 100, 130), C3)]
    W, H, body = line_chart(
        lang, L(lang, "步数与步行时间对照图", "歩数と歩く時間の早見グラフ"),
        L(lang, "时间 = 步数 ÷ 步频（每分钟步数）；1 万步：慢走约 125 分钟、常速 100 分钟、快走约 77 分钟",
          "時間＝歩数÷歩調（1分あたりの歩数）。1万歩はゆっくり約125分、ふつう100分、速歩き約77分"),
        xs, series, L(lang, "步数", "歩数"), L(lang, "分钟", "分"),
        L(lang, "步频因人而异，可以数 1 分钟自己的步数来校正。", "歩調は人によって違うので、1分間の歩数を数えて調整してください。"),
        ymax=260, xfmt=lambda v: f"{v // 1000}k", yfmt=lambda v: f"{v:.0f}", label_at=10000)
    t = L(lang, "步数换算步行时间对照图（2,000–20,000 步）", "歩数から歩く時間の早見グラフ（2,000〜20,000歩）")
    return W, H, doc(W, H, lang, t, t, body)


def chart_steps_distance(lang):
    xs = [150, 155, 160, 165, 170, 175, 180, 185, 190]
    series = [(L(lang, "男性", "男性"), C3[0], [10000 * h * 0.415 / 100000 for h in xs]),
              (L(lang, "女性", "女性"), C3[2], [10000 * h * 0.413 / 100000 for h in xs])]
    W, H, body = line_chart(
        lang, L(lang, "1 万步是多少公里？按身高对照", "1万歩は何km？身長別の早見グラフ"),
        L(lang, "步幅 ≈ 身高 × 0.415（男）/ 0.413（女），距离 = 步数 × 步幅；身高 170 cm 的男性 1 万步约 7.1 km",
          "歩幅≈身長×0.415（男性）／0.413（女性）、距離＝歩数×歩幅。身長170cmの男性で1万歩は約7.1km"),
        xs, series, L(lang, "身高（cm）", "身長（cm）"), "km",
        L(lang, "快走时步幅变大、上坡或拥挤时变小，误差约在 ±10% 内常见。", "速歩きでは歩幅が広がり、坂道や混雑では狭くなります。"),
        ymax=8.5, xfmt=str, yfmt=lambda v: f"{v:.1f}" if v % 1 else f"{v:.0f}", label_at=170)
    t = L(lang, "1 万步等于多少公里：身高与步行距离对照图", "1万歩は何km：身長別の歩行距離グラフ")
    return W, H, doc(W, H, lang, t, t, body)


def _per_kg(lang, key, title_h, title_j, sub_h, sub_j, factors, names_h, names_j, note_h, note_j, ymax):
    xs = list(range(45, 105, 5))
    series = [(L(lang, f"{nh} {f:g} g/kg", f"{nj} {f:g}g/kg"), c, [x * f for x in xs])
              for f, nh, nj, c in zip(factors, names_h, names_j, C3)]
    W, H, body = line_chart(lang, L(lang, title_h, title_j), L(lang, sub_h, sub_j), xs, series,
                            L(lang, "体重（kg）", "体重（kg）"), L(lang, "克/天", "g/日"), L(lang, note_h, note_j),
                            ymax=ymax, yfmt=lambda v: f"{v:.0f}", label_at=60)
    t = L(lang, title_h, title_j)
    return W, H, doc(W, H, lang, t, t, body)


def chart_carbs(lang):
    return _per_kg(lang, "carbs", "每天该吃多少碳水？按体重对照", "1日の炭水化物量：体重別の早見グラフ",
                   "减脂 3 g/kg、维持 4 g/kg、增肌 5 g/kg（与本站碳水计算器相同）；体重 60 kg 维持期约 240 g",
                   "減量3g/kg・維持4g/kg・増量5g/kg（当サイトの計算機と同じ）。体重60kgの維持期で約240g",
                   (3.0, 4.0, 5.0), ("减脂", "维持", "增肌"), ("減量", "維持", "増量"),
                   "1 g 碳水约 4 kcal；运动量很大或很小时需要上下调整。", "炭水化物1gは約4kcal。運動量が多い・少ない場合は調整が必要です。", 520)


def chart_fat(lang):
    return _per_kg(lang, "fat", "每天该吃多少脂肪？按体重对照", "1日の脂質量：体重別の早見グラフ",
                   "减脂 0.8 g/kg、维持 1.0 g/kg、增肌 1.1 g/kg（与本站脂肪计算器相同）；体重 60 kg 维持期约 60 g",
                   "減量0.8g/kg・維持1.0g/kg・増量1.1g/kg。体重60kgの維持期で約60g",
                   (0.8, 1.0, 1.1), ("减脂", "维持", "增肌"), ("減量", "維持", "増量"),
                   "1 g 脂肪约 9 kcal；包括烹调油、坚果、肉类和乳制品中的脂肪。", "脂質1gは約9kcal。調理油・ナッツ・肉・乳製品に含まれる分も含みます。", 120)


def chart_protein(lang):
    return _per_kg(lang, "protein", "每天该吃多少蛋白质？按体重对照", "1日のたんぱく質量：体重別の早見グラフ",
                   "日常 1.2 g/kg、减脂 1.6 g/kg、增肌 1.8 g/kg（与本站蛋白质计算器相同）；体重 60 kg 日常约 72 g",
                   "日常1.2g/kg・減量1.6g/kg・筋肥大1.8g/kg（当サイトの計算機と同じ）。体重60kgの日常で約72g",
                   (1.2, 1.6, 1.8), ("日常", "减脂", "增肌"), ("日常", "減量", "筋肥大"),
                   "肥胖者宜按标准体重计算；肾功能不全者请遵医嘱。", "肥満の方は標準体重で計算を。腎臓病の方は医師の指示に従ってください。", 200)


def chart_macro(lang):
    modes = [(L(lang, "减脂期", "減量期"), .30, .35, .35), (L(lang, "维持期", "維持期"), .25, .45, .30),
             (L(lang, "增肌期", "増量期"), .25, .50, .25)]
    if lang == "ja":
        modes = [("食事摂取基準の目安", .15, .60, .25)] + modes
    kcal = 2000
    W = 760
    top, rowh = 120, 66
    H = top + rowh * len(modes) + 70
    l, r = 150, 30
    bw = W - l - r
    body = [tx(24, 40, L(lang, "三大营养素怎么分配？按目标对照（2,000 kcal）", "PFCバランスの配分：目的別の早見図（2,000kcal）"), 21, weight="bold"),
            tx(24, 64, L(lang, "与本站宏量营养素计算器相同的比例；蛋白质、碳水 1 g = 4 kcal，脂肪 1 g = 9 kcal",
                         "当サイトのPFC計算機と同じ比率。たんぱく質・炭水化物は1g＝4kcal、脂質は1g＝9kcal"), 12.5, SOFT)]
    lg = [(MAC["p"], L(lang, "蛋白质", "たんぱく質")), (MAC["c"], L(lang, "碳水", "炭水化物")), (MAC["f"], L(lang, "脂肪", "脂質"))]
    x = 24
    for col, name in lg:
        body.append(f'<rect x="{x}" y="82" width="14" height="14" rx="3" fill="{col}"/>')
        body.append(tx(x + 20, 94, name, 12.5))
        x += 20 + len(name) * 13 + 24
    for i, (name, p, c, f) in enumerate(modes):
        y = top + i * rowh
        body.append(tx(24, y + 28, name, 14, weight="bold"))
        x = l
        for share, col, g in ((p, MAC["p"], kcal * p / 4), (c, MAC["c"], kcal * c / 4), (f, MAC["f"], kcal * f / 9)):
            w = bw * share
            body.append(f'<rect x="{x:.1f}" y="{y + 8}" width="{w - 2:.1f}" height="30" rx="4" fill="{col}"/>')
            body.append(tx(x + w / 2, y + 28, f"{share * 100:.0f}%", 12.5, "#fff", "middle", "bold"))
            body.append(tx(x + w / 2, y + 56, f"{g:.0f} g", 12, SOFT, "middle"))
            x += w
    body.append(tx(24, H - 22, L(lang, "热量不同时，克数按比例增减；例如 1,600 kcal 维持期：蛋白质 100 g、碳水 180 g、脂肪 53 g。",
                                   "エネルギー量が違えばグラム数も比例して変わります。例：1,600kcalの維持期はP100g・C180g・F53g。"), 11.5, SOFT))
    t = L(lang, "三大营养素比例与克数对照图（减脂、维持、增肌）", "PFCバランスの比率とグラム数（目的別）")
    return W, H, doc(W, H, lang, t, t, body)


def chart_deficit(lang):
    kcal_per_kg = 7200 if lang == "ja" else 7700
    deficits = [250, 300, 500, 750, 1000]
    W, top, rowh = 760, 118, 54
    H = top + rowh * len(deficits) + 70
    l = 170
    maxw = W - l - 210
    body = [tx(24, 40, L(lang, "每天少吃多少热量，一周能减多少？", "1日に何kcal減らすと、1週間で何kg減る？"), 21, weight="bold"),
            tx(24, 64, L(lang, f"按 1 kg 体脂肪 ≈ {kcal_per_kg:,} kcal 估算：每周减重 = 每日缺口 × 7 ÷ {kcal_per_kg:,}",
                         f"体脂肪1kg≈{kcal_per_kg:,}kcalとして計算：1週間の減少量＝1日の不足分×7÷{kcal_per_kg:,}"), 12.5, SOFT)]
    body.append(tx(l, top - 12, L(lang, "每周约减（kg）", "1週間の減少（kg）"), 12, SOFT))
    body.append(tx(W - 24, top - 12, L(lang, "减 5 kg 约需", "5kg減に必要な期間"), 12, SOFT, "end"))
    wk_max = 1000 * 7 / kcal_per_kg
    for i, d in enumerate(deficits):
        y = top + i * rowh
        kg = d * 7 / kcal_per_kg
        weeks = 5 / kg
        col = "#198754" if d <= 500 else "#e8833a"
        body.append(tx(24, y + 26, L(lang, f"每天 −{d} kcal", f"1日 −{d}kcal"), 14, weight="bold"))
        body.append(f'<rect x="{l}" y="{y + 8}" width="{maxw * kg / wk_max:.1f}" height="26" rx="4" fill="{col}"/>')
        body.append(tx(l + maxw * kg / wk_max + 8, y + 26, f"{kg:.2f} kg", 13))
        body.append(tx(W - 24, y + 26, L(lang, f"约 {weeks:.0f} 周", f"約{weeks:.0f}週"), 13, INK, "end"))
    body.append(tx(24, H - 38, L(lang, "绿色：每天 300–500 kcal 的常用范围；橙色：缺口较大，更难坚持，也更容易流失肌肉。",
                                   "緑：1日300〜500kcalの一般的な範囲。オレンジ：不足が大きく、続けにくく筋肉も落ちやすくなります。"), 11.5, SOFT))
    body.append(tx(24, H - 20, L(lang, "实际减重会比线性估算慢：体重下降后消耗也随之减少（Hall 等，2011）。",
                                   "実際の減り方は計算より遅くなりがちです。体重が減ると消費量も下がるためです。"), 11.5, SOFT))
    t = L(lang, "热量缺口与每周减重对照图", "エネルギー不足量と1週間の減量の目安")
    return W, H, doc(W, H, lang, t, t, body)


CHARTS = {
    # key: (函数, 所在页面, 简体 alt, 简体说明, 日语 alt, 日语说明)
    "pace-finish-times": (chart_pace, "/running-pace",
                          "跑步配速与完赛时间对照表：配速 4:00–8:00/km 对应的时速及 5K、10K、半马、全马完赛时间",
                          "配速与完赛时间对照表。按全程匀速计算，长距离的实际成绩通常会比表中慢一些。",
                          "ランニングのペース別完走タイム早見表：キロ4分〜8分の時速と5K・10K・ハーフ・フルの完走タイム",
                          "ペース別の完走タイム早見表。一定ペースで走った場合の計算で、長い距離ほど実際は遅くなりがちです。"),
    "steps-time-chart": (chart_steps_time, "/steps-time",
                         "步数与步行时间对照图：2,000–20,000 步在每分钟 80、100、130 步时需要的分钟数",
                         "步数换算步行时间：同样 1 万步，慢走约 125 分钟，常速 100 分钟，快走约 77 分钟。",
                         "歩数と歩く時間の早見グラフ：2,000〜20,000歩を1分80・100・130歩で歩いたときの時間",
                         "歩数から歩く時間の目安。同じ1万歩でも、ゆっくり約125分、ふつう100分、速歩き約77分です。"),
    "steps-distance-chart": (chart_steps_distance, "/steps-distance",
                             "1 万步是多少公里：身高 150–190 cm 男女的步行距离折线图",
                             "1 万步对应的步行距离随身高增加：身高每高 5 cm，1 万步约多走 0.2 km。",
                             "1万歩は何km：身長150〜190cmの男女別の歩行距離グラフ",
                             "1万歩で歩ける距離は身長とともに長くなり、身長が5cm高いと約0.2km長くなります。"),
    "carbs-by-weight": (chart_carbs, "/carbs",
                        "每日碳水化合物需求对照图：体重 45–100 kg 在减脂、维持、增肌时每天的克数",
                        "按体重估算每天的碳水克数：减脂 3 g/kg、维持 4 g/kg、增肌 5 g/kg。",
                        "1日の炭水化物量の早見グラフ：体重45〜100kgの減量・維持・増量別のグラム数",
                        "体重から見た1日の炭水化物量。減量3g/kg、維持4g/kg、増量5g/kg。"),
    "fat-by-weight": (chart_fat, "/fat-intake",
                      "每日脂肪摄入对照图：体重 45–100 kg 在减脂、维持、增肌时每天的克数",
                      "按体重估算每天的脂肪克数：减脂 0.8 g/kg、维持 1.0 g/kg、增肌 1.1 g/kg。",
                      "1日の脂質量の早見グラフ：体重45〜100kgの減量・維持・増量別のグラム数",
                      "体重から見た1日の脂質量。減量0.8g/kg、維持1.0g/kg、増量1.1g/kg。"),
    "protein-by-weight": (chart_protein, "/protein",
                          "每日蛋白质需求对照图：体重 45–100 kg 在日常、减脂、增肌时每天的克数",
                          "按体重估算每天的蛋白质克数：日常 1.2 g/kg、减脂 1.6 g/kg、增肌 1.8 g/kg。",
                          "1日のたんぱく質量の早見グラフ：体重45〜100kgの日常・減量・筋肥大別のグラム数",
                          "体重から見た1日のたんぱく質量。日常1.2g/kg、減量1.6g/kg、筋肥大1.8g/kg。"),
    "macro-split-chart": (chart_macro, "/macro",
                          "三大营养素比例与克数对照图：2,000 kcal 时减脂、维持、增肌的蛋白质、碳水、脂肪克数",
                          "三种目标下蛋白质、碳水、脂肪的比例和克数（以每天 2,000 kcal 为例）。",
                          "PFCバランスの比率とグラム数の図：2,000kcalのときの目的別のたんぱく質・炭水化物・脂質",
                          "目的別のたんぱく質・炭水化物・脂質の比率とグラム数（1日2,000kcalの例）。"),
    "deficit-weekly-loss": (chart_deficit, "/deficit",
                            "热量缺口与每周减重对照图：每天少吃 250–1,000 kcal 时每周约减多少公斤、减 5 kg 要几周",
                            "每日热量缺口与每周减重的关系；每天 300–500 kcal 是较容易坚持的范围。",
                            "エネルギー不足量と1週間の減量の目安：1日250〜1,000kcal減らしたときの1週間の減少量と5kg減に必要な週数",
                            "1日のエネルギー不足量と1週間の減量の関係。1日300〜500kcalが続けやすい範囲です。"),
}


def main():
    meta = {}
    for key, (fn, page, alt, cap, alt_ja, cap_ja) in CHARTS.items():
        for lang in LANGS:
            w, h, svg = fn(lang)
            (IMG / f"{key}{'' if lang == 'hans' else '.' + lang}.svg").write_text(svg, encoding="utf-8", newline="\n")
        meta[key] = {"w": w, "h": h, "page": page, "alt": alt, "caption": cap, "ja": {"alt": alt_ja, "caption": cap_ja}}
    (ROOT / "data" / "tool_chart_figures.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1),
                                                          encoding="utf-8", newline="\n")
    print("wrote", len(CHARTS) * 3, "charts")


if __name__ == "__main__":
    main()
