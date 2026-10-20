#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""逐档校验生成结果：用 Chrome 读 computed style，确认选择器真的命中。

用法：
    python verify_theme.py --dir themes/white-campus
    python verify_theme.py --dir themes/white-campus --chrome "C:/.../chrome.exe"

检查项（每项不通过都会点名）：
  · 侧栏 / 卡片白雾 α 是否等于该档位基线（ultra .20/.08，high .22/.08，normal .30/.20）
  · ultra 档是否完全没有 backdrop-filter；high/normal 是否分别是 blur(10px)/blur(18px)
  · 选中导航项与按钮是否为渐变
  · 是否出现横向/纵向溢出、卡片是否坍塌

退出码：全部通过 0，有失败 1。
"""
import argparse
import html as _html
import json
import os
import re
import subprocess
import sys

EXPECT = {
    "ultra": dict(nav=0.20, card=0.08, blur=None),
    "high": dict(nav=0.22, card=0.08, blur=10),
    "normal": dict(nav=0.30, card=0.20, blur=18),
}

PROBE_JS = """
<script>
function cs(el){return el?getComputedStyle(el):null;}
function box(el){if(!el)return null;var r=el.getBoundingClientRect();
 return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};}
var o={};
o.navBg=cs(document.querySelector('.layout-content__left')).backgroundColor;
o.navBlur=cs(document.querySelector('.layout-content__left')).backdropFilter||'none';
var card=document.querySelector('.base-page .MuiGrid2-root > .MuiBox-root');
o.cardBg=cs(card).backgroundColor;
o.cardBlur=cs(card).backdropFilter||'none';
o.selBg=cs(document.querySelector('.the-menu .MuiListItemButton-root.Mui-selected')).backgroundImage;
o.btnBg=cs(document.querySelector('.MuiButton-contained')).backgroundImage;
o.geo={card:box(card),sel:box(document.querySelector('.the-menu .MuiListItemButton-root.Mui-selected'))};
o.overflow={sh:document.documentElement.scrollHeight,ch:document.documentElement.clientHeight,
            sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth};
var pre=document.createElement('pre');pre.id='probe';
pre.textContent='@@PROBE@@'+JSON.stringify(o)+'@@END@@';
document.body.appendChild(pre);
</script>
"""


def find_chrome(explicit=None):
    if explicit:
        return explicit if os.path.exists(explicit) else None
    env = os.environ.get("CHROME_PATH")
    if env and os.path.exists(env):
        return env
    cands = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium",
    ]
    return next((c for c in cands if os.path.exists(c)), None)


def read_styles(chrome, html_path):
    r = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--window-size=1200,700", "--virtual-time-budget=1200",
                        "--dump-dom", "file:///" + html_path.replace("\\", "/")],
                       capture_output=True)
    dom = r.stdout.decode("utf-8", "ignore")
    m = re.search(r'<pre id="probe">@@PROBE@@(.*?)@@END@@', dom, re.S)
    if not m:
        return None
    return json.loads(_html.unescape(m.group(1)))


def alpha(c):
    try:
        return float(c.split(",")[-1].strip(" )"))
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="主题目录（含 clash-verge-<slug>-*.css）")
    ap.add_argument("--chrome", default=None)
    args = ap.parse_args()

    theme_dir = os.path.abspath(args.dir.rstrip("/\\"))   # 绝对路径，file:// URL 才有效
    slug = os.path.basename(theme_dir)
    css_files = {t: os.path.join(theme_dir, "clash-verge-%s-%s.css" % (slug, t))
                 for t in ("ultra", "high", "normal")}
    missing = [t for t, p in css_files.items() if not os.path.exists(p)]
    if missing:
        print("缺少 CSS：%s（目录应为 themes/<slug>/，文件命名 clash-verge-<slug>-<tier>.css）" % missing)
        return 1

    chrome = find_chrome(args.chrome)
    if not chrome:
        print("未找到 Chrome，无法校验。用 --chrome 指定路径。")
        return 1

    # preview HTML 需要 build_theme 的 mock；这里内联一份最小版，避免依赖
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from build_theme import build_preview_html
    except ImportError:
        print("build_theme.py 不可用，无法构造 mock 页面")
        return 1

    fake = dict(zh=slug, en=slug, primary="#000000", light="#000000", text="#000000",
                shadow=(0, 0, 0))
    tmp = os.path.join(theme_dir, ".verify_tmp")
    os.makedirs(tmp, exist_ok=True)

    failed = 0
    for tier in ("ultra", "high", "normal"):
        css = open(css_files[tier], encoding="utf-8").read()
        hp = os.path.join(tmp, "verify-%s.html" % tier)
        with open(hp, "w", encoding="utf-8") as f:
            f.write(build_preview_html(css, fake).replace("</body>", PROBE_JS + "</body>"))
        o = read_styles(chrome, hp)
        if not o:
            print("%-8s FAIL  取不到 computed style" % tier)
            failed += 1
            continue
        exp = EXPECT[tier]
        issues = []
        na, ca = alpha(o["navBg"]), alpha(o["cardBg"])
        if na is None or abs(na - exp["nav"]) > 1e-6:
            issues.append("侧栏α=%s 期望%s" % (o["navBg"], exp["nav"]))
        if ca is None or abs(ca - exp["card"]) > 1e-6:
            issues.append("卡片α=%s 期望%s" % (o["cardBg"], exp["card"]))
        nb, cb = o["navBlur"], o["cardBlur"]
        if exp["blur"] is None:
            if "blur" in nb:
                issues.append("侧栏不该有模糊：%s" % nb)
            if "blur" in cb:
                issues.append("卡片不该有模糊：%s" % cb)
        else:
            want = "blur(%dpx)" % exp["blur"]
            if want not in nb.replace(" ", ""):
                issues.append("侧栏模糊=%s 期望%s" % (nb, want))
            if want not in cb.replace(" ", ""):
                issues.append("卡片模糊=%s 期望%s" % (cb, want))
        if "gradient" not in o["selBg"]:
            issues.append("选中导航不是渐变：%s" % o["selBg"])
        if "gradient" not in o["btnBg"]:
            issues.append("按钮不是渐变：%s" % o["btnBg"])
        ov = o["overflow"]
        if ov["sh"] > ov["ch"] + 1 or ov["sw"] > ov["cw"] + 1:
            issues.append("页面溢出 %s" % ov)
        g = o["geo"]
        if not g["card"] or g["card"]["w"] < 150 or g["card"]["h"] < 40:
            issues.append("卡片坍塌 %s" % g["card"])
        if issues:
            failed += 1
            print("%-8s FAIL  %s" % (tier, " | ".join(issues)))
        else:
            print("%-8s PASS" % tier)

    print("\n%s：%d/3 档通过" % (slug, 3 - failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
