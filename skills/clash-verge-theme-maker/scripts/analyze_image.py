#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""分析壁纸，给出配色候选与风险提示（供命名/取色决策用）。

用法：
    python analyze_image.py 图片1.jpg 图片2.jpg ... [--json]

输出：尺寸、主色板（占比）、亮度对比度、主色候选（按「面积 × 饱和度」排序）、
      以及踩坑提示（过暗 / 过亮 / 低对比 / 冷色占比）。

依赖：Pillow（pip install Pillow）
"""
import colorsys
import json
import sys


def load(path, max_side=400):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    small = im.copy()
    small.thumbnail((max_side, max_side))
    return im, small, (w, h)


def palette(small, n=8):
    from PIL import Image
    q = small.quantize(colors=n, method=Image.MEDIANCUT).convert("RGB")
    w, h = q.size
    cnt = q.getcolors(w * h) or []
    cnt.sort(reverse=True)
    total = sum(c for c, _ in cnt) or 1
    out = []
    for c, (r, g, b) in cnt[:n]:
        hl, ls, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        out.append(dict(hex="#%02X%02X%02X" % (r, g, b), share=round(100 * c / total, 1),
                        l=round(ls, 3), s=round(s, 3), hue=round(hl * 360)))
    return out


def brightness(small):
    from PIL import ImageStat, Image
    g = small.convert("L")
    st = ImageStat.Stat(g)
    return dict(mean=round(st.mean[0], 1), stddev=round(st.stddev[0], 1))


def candidates(pal):
    """主色候选：占比 ≥3%、明度 0.18–0.72、按 饱和度×占比 排序。"""
    ok = [c for c in pal if c["share"] >= 3 and 0.18 <= c["l"] <= 0.72]
    ok.sort(key=lambda c: c["s"] * c["share"], reverse=True)
    return ok[:4]


def analyze(path):
    im, small, size = load(path)
    pal = palette(small)
    br = brightness(small)
    cand = candidates(pal)
    tips = []
    if br["mean"] < 90:
        tips.append("画面整体偏暗（mean=%.0f）。默认深色文字 + 白色 text-shadow 可能压不住，"
                    "建议把卡片白雾提到 .12–.16，或改用浅色文字版式。" % br["mean"])
    if br["mean"] > 200:
        tips.append("画面接近全白（mean=%.0f）。卡片轮廓会几乎看不见，主色必须够深（明度 ≤0.45）。" % br["mean"])
    if br["stddev"] < 35:
        tips.append("对比度低（stddev=%.0f）。低饱和主色容易和壁纸糊在一起，建议主色饱和度 ≥0.25。" % br["stddev"])
    if not cand:
        tips.append("没有落在明度 0.18–0.72 且占比 ≥3% 的色块，主色需要人工指定（常见於纯黑发/纯白墙画面）。")
    ar = round(size[0] / size[1], 2)
    if not 1.2 <= ar <= 2.1:
        tips.append("宽高比 %.2f 偏离常见屏幕（1.3–1.9），cover 裁切后主体可能被切掉，建议先裁成 16:9。" % ar)
    return dict(path=path, size="%dx%d" % size, aspect=ar, brightness=br,
                palette=pal, primary_candidates=cand, tips=tips)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    if not args:
        print(__doc__)
        return
    res = [analyze(p) for p in args]
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return
    for r in res:
        print("=" * 60)
        print("%s   %s (比例 %s)" % (r["path"], r["size"], r["aspect"]))
        print("亮度 mean=%.0f  stddev=%.0f" % (r["brightness"]["mean"], r["brightness"]["stddev"]))
        print("主色板：")
        for c in r["palette"]:
            print("  %s  %5.1f%%  L=%.2f S=%.2f H=%d" % (c["hex"], c["share"], c["l"], c["s"], c["hue"]))
        print("主色候选：")
        for c in r["primary_candidates"]:
            print("  %s  %5.1f%%  L=%.2f S=%.2f" % (c["hex"], c["share"], c["l"], c["s"]))
        for t in r["tips"]:
            print("⚠ " + t)


if __name__ == "__main__":
    main()
