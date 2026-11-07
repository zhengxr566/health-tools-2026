"""
繁体中文（台湾正体）版本：/zh-hant/...

做法：
- HantPrefixMiddleware 把 /zh-hant 前缀挂到 SCRIPT_NAME 上，路由仍按原路径匹配，
  所以简体和繁体共用同一套路由、模板和计算逻辑，内容永远同步。
- 页面渲染完后，convert_html() 用 OpenCC s2twp（简体 → 台湾正体并转换常用词）
  转成繁体，再套用 TW_FIXES 补充台湾用语，并把站内链接改成 /zh-hant/ 开头。

想调整某个词的繁体写法：在 TW_FIXES 里加一行即可。
"""

import re

from opencc import OpenCC

HANT_PREFIX = "/zh-hant"
ENV_KEY = "calmy.lang"

_cc = OpenCC("s2twp")

# OpenCC 之后再替换的台湾常用说法（左边是 OpenCC 输出，右边是台湾用语）
TW_FIXES = [
    ("酸奶", "優格"),
    ("西蘭花", "青花菜"),
    ("紅薯", "地瓜"),
    ("土豆", "馬鈴薯"),
    ("外賣", "外送"),
    ("計算器", "計算機"),
    ("薯片", "洋芋片"),
    ("方便麵", "泡麵"),
    ("掛麵", "乾麵條"),
    ("鍛煉", "鍛鍊"),
    ("自行車", "腳踏車"),
    ("塑料", "塑膠"),
    ("軟尺", "皮尺"),
    ("激素", "荷爾蒙"),
    ("帶娃", "帶小孩"),
    ("刷手機", "滑手機"),
    ("臺灣", "台灣"),
]


class HantPrefixMiddleware:
    """把 /zh-hant/... 的请求交给原应用处理，并标记语言。"""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if path == HANT_PREFIX or path.startswith(HANT_PREFIX + "/"):
            environ["SCRIPT_NAME"] = environ.get("SCRIPT_NAME", "") + HANT_PREFIX
            environ["PATH_INFO"] = path[len(HANT_PREFIX):] or "/"
            environ[ENV_KEY] = "hant"
        return self.wsgi_app(environ, start_response)


# 站内相对链接：href="/xxx"、action="/xxx"、JS 里的 path: "/xxx"
_LINK_RE = re.compile(r'(\b(?:href|action)=")/(?!/|static/|zh-hant(?:/|"))')
_JS_PATH_RE = re.compile(r'(\bpath:\s*")/(?!/|static/|zh-hant(?:/|"))')


def to_hant_text(text: str) -> str:
    out = _cc.convert(text)
    for src, dst in TW_FIXES:
        out = out.replace(src, dst)
    return out


_NOHANT_RE = re.compile(r"(<!--nohant-->.*?<!--/nohant-->)", re.S)


def convert_html(html: str) -> str:
    # <!--nohant-->...<!--/nohant--> 之间的内容保持原样（例如“简体”切换链接）
    parts = _NOHANT_RE.split(html)
    out = "".join(p if p.startswith("<!--nohant-->") else to_hant_text(p) for p in parts)
    out = _LINK_RE.sub(r"\1" + HANT_PREFIX + "/", out)
    out = _JS_PATH_RE.sub(r"\1" + HANT_PREFIX + "/", out)
    out = out.replace('"inLanguage": "zh-CN"', '"inLanguage": "zh-Hant"')
    # 静态文件两种语言共用 /static/，避免重复缓存
    out = out.replace(HANT_PREFIX + "/static/", "/static/")
    return out
