"""
健康指南文章的元数据。

新增一篇文章：
1. 在 ARTICLES 里加一项（slug 唯一，用英文短横线）
2. 新建 templates/guide/<slug>.html，写 {% extends "article.html" %} 和 {% block article_body %}
3. 正文里的 <h2 id="..."> 要和 toc 里的 id 对应
"""

AUTHOR = {
    "name": "Zooey",
    "url": "/about",
    "bio": "独立网页开发者，关注健康生活与生活工具开发。",
}

ARTICLES = [
    {
        "slug": "10000-steps-km",
        "title": "一万步是多少公里？按身高换算距离、时间和热量（附对照表）",
        "h1": "一万步是多少公里？按身高换算距离、时间和热量",
        "description": "一万步大约是 6.2–7.7 公里，取决于身高与步幅。本文给出按身高的步数距离对照表、走一万步需要多久、消耗多少热量，以及手机计步不准的原因。",
        "category": "运动与步数",
        "published": "2026-11-07",
        "updated": "2026-11-07",
        "read_minutes": 6,
        "toc": [
            ("answer", "先说结论"),
            ("stride", "步幅怎么估算"),
            ("table", "按身高的一万步距离对照表"),
            ("time", "走一万步要多久"),
            ("kcal", "走一万步消耗多少热量"),
            ("accuracy", "为什么手机和手表的数字不一样"),
            ("faq", "常见问题"),
        ],
        "faq": [
            ("一万步大约是多少公里？",
             "按常用的“步幅 ≈ 身高 × 0.41”估算，身高 150–185 cm 的成年人走一万步约为 6.2–7.7 公里，身高 160–175 cm 的人大多在 6.6–7.3 公里之间。"),
            ("一公里大约多少步？",
             "身高 155 cm 约 1,560 步，165 cm 约 1,460 步，175 cm 约 1,380 步。走得越快步幅通常越大，每公里步数会更少。"),
            ("走一万步需要多长时间？",
             "以常见的每分钟约 100 步计算，大约 100 分钟；慢走（每分钟约 80 步）约 2 小时，快走（每分钟约 130 步）约 77 分钟。"),
            ("走一万步能消耗多少热量？",
             "以中等步速、约 3.5 MET 估算，体重 60 kg 约 350 kcal、70 kg 约 410 kcal（含基础代谢的总消耗）。只算“额外”多消耗的部分约为这个数字的七成。"),
        ],
        "sources": [
            "步幅估算采用常用经验系数：男性 ≈ 身高 × 0.415，女性 ≈ 身高 × 0.413（与本站步数工具一致）。",
            "Ainsworth BE, et al. 2011 Compendium of Physical Activities. Med Sci Sports Exerc, 2011.（步行 MET 值）",
            "Tudor-Locke C, et al. Walking cadence (steps/min) and intensity in 21–40 year olds: CADENCE-adults. IJBNPA, 2019.（每分钟约 100 步对应中等强度）",
        ],
        "related_tools": ["/steps-distance", "/steps-time", "/steps", "/step-goal"],
        "related_articles": ["daily-steps-health", "sleep-cycle-90-minutes"],
    },
    {
        "slug": "daily-steps-health",
        "title": "一天走多少步才健康？一万步的由来和研究给出的答案",
        "h1": "一天走多少步才健康？研究给出的答案",
        "description": "一万步并不是科学标准。大型研究显示，60 岁以下约 8,000–10,000 步、60 岁以上约 6,000–8,000 步时健康收益趋于平稳。本文整理主要研究结论，并给出循序渐进增加步数的方法。",
        "category": "运动与步数",
        "published": "2026-11-07",
        "updated": "2026-11-07",
        "read_minutes": 7,
        "toc": [
            ("answer", "先说结论"),
            ("origin", "“一万步”是怎么来的"),
            ("research", "研究怎么说"),
            ("intensity", "步数之外：走多快也重要"),
            ("plan", "怎样把步数加上去"),
            ("faq", "常见问题"),
        ],
        "faq": [
            ("每天一定要走一万步吗？",
             "不一定。一万步最早来自 1960 年代日本计步器的宣传。综合多项研究，60 岁以下成年人约 8,000–10,000 步、60 岁以上约 6,000–8,000 步时，健康收益已接近平台期。"),
            ("每天走 4,000 步有用吗？",
             "有用。多项研究发现，从很低的步数（例如 2,000–3,000 步）增加到 4,000 步左右，与健康风险下降相关。对久坐的人来说，先多走起来比直接追求一万步更重要。"),
            ("走得快比走得多更重要吗？",
             "两者都有关系。研究发现，在总步数相同的情况下，包含更多较快步行（例如每分钟 100 步以上）的人健康指标往往更好。"),
            ("怎么增加每天的步数？",
             "建议以当前日均步数为基础，每 1–2 周增加 1,000–2,000 步，例如饭后散步 10–15 分钟、提前一站下车、用走楼梯代替电梯。"),
        ],
        "sources": [
            "Hatano Y. Use of the pedometer for promoting daily walking exercise. ICHPER Journal, 1993.（“一万步”的由来）",
            "Paluch AE, et al. Daily steps and all-cause mortality: a meta-analysis of 15 international cohorts. Lancet Public Health, 2022.",
            "Lee IM, et al. Association of step volume and intensity with all-cause mortality in older women. JAMA Intern Med, 2019.",
            "Saint-Maurice PF, et al. Association of daily step count and step intensity with mortality among US adults. JAMA, 2020.",
            "del Pozo Cruz B, et al. Prospective associations of daily step counts and intensity with cancer and cardiovascular disease incidence and mortality and all-cause mortality. JAMA Intern Med, 2022.",
            "World Health Organization. WHO guidelines on physical activity and sedentary behaviour, 2020.",
        ],
        "related_tools": ["/step-goal", "/steps", "/activity-level", "/steps-distance"],
        "related_articles": ["10000-steps-km", "sleep-cycle-90-minutes"],
    },
    {
        "slug": "sleep-cycle-90-minutes",
        "title": "睡眠周期 90 分钟是真的吗？几点睡、几点起更清醒（附作息表）",
        "h1": "睡眠周期 90 分钟是真的吗？几点睡、几点起更清醒",
        "description": "一个睡眠周期平均约 90 分钟，但每个人、每个周期都不完全一样。本文解释睡眠周期的组成、为什么在深睡中醒来会昏沉，并给出按起床时间倒推的入睡时间表和更实用的作息建议。",
        "category": "睡眠",
        "published": "2026-11-07",
        "updated": "2026-11-07",
        "read_minutes": 7,
        "toc": [
            ("answer", "先说结论"),
            ("stages", "一个睡眠周期里发生了什么"),
            ("inertia", "为什么有时醒来特别昏沉"),
            ("table", "按起床时间倒推的入睡时间表"),
            ("hours", "睡多久才够"),
            ("tips", "比“算周期”更重要的事"),
            ("faq", "常见问题"),
        ],
        "faq": [
            ("睡眠周期一定是 90 分钟吗？",
             "不一定。90 分钟是平均值，常见范围约 70–120 分钟，而且同一晚不同周期的长度和组成也会变化，所以按 90 分钟推算只能作为参考。"),
            ("想 6 点半起床，几点睡比较好？",
             "如果按 90 分钟一个周期、入睡约需 15 分钟计算，可以在 22:45 上床（约 7.5 小时睡眠），或 21:15 上床（约 9 小时）。00:15 上床只有约 6 小时，长期来说偏少。"),
            ("成年人每天要睡多久？",
             "美国国家睡眠基金会建议 18–64 岁成年人每晚 7–9 小时，65 岁以上 7–8 小时。美国睡眠医学会也建议成年人规律地每晚睡 7 小时以上。"),
            ("午睡睡多久比较好？",
             "如果只是想恢复精神，10–20 分钟的短午睡通常较少出现醒后昏沉；时间充裕时也可以睡满约 90 分钟的完整周期。午睡太晚或太长可能影响夜间入睡。"),
        ],
        "sources": [
            "Hirshkowitz M, et al. National Sleep Foundation's sleep time duration recommendations. Sleep Health, 2015.",
            "Watson NF, et al. Recommended amount of sleep for a healthy adult: AASM and SRS joint consensus statement. Sleep, 2015.",
            "Carskadon MA, Dement WC. Normal human sleep: an overview. In: Principles and Practice of Sleep Medicine.",
            "Tassi P, Muzet A. Sleep inertia. Sleep Medicine Reviews, 2000.",
        ],
        "related_tools": ["/sleep", "/sleep-bedtime", "/sleep-wake-time", "/sleep-need", "/nap-time"],
        "related_articles": ["daily-steps-health", "10000-steps-km"],
    },
]

ARTICLES_BY_SLUG = {a["slug"]: a for a in ARTICLES}
