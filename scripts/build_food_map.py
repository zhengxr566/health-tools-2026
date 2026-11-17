"""食物营养图谱：按营养素密度给常见食物做层次聚类，生成示意图（SVG，简/繁/日）和页面用的 JSON。

用法（在仓库根目录）：
    python scripts/build_food_map.py

依赖：numpy、scipy（只在本脚本里用，线上不需要）。
输入：data/nutrition_foods.json（每 100 g 的营养素，来源见 build_nutrition_foods.py）
输出：
    static/img/food-*.svg、*.hant.svg、*.ja.svg
    static/data/food-map.json          —— 页面里“查相似 / 互补食物”小工具用
    data/food_map_figures.json         —— 图片的 alt / 说明文字 / 尺寸，app.py 读取

方法：
    1. 去掉调味料和几乎没有热量的饮品（美式咖啡），剩 109 种食物。
    2. 对 10 种营养素计算“每 100 kcal 提供的参考摄入量百分比”（营养素密度），取 log10(1 + x/5)；
       再加上脂肪、碳水的供能比。各列标准化后用 Ward 法层次聚类，切成 11 群。
    3. 二维图谱用同一组特征的主成分分析（PCA）前两个主成分。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from i18n_hant import to_hant_text  # noqa: E402

IMG_DIR = ROOT / "static" / "img"
FONT = {
    "hans": "'PingFang SC','Microsoft YaHei','Noto Sans SC','Noto Sans CJK SC',sans-serif",
    "hant": "'PingFang TC','Microsoft JhengHei','Noto Sans TC','Noto Sans CJK TC',sans-serif",
    "ja": "'Hiragino Sans','Hiragino Kaku Gothic ProN','Noto Sans JP','Yu Gothic','Meiryo',sans-serif",
}
LANGS = ("hans", "hant", "ja")
INK, SOFT, LINE = "#1f2937", "#6b7280", "#e5e7eb"

# 计算密度用的成人参考值（只用来把不同营养素放到同一尺度上比较，不作为推荐量展示）
REF = {"protein": 55, "fiber": 25, "potassium": 2000, "calcium": 800, "iron": 15, "magnesium": 330,
       "zinc": 8, "vit_a": 700, "vit_c": 100, "sodium": 1500}
DENS = list(REF)  # 10 种营养素
UNIT = {"protein": "g", "fiber": "g", "potassium": "mg", "calcium": "mg", "iron": "mg", "magnesium": "mg",
        "zinc": "mg", "vit_a": "µg", "vit_c": "mg", "sodium": "mg"}
NUT = {  # (简体, 日语)
    "protein": ("蛋白质", "たんぱく質"), "fiber": ("膳食纤维", "食物繊維"), "potassium": ("钾", "カリウム"),
    "calcium": ("钙", "カルシウム"), "iron": ("铁", "鉄"), "magnesium": ("镁", "マグネシウム"),
    "zinc": ("锌", "亜鉛"), "vit_a": ("维生素A", "ビタミンA"), "vit_c": ("维生素C", "ビタミンC"),
    "sodium": ("钠", "ナトリウム"), "fat_e": ("脂肪供能比", "脂質エネルギー比"),
    "carb_e": ("碳水供能比", "炭水化物エネルギー比"),
}

JA_NAME = {
    1: "白ごはん", 2: "玄米ごはん", 3: "マントウ", 4: "食パン", 5: "全粒粉食パン", 6: "オートミール",
    7: "パスタ（ゆで）", 8: "ビーフン", 9: "うどん", 10: "さつまいも", 11: "じゃがいも", 12: "スイートコーン",
    13: "水餃子", 14: "肉まん", 15: "小籠包", 16: "焼き餃子", 17: "もち米おにぎり", 18: "おにぎり（肉でんぶ）",
    19: "肉ちまき", 20: "大根もち", 21: "シャオビン", 22: "揚げパン（油条）", 23: "インスタントラーメン",
    24: "バーガーバンズ", 25: "ピザ", 26: "チャーハン", 27: "ゆで卵", 28: "目玉焼き", 29: "茶葉卵",
    30: "牛乳", 31: "低脂肪牛乳", 32: "ヨーグルト（加糖）", 33: "スライスチーズ", 34: "豆乳（無調整）",
    35: "豆乳（加糖）", 36: "木綿豆腐", 37: "絹ごし豆腐", 38: "押し豆腐", 39: "豆花（無糖）", 40: "枝豆",
    41: "鶏むね肉", 42: "鶏もも肉", 43: "豚ヒレ肉", 44: "豚ひき肉", 45: "牛赤身肉", 46: "ハンバーグ",
    47: "鮭", 48: "さば", 49: "ティラピア", 50: "ツナ缶（水煮）", 51: "えび", 52: "ベーコン", 53: "ハム",
    54: "キャベツ", 55: "ブロッコリー", 56: "ほうれん草", 57: "さつまいもの葉", 58: "空心菜",
    59: "チンゲン菜", 60: "白菜", 61: "トマト", 62: "にんじん", 63: "たまねぎ", 64: "きゅうり", 65: "なす",
    66: "ピーマン", 67: "しいたけ", 68: "えのき", 69: "もやし", 70: "オクラ", 71: "さやいんげん",
    72: "かぼちゃ", 73: "レタス", 74: "わかめ", 75: "のり", 76: "バナナ", 77: "りんご", 78: "オレンジ",
    79: "グァバ", 80: "キウイ", 81: "ぶどう", 82: "すいか", 83: "パパイヤ", 84: "パイナップル",
    85: "マンゴー", 86: "いちご", 87: "ブルーベリー", 88: "梨", 89: "桃", 90: "グレープフルーツ",
    91: "ピーナッツ", 92: "アーモンド", 93: "くるみ", 94: "カシューナッツ", 95: "黒すりごま",
    96: "大豆油", 97: "オリーブ油", 102: "タピオカミルクティー", 103: "ミルクティー（無糖）", 104: "コーラ",
    105: "カフェラテ（無糖）", 107: "オレンジジュース", 108: "スポーツドリンク", 109: "ビール",
    110: "ポテトチップス", 111: "ミルクチョコ", 112: "高カカオチョコ", 113: "バニラアイス", 114: "クラッカー",
}

# 11 个群：用“代表食物”认领聚类结果，这样即使重新计算后编号变了，名字也不会贴错
CLUSTERS = [
    # key, 代表食物 id, 颜色, 简体名, 简体一句话, 日语名, 日语一句话
    ("veg-light", 55, "#5fa83b", "浅色蔬菜", "膳食纤维、钾、维生素C", "淡色野菜", "食物繊維・カリウム・ビタミンC"),
    ("veg-orange", 62, "#f08c2e", "橙黄色蔬菜与薯类", "维生素A、钾", "緑黄色野菜・いも", "ビタミンA・カリウム"),
    ("veg-leafy", 56, "#1d7a3e", "深绿叶菜", "铁、钙、维生素A、镁", "濃い緑の葉物", "鉄・カルシウム・ビタミンA・マグネシウム"),
    ("seaweed", 75, "#23978f", "海藻", "铁、镁（也含较多钠）", "海藻", "鉄・マグネシウム（ナトリウムも多め）"),
    ("grain-bean", 40, "#9a6b3f", "全谷、毛豆与菇类", "锌、膳食纤维、镁", "全粒穀物・枝豆・きのこ", "亜鉛・食物繊維・マグネシウム"),
    ("soy-nut", 36, "#c9a227", "豆制品与坚果", "镁、钙、优质脂肪", "大豆製品・ナッツ", "マグネシウム・カルシウム・良質な脂質"),
    ("meat-fish", 41, "#d1495b", "肉、鱼、虾", "蛋白质、锌、铁", "肉・魚・えび", "たんぱく質・亜鉛・鉄"),
    ("egg-dairy", 30, "#4f7fe0", "蛋、奶与加工肉", "蛋白质、钙（加工肉高钠）", "卵・乳製品・加工肉", "たんぱく質・カルシウム（加工肉は高塩分）"),
    ("fruit", 80, "#e0609f", "水果与浅色根茎", "维生素C、钾", "果物・淡色の根菜", "ビタミンC・カリウム"),
    ("bun-noodle", 14, "#8d99ae", "面点与加工主食", "碳水化合物，钠偏高", "粉もの・加工主食", "炭水化物（塩分が多め）"),
    ("refined", 1, "#6c757d", "精制主食与高热量零食饮料", "主要提供能量，微量营养素少", "精製穀物・菓子・甘い飲み物", "エネルギー中心で微量栄養素が少ない"),
]


def short_hans(n: str) -> str:
    s = re.sub(r"（[^）]*）", "", n)
    s = s.split(" / ")[0]
    return s.strip()


def load_foods():
    d = json.load(open(ROOT / "data" / "nutrition_foods.json", encoding="utf-8"))
    keys = d["keys"]
    foods = [f for f in d["foods"] if f["g"] != "调味料" and f["v"][0] >= 5]
    shorts = [short_hans(f["n"]) for f in foods]
    for f, s in zip(foods, shorts):
        v = dict(zip(keys, f["v"]))
        f["vals"] = v
        f["hans"] = s if shorts.count(s) == 1 else f["n"]
        f["ja"] = JA_NAME[f["id"]]
        f["hant"] = to_hant_text(f["hans"])
    return foods


def features(foods):
    X = []
    for f in foods:
        v = f["vals"]
        row = [np.log10(1 + 100 * 100 * v[k] / v["kcal"] / REF[k] / 5) for k in DENS]
        e = v["protein"] * 4 + v["fat"] * 9 + v["carbs"] * 4
        row += [v["fat"] * 9 / e, v["carbs"] * 4 / e]
        X.append(row)
    X = np.array(X)
    Z = (X - X.mean(0)) / X.std(0)
    Z[:, 10:] = X[:, 10:] * 2.4  # 供能比本身是 0–1，放大到与标准化列相近的权重
    return X, Z


# ---------------------------------------------------------------------------
# SVG 小工具
# ---------------------------------------------------------------------------
def L(lang, hans, ja):
    return ja if lang == "ja" else to_hant_text(hans) if lang == "hant" else hans


def svg_doc(w, h, body, lang, title, desc):
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'font-family="{FONT[lang]}" role="img">',
        f"<title>{escape(title)}</title>", f"<desc>{escape(desc)}</desc>",
        f'<rect width="{w}" height="{h}" fill="#ffffff"/>', *body,
        f'<text x="{w - 16}" y="{h - 12}" text-anchor="end" font-size="12" fill="#9ca3af">calmyhealth.com</text>',
        "</svg>", ""])


def tx(x, y, s, size=13, fill=INK, anchor="start", weight="normal", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}"{extra}>{escape(str(s))}</text>')


def text_w(s, size):
    return sum(size * (0.55 if ord(c) < 128 else 1.0) for c in s)


def legend(clusters, lang, x0, y0, width, size=12):
    out, x, y = [], x0, y0
    for c in clusters:
        label = L(lang, c[3], c[5])
        w = 18 + text_w(label, size) + 18
        if x + w > x0 + width:
            x, y = x0, y + 20
        out.append(f'<circle cx="{x + 6}" cy="{y - 4}" r="5.5" fill="{c[2]}"/>')
        out.append(tx(x + 16, y, label, size))
        x += w
    return out, y


# ---------------------------------------------------------------------------
# 图 1：二维营养图谱（PCA）
# ---------------------------------------------------------------------------
def fig_map(foods, Z, lab, lang):
    W, H = 1000, 860
    U, S, Vt = np.linalg.svd(Z - Z.mean(0), full_matrices=False)
    P = U[:, :2] * S[:2]
    # 横轴：右 = 每 100 kcal 微量营养素多（钾指向右）；纵轴：上 = 碳水为主（碳水供能比指向上）
    if Vt[0, DENS.index("potassium")] < 0:
        P[:, 0] *= -1
    if Vt[1, 11] < 0:
        P[:, 1] *= -1
    P = np.sign(P) * np.abs(P) ** 0.7  # 稍微压缩两端，避免少数蔬菜把其他点挤在一起
    left, right, top, bottom = 50, W - 40, 130, H - 120
    xs = np.interp(P[:, 0], (P[:, 0].min(), P[:, 0].max()), (left + 30, right - 60))
    ys = np.interp(P[:, 1], (P[:, 1].min(), P[:, 1].max()), (bottom - 24, top + 24))
    body = [tx(30, 44, L(lang, "常见食物营养图谱：哪些食物营养相似？", "身近な食品の栄養マップ：栄養が似ている食品は？"), 24, weight="bold"),
            tx(30, 72, L(lang, "109 种食物按每 100 kcal 的营养素密度做主成分分析，颜色为层次聚类的 11 个营养群；距离越近，营养组成越相似",
                         "109食品を100 kcalあたりの栄養素密度で主成分分析。色は階層クラスタリングの11グループ。近いほど栄養の組み立てが似ています"), 13, SOFT)]
    body.append(f'<rect x="{left}" y="{top}" width="{right - left}" height="{bottom - top}" fill="#fafafa" stroke="{LINE}"/>')
    ax = "#94a3b8"
    body.append(tx(left + 8, top - 10, L(lang, "↑ 碳水为主（水果、主食、甜饮）", "↑ 炭水化物が中心（果物・主食・甘い飲み物）"), 12, ax))
    body.append(tx(left + 8, bottom + 18, L(lang, "↓ 蛋白质、脂肪为主（肉鱼、蛋奶、豆制品、坚果）", "↓ たんぱく質・脂質が中心（肉・魚・卵・乳・大豆・ナッツ）"), 12, ax))
    body.append(tx(right - 8, top - 10, L(lang, "微量营养素密度高（蔬菜）→", "ビタミン・ミネラルが多い（野菜）→"), 12, ax, "end"))
    body.append(tx(right - 8, bottom + 18, L(lang, "← 能量为主、微量营养素少", "← エネルギー中心・微量栄養素が少ない"), 12, ax, "end"))
    placed = []
    order = np.argsort(xs)
    for i in order:
        c = CLUSTERS[lab[i]]
        body.append(f'<circle cx="{xs[i]:.1f}" cy="{ys[i]:.1f}" r="5" fill="{c[2]}" stroke="#fff" stroke-width="1"/>')
        placed.append((xs[i] - 5, ys[i] - 5, xs[i] + 5, ys[i] + 5))
    for i in order:
        name = foods[i][lang]
        w, h = text_w(name, 11), 12
        for ox, oy, anc in ((7, 4, "start"), (-7, 4, "end"), (0, -8, "middle"), (0, 16, "middle"),
                            (7, -6, "start"), (-7, -6, "end"), (7, 13, "start"), (-7, 13, "end")):
            x0 = xs[i] + ox - (w if anc == "end" else w / 2 if anc == "middle" else 0)
            box = (x0, ys[i] + oy - h + 2, x0 + w, ys[i] + oy + 2)
            if box[0] < left or box[2] > right or box[1] < top or box[3] > bottom:
                continue
            if all(box[2] < b[0] or box[0] > b[2] or box[3] < b[1] or box[1] > b[3] for b in placed):
                placed.append(box)
                body.append(tx(xs[i] + ox, ys[i] + oy, name, 11, "#374151", anc))
                break
    lg, ly = legend(CLUSTERS, lang, 30, bottom + 48, W - 60)
    body += lg
    body.append(tx(30, ly + 26, L(lang, "数据：台湾食品营养成分资料库、USDA FoodData Central；不含调味料。部分重叠的标签省略。",
                                  "データ：台湾食品栄養成分データベース、USDA FoodData Central（調味料を除く）。重なるラベルは一部省略。"), 11, SOFT))
    title = L(lang, "常见食物营养图谱（营养素聚类图）", "身近な食品の栄養マップ（栄養素クラスター図）")
    desc = L(lang, "109 种常见食物按营养素密度做主成分分析的散点图，按 11 个营养群着色。",
             "身近な109食品を栄養素密度で主成分分析した散布図。11の栄養グループで色分け。")
    return svg_doc(W, H, body, lang, title, desc), (W, H)


# ---------------------------------------------------------------------------
# 图 2：树状图 + 热图
# ---------------------------------------------------------------------------
def heat_color(val, vmax, hue):
    t = max(0.0, min(1.0, val / vmax))
    base = {"g": (25, 135, 84), "r": (214, 69, 65), "b": (59, 110, 200)}[hue]
    r, g, b = (int(255 + (c - 255) * t) for c in base)
    return f"#{r:02x}{g:02x}{b:02x}"


def fig_heatmap(foods, X, Lk, lab, lang):
    dn = dendrogram(Lk, no_plot=True)
    leaves = dn["leaves"]
    n = len(leaves)
    rowh, top = 15, 140
    tree_w, name_w, cell = 150, 130, 44
    cols = DENS + ["fat_e", "carb_e"]
    x_tree, x_name = 20, 20 + tree_w + 8
    x_cells = x_name + name_w
    W = x_cells + cell * len(cols) + 30
    H = top + n * rowh + 90
    body = [tx(20, 40, L(lang, "食物营养素热图与聚类树", "食品の栄養素ヒートマップとクラスター樹形図"), 24, weight="bold"),
            tx(20, 66, L(lang, "颜色越深 = 每 100 kcal 提供的该营养素越多（钠为红色，越深越高）；左侧树状图把营养组成相似的食物连在一起",
                         "色が濃いほど100 kcalあたりの量が多い（ナトリウムは赤）。左の樹形図は栄養の組み立てが似た食品をつないでいます"), 12, SOFT)]
    for j, k in enumerate(cols):
        x = x_cells + j * cell + cell / 2
        body.append(tx(x, top - 10, L(lang, *NUT[k]), 11, INK, "start",
                       extra=f' transform="rotate(-50 {x:.1f} {top - 10})"'))
    # 树状图（scipy 坐标：叶子在 5,15,25…；高度 dcoord）
    hmax = max(max(d) for d in dn["dcoord"])
    for ic, dc in zip(dn["icoord"], dn["dcoord"]):
        pts = []
        for xi, di in zip(ic, dc):
            yy = top + (xi - 5) / 10 * rowh + rowh / 2
            xx = x_tree + tree_w - di / hmax * tree_w
            pts.append(f"{xx:.1f},{yy:.1f}")
        body.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#9ca3af" stroke-width="1"/>')
    vmax = [np.percentile(X[:, j], 95) for j in range(len(cols))]
    for r, i in enumerate(leaves):
        y = top + r * rowh
        c = CLUSTERS[lab[i]]
        body.append(f'<rect x="{x_name - 6}" y="{y + 2}" width="4" height="{rowh - 3}" fill="{c[2]}"/>')
        body.append(tx(x_name + 2, y + rowh - 3.5, foods[i][lang], 11))
        for j, k in enumerate(cols):
            hue = "r" if k == "sodium" else "b" if k in ("fat_e", "carb_e") else "g"
            body.append(f'<rect x="{x_cells + j * cell}" y="{y}" width="{cell - 1}" height="{rowh - 1}" '
                        f'fill="{heat_color(X[i, j], vmax[j], hue)}"/>')
    y = top + n * rowh + 30
    lg, ly = legend(CLUSTERS, lang, 20, y, W - 40, 11)
    body += lg
    body.append(tx(20, ly + 24, L(lang, "方法：营养素密度取对数后标准化，Ward 法层次聚类。数据：台湾食品营养成分资料库、USDA FoodData Central。",
                                  "方法：栄養素密度を対数変換・標準化し、Ward法で階層クラスタリング。データ：台湾食品栄養成分データベース、USDA。"), 11, SOFT))
    H = ly + 50
    title = L(lang, "109 种食物营养素热图（层次聚类）", "109食品の栄養素ヒートマップ（階層クラスタリング）")
    desc = L(lang, "按营养组成相似度排序的食物营养素热图，左侧为聚类树状图。", "栄養の組み立ての近さで並べた食品の栄養素ヒートマップと樹形図。")
    return svg_doc(W, H, body, lang, title, desc), (W, H)


# ---------------------------------------------------------------------------
# 图 3：11 个营养群的平均轮廓
# ---------------------------------------------------------------------------
def fig_profiles(foods, Z, lab, lang):
    cols_n, pw, ph = 3, 320, 250
    rows = (len(CLUSTERS) + cols_n - 1) // cols_n
    W, H = 30 + cols_n * pw + 10, 100 + rows * ph + 40
    body = [tx(30, 42, L(lang, "11 个食物营养群的营养特点", "11の食品栄養グループの特徴"), 24, weight="bold"),
            tx(30, 68, L(lang, "柱子向右 = 该群每 100 kcal 的该营养素高于 109 种食物的平均，向左 = 低于平均（标准分）",
                         "右に伸びるほど100 kcalあたりの量が109食品の平均より多く、左は少ない（標準得点）"), 12, SOFT)]
    feats = DENS
    for ci, c in enumerate(CLUSTERS):
        idx = np.where(lab == ci)[0]
        prof = Z[idx][:, :len(feats)].mean(0)
        ox, oy = 30 + (ci % cols_n) * pw, 100 + (ci // cols_n) * ph
        body.append(f'<rect x="{ox}" y="{oy}" width="{pw - 14}" height="{ph - 14}" rx="10" fill="#fafafa" stroke="{LINE}"/>')
        body.append(f'<circle cx="{ox + 16}" cy="{oy + 20}" r="6" fill="{c[2]}"/>')
        body.append(tx(ox + 28, oy + 25, L(lang, c[3], c[5]), 14, weight="bold"))
        body.append(tx(ox + 12, oy + 44, L(lang, c[4], c[6]), 11, SOFT))
        mid, scale = ox + 170, 50
        body.append(f'<line x1="{mid}" y1="{oy + 54}" x2="{mid}" y2="{oy + 54 + len(feats) * 15}" stroke="#cbd5e1"/>')
        for j, k in enumerate(feats):
            y = oy + 56 + j * 15
            v = max(-2.4, min(2.4, prof[j]))
            body.append(tx(ox + 12, y + 10, L(lang, *NUT[k]), 10.5, "#374151"))
            col = "#d64541" if k == "sodium" and v > 0 else c[2] if v > 0 else "#cbd5e1"
            x0 = mid if v >= 0 else mid + v * scale
            body.append(f'<rect x="{x0:.1f}" y="{y + 2}" width="{abs(v) * scale:.1f}" height="10" fill="{col}"/>')
        sep = "・" if lang == "ja" else "、"
        ex = L(lang, "例：", "例：")
        for n_, i in enumerate(idx):
            nxt = ex + ("" if n_ == 0 else sep) + foods[i][lang]
            if text_w(nxt, 10.5) > pw - 40:
                break
            ex = nxt
        body.append(tx(ox + 12, oy + ph - 26, ex, 10.5, SOFT))
    title = L(lang, "食物营养群特点（每 100 kcal 营养素密度）", "食品栄養グループの特徴（100 kcalあたりの栄養素密度）")
    desc = L(lang, "11 个食物营养群各营养素相对于平均水平的高低。", "11の食品グループごとの栄養素の多い・少ない。")
    return svg_doc(W, H, body, lang, title, desc), (W, H)


# ---------------------------------------------------------------------------
# 图 4：营养素之间的相关（哪些营养素常一起出现）
# ---------------------------------------------------------------------------
def fig_corr(X, lang):
    C = np.corrcoef(X[:, :len(DENS)].T)
    n, cell, lx, ty = len(DENS), 52, 140, 150
    W, H = lx + n * cell + 40, ty + n * cell + 90
    body = [tx(24, 40, L(lang, "营养素“同伴”图：哪些营养素常在同一类食物里？", "栄養素の相関図：いっしょに含まれやすい栄養素は？"), 22, weight="bold"),
            tx(24, 64, L(lang, "109 种食物每 100 kcal 营养素密度的相关系数；绿色 = 常一起高，紫色 = 此消彼长",
                         "109食品の100 kcalあたり栄養素密度の相関係数。緑＝いっしょに多い、紫＝反対の傾向"), 12, SOFT)]
    for j, k in enumerate(DENS):
        x = lx + j * cell + cell / 2
        body.append(tx(x, ty - 8, L(lang, *NUT[k]), 11, INK, "start", extra=f' transform="rotate(-45 {x:.1f} {ty - 8})"'))
        body.append(tx(lx - 8, ty + j * cell + cell / 2 + 4, L(lang, *NUT[k]), 11, INK, "end"))
    for a in range(n):
        for b in range(n):
            r = C[a, b]
            if r >= 0:
                col = heat_color(r, 1, "g")
            else:
                t = min(1, -r)
                col = f"#{int(255 - 120 * t):02x}{int(255 - 140 * t):02x}{int(255 - 40 * t):02x}"
            x, y = lx + b * cell, ty + a * cell
            body.append(f'<rect x="{x}" y="{y}" width="{cell - 2}" height="{cell - 2}" fill="{col}"/>')
            body.append(tx(x + cell / 2 - 1, y + cell / 2 + 4, f"{r:.2f}", 11, "#fff" if abs(r) > 0.6 else INK, "middle"))
    body.append(tx(24, H - 40, L(lang, "相关只说明这些营养素常出现在同一类食物里，不代表一种营养素会影响另一种的吸收。",
                                 "相関は同じ種類の食品に含まれやすいことを示すだけで、吸収に影響するという意味ではありません。"), 11, SOFT))
    title = L(lang, "食物营养素相关矩阵", "食品の栄養素相関マトリックス")
    desc = L(lang, "10 种营养素在常见食物中的相关系数矩阵。", "身近な食品における10栄養素の相関係数マトリックス。")
    return svg_doc(W, H, body, lang, title, desc), (W, H), C


# ---------------------------------------------------------------------------
# 图 5–13：每种营养素的“每份”排行
# ---------------------------------------------------------------------------
RANK_NUTS = ["protein", "fiber", "calcium", "iron", "potassium", "magnesium", "zinc", "vit_a", "vit_c"]


MIXED_DISH = set(range(13, 27))  # 饺子、包子、饭团、粽子、披萨、炒饭等复合菜品，份量差异大


def serving(f):
    return f["u"][0][1]


def single_food(f):
    """排行和“互补食物”只用单一食材：去掉复合菜品和饮料零食（含添加营养素的饮料、份量很大的拿铁等）。"""
    return f["id"] not in MIXED_DISH and f["id"] != 35 and f["g"] != "饮料零食"


def fig_rank(foods, lab, k, lang, topn=12):
    vals = [(f["vals"][k] * serving(f) / 100, i) for i, f in enumerate(foods) if single_food(f)]
    vals.sort(reverse=True)
    vals = vals[:topn]
    W, rowh, top, lw = 760, 30, 110, 250
    H = top + topn * rowh + 70
    vmax = vals[0][0]
    nm = L(lang, *NUT[k])
    body = [tx(24, 42, L(lang, f"{nm}含量最高的常见食物（每份）", f"{nm}が多い身近な食品（1回量あたり）"), 22, weight="bold"),
            tx(24, 68, L(lang, f"按常见一份的量计算；颜色表示所属营养群。参考：成人每日约 {REF[k]} {UNIT[k]}（计算用参考值）",
                         f"よく食べる1回量で計算。色は栄養グループ。参考：成人1日約{REF[k]} {UNIT[k]}（計算用の目安）"), 12, SOFT)]
    for r, (v, i) in enumerate(vals):
        f, y = foods[i], top + r * rowh
        c = CLUSTERS[lab[i]]
        body.append(tx(24, y + 19, f"{f[lang]}（{serving(f):g} g）", 13))
        bw = (W - lw - 110) * v / vmax
        body.append(f'<rect x="{lw}" y="{y + 5}" width="{bw:.1f}" height="{rowh - 10}" rx="3" fill="{c[2]}"/>')
        vs = f"{v:.1f}" if v < 10 else f"{v:.0f}"
        body.append(tx(lw + bw + 8, y + 19, f"{vs} {UNIT[k]}", 12, "#374151"))
    body.append(tx(24, H - 36, L(lang, "数据：台湾食品营养成分资料库、USDA FoodData Central；维生素A为视黄醇活性当量（RAE）。",
                                 "データ：台湾食品栄養成分データベース、USDA FoodData Central。ビタミンAはレチノール活性当量（RAE）。"), 11, SOFT))
    title = L(lang, f"{nm}含量排行：常见食物每份含量", f"{nm}が多い食品ランキング（1回量あたり）")
    desc = L(lang, f"常见食物每份{nm}含量前 {topn} 名的条形图。", f"身近な食品の1回量あたりの{nm}量・上位{topn}の棒グラフ。")
    return svg_doc(W, H, body, lang, title, desc), (W, H), vals


# 图片的 alt 和说明文字：(简体 alt, 简体说明, 日语 alt, 日语说明)；繁体由页面输出时自动转换
FIG_TEXT = {
    "food-nutrient-map": (
        "常见食物营养图谱：109 种食物按营养素密度做主成分分析的散点图，按 11 个营养群着色，蔬菜在右、肉鱼蛋奶在下、水果主食在上",
        "常见食物营养图谱。点越近，每 100 kcal 的营养组成越相似；右侧是微量营养素密度高的蔬菜，左侧是以提供能量为主的精制主食、油和甜饮料。",
        "身近な食品の栄養マップ：109食品を栄養素密度で主成分分析し、11の栄養グループで色分けした散布図",
        "身近な食品の栄養マップ。点が近いほど100 kcalあたりの栄養の組み立てが似ています。右は野菜、左はエネルギー中心の精製穀物・油・甘い飲み物。"),
    "food-nutrient-heatmap": (
        "109 种常见食物的营养素热图与层次聚类树状图，显示蛋白质、膳食纤维、钾、钙、铁、镁、锌、维生素A、维生素C、钠的密度",
        "营养素热图：每一行是一种食物，颜色越深表示每 100 kcal 提供该营养素越多；左侧树状图把营养组成相似的食物连在一起。",
        "109食品の栄養素ヒートマップと階層クラスタリングの樹形図（たんぱく質・食物繊維・カリウム・カルシウム・鉄・マグネシウム・亜鉛・ビタミンA・C・ナトリウム）",
        "栄養素ヒートマップ。1行が1食品で、色が濃いほど100 kcalあたりの量が多いことを示します。左の樹形図は栄養が似た食品をつないでいます。"),
    "food-cluster-profiles": (
        "11 个食物营养群的营养素特点条形图：浅色蔬菜、橙黄色蔬菜、深绿叶菜、海藻、全谷豆菇、豆制品坚果、肉鱼虾、蛋奶、水果、面点、精制主食",
        "11 个食物营养群各自擅长和缺少的营养素。同一群的食物可以互相替换，不同群的食物则在营养上互补。",
        "11の食品栄養グループの特徴を示す棒グラフ：淡色野菜、緑黄色野菜、葉物、海藻、全粒穀物、大豆・ナッツ、肉・魚、卵・乳、果物、粉もの、精製穀物",
        "11の食品グループが得意な栄養素と少ない栄養素。同じグループの食品は置き換えやすく、違うグループの食品は栄養を補い合います。"),
    "nutrient-correlation": (
        "食物营养素相关矩阵：钾、镁、铁、膳食纤维常在同一类食物中一起出现，蛋白质与锌相关",
        "营养素相关矩阵。钾、镁、铁和膳食纤维常常“结伴”出现在蔬菜、豆类里；蛋白质和锌则一起出现在肉类里。",
        "栄養素の相関マトリックス：カリウム・マグネシウム・鉄・食物繊維は同じ食品に含まれやすく、たんぱく質と亜鉛も相関",
        "栄養素の相関マトリックス。カリウム・マグネシウム・鉄・食物繊維は野菜や豆にいっしょに含まれやすく、たんぱく質と亜鉛は肉にそろって含まれます。"),
}
for _k, (_h, _j) in {
    "protein": ("蛋白质", "たんぱく質"), "fiber": ("膳食纤维", "食物繊維"), "calcium": ("钙", "カルシウム"),
    "iron": ("铁", "鉄"), "potassium": ("钾", "カリウム"), "magnesium": ("镁", "マグネシウム"),
    "zinc": ("锌", "亜鉛"), "vit_a": ("维生素A", "ビタミンA"), "vit_c": ("维生素C", "ビタミンC"),
}.items():
    FIG_TEXT[f"top-foods-{_k.replace('_', '-')}"] = (
        f"{_h}含量最高的常见食物排行条形图（每份）",
        f"常见食物每份{_h}含量前 12 名（单一食材，按常见一份计算），颜色表示所属营养群。",
        f"{_j}が多い身近な食品ランキング（1回量あたり）の棒グラフ",
        f"1回量あたりの{_j}が多い身近な食品の上位12（単品食材）。色は栄養グループを表します。")


# ---------------------------------------------------------------------------
def main():
    foods = load_foods()
    X, Z = features(foods)
    Lk = linkage(Z, "ward")
    raw = fcluster(Lk, len(CLUSTERS), "maxclust") - 1
    # 用代表食物把聚类编号对应到 CLUSTERS 的顺序
    pos = {f["id"]: i for i, f in enumerate(foods)}
    mapping = {}
    for ci, c in enumerate(CLUSTERS):
        rc = raw[pos[c[1]]]
        assert rc not in mapping, f"{c[0]} 与 {CLUSTERS[mapping[rc]][0]} 落在同一群"
        mapping[rc] = ci
    assert len(mapping) == len(CLUSTERS)
    lab = np.array([mapping[r] for r in raw])

    meta = {}
    report = {}

    def save(key, lang, svg):
        out = IMG_DIR / f"{key}{'' if lang == 'hans' else '.' + lang}.svg"
        out.write_text(svg, encoding="utf-8", newline="\n")

    for lang in LANGS:
        svg, wh = fig_map(foods, Z, lab, lang)
        save("food-nutrient-map", lang, svg)
        meta["food-nutrient-map"] = wh
        svg, wh = fig_heatmap(foods, X, Lk, lab, lang)
        save("food-nutrient-heatmap", lang, svg)
        meta["food-nutrient-heatmap"] = wh
        svg, wh = fig_profiles(foods, Z, lab, lang)
        save("food-cluster-profiles", lang, svg)
        meta["food-cluster-profiles"] = wh
        svg, wh, C = fig_corr(X, lang)
        save("nutrient-correlation", lang, svg)
        meta["nutrient-correlation"] = wh
        for k in RANK_NUTS:
            svg, wh, vals = fig_rank(foods, lab, k, lang)
            save(f"top-foods-{k.replace('_', '-')}", lang, svg)
            meta[f"top-foods-{k.replace('_', '-')}"] = wh
            if lang == "hans":
                report[k] = [(foods[i]["hans"], round(v, 1)) for v, i in vals]

    # 相似 / 互补食物
    good = [k for k in DENS if k != "sodium"]
    gidx = [DENS.index(k) for k in good]
    D = np.sqrt(((Z[:, None, :] - Z[None, :, :]) ** 2).sum(-1))
    low_density = {CLUSTERS.index(c) for c in CLUSTERS if c[0] in ("refined", "bun-noodle")}
    items = []
    for i, f in enumerate(foods):
        sim = [int(j) for j in np.argsort(D[i]) if j != i][:5]
        zi = Z[i, gidx]
        strong = [good[j] for j in np.argsort(-zi)[:3] if zi[j] > 0.3]
        weak = [good[j] for j in np.argsort(zi)[:3]]
        wj = [DENS.index(k) for k in weak]
        # 互补：按“一份能补上多少”打分（每种弱项最多计 40% 参考量），每个营养群只取最好的一种
        cand = []
        for j, g in enumerate(foods):
            if lab[j] == lab[i] or lab[j] in low_density or g["id"] in (74, 75) or not single_food(g):
                continue
            sc = sum(min(0.4, g["vals"][k] * serving(g) / 100 / REF[k]) for k in weak)
            cand.append((sc, j))
        comp, seen = [], set()
        for _, j in sorted(cand, reverse=True):
            if lab[j] not in seen:
                seen.add(lab[j])
                comp.append(int(j))
            if len(comp) == 4:
                break
        items.append({"id": f["id"], "c": int(lab[i]),
                      "n": {"hans": f["hans"], "hant": f["hant"], "ja": f["ja"]},
                      "s": sim, "p": comp, "hi": strong, "lo": weak})
    data = {
        "nutrients": {k: {"hans": NUT[k][0], "hant": to_hant_text(NUT[k][0]), "ja": NUT[k][1]} for k in good},
        "clusters": [{"key": c[0], "color": c[2],
                      "hans": c[3], "hant": to_hant_text(c[3]), "ja": c[5],
                      "note": {"hans": c[4], "hant": to_hant_text(c[4]), "ja": c[6]}} for c in CLUSTERS],
        "foods": items,
    }
    (ROOT / "static" / "data").mkdir(exist_ok=True)
    (ROOT / "static" / "data" / "food-map.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8", newline="\n")
    figs = {}
    for k, (w, h) in meta.items():
        alt, cap, alt_ja, cap_ja = FIG_TEXT[k]
        figs[k] = {"w": w, "h": h, "alt": alt, "caption": cap, "ja": {"alt": alt_ja, "caption": cap_ja}}
    (ROOT / "data" / "food_map_figures.json").write_text(
        json.dumps(figs, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

    # 写文章时用的摘要
    print("clusters:")
    for ci, c in enumerate(CLUSTERS):
        print(" ", c[3], "|", " ".join(foods[i]["hans"] for i in np.where(lab == ci)[0]))
    print("corr (>0.5):")
    for a in range(len(DENS)):
        for b in range(a + 1, len(DENS)):
            if abs(C[a, b]) > 0.45:
                print("  ", DENS[a], DENS[b], round(C[a, b], 2))
    print("top:")
    for k, v in report.items():
        print(" ", k, v[:8])
    for nm in ("白米饭", "鸡胸肉", "香蕉", "西兰花", "全脂牛奶", "老豆腐"):
        it = next(x for x in items if x["n"]["hans"] == nm)
        print(" ", nm, "sim:", [foods[j]["hans"] for j in it["s"]], "comp:", [foods[j]["hans"] for j in it["p"]], it["hi"], it["lo"])


if __name__ == "__main__":
    main()
