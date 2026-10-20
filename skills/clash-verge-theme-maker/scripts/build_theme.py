#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从 spec.json 生成 Clash Verge Rev 主题：3 档 CSS + 预览图 + README。

用法：
    python build_theme.py --spec spec.json [--out themes] [--no-preview]
                          [--chrome PATH] [--root-readme README.md]
                          [--wall-budget 260000] [--quiet]

spec.json 最小示例（只给 src + 主色，其余自动推导）：
{
  "out": "themes",
  "themes": [
    {"src": "壁纸/我的猫.jpg", "zh": "午后橘猫", "en": "CatNap",
     "slug": "cat-nap", "primary": "#C08040"}
  ]
}

完整字段见 references/design-guide.md 的「spec.json 字段表」。

依赖：Pillow（壁纸压缩必装）；Google Chrome（预览图可选，缺失时自动跳过）。
"""
import argparse
import base64
import colorsys
import json
import os
import subprocess
import sys

# ---------------------------------------------------------------- 档位基线
# 与 docs/css-classnames.md 第四节一致，改动前先读那份文档。
TIERS = {
    "ultra": dict(card=".08", nav=".20", bgalpha=".08", blur=0),
    "high": dict(card=".08", nav=".22", bgalpha=".18", blur=10),
    "normal": dict(card=".20", nav=".30", bgalpha=".18", blur=18),
}

# ---------------------------------------------------------------- 色彩工具


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(rgb):
    return "#%02X%02X%02X" % tuple(int(round(c)) for c in rgb)


def rgba(rgb, a):
    return "rgba(%d,%d,%d,%s)" % (int(rgb[0]), int(rgb[1]), int(rgb[2]), a)


def rgb_s(rgb):
    return "%d,%d,%d" % tuple(int(round(c)) for c in rgb)


def mix(rgb, other, t):
    return tuple(c + (o - c) * t for c, o in zip(rgb, other))


def _hls(rgb):
    return colorsys.rgb_to_hls(*[c / 255.0 for c in rgb])


def _rgb(h, l, s):
    return tuple(c * 255 for c in colorsys.hls_to_rgb(h, l, s))


def derive_light(primary_rgb):
    """亮部：同色相提亮，用于渐变端点 / 焦点描边 / 进度条。"""
    h, l, s = _hls(primary_rgb)
    return _rgb(h, min(0.78, l + 0.20), min(1.0, s + 0.05))


def derive_text(primary_rgb):
    """正文色：取主色 Hue 的极暗版，比纯黑更贴合壁纸。"""
    h, l, s = _hls(primary_rgb)
    return _rgb(h, min(0.16, l * 0.40), min(0.35, s))


def derive_shadow(primary_rgb):
    """阴影色：卡片投影与选中态光晕，比主色暗但保留色相。"""
    h, l, s = _hls(primary_rgb)
    return _rgb(h, 0.26, s)


def derive_depth(primary_rgb):
    """文字按钮用的深一档主色。"""
    return mix(primary_rgb, (0, 0, 0), 0.22)


# ---------------------------------------------------------------- CSS 模板
CSS_TEMPLATE = r""":root {
  --primary-main: {PRIMARY} !important;
  --text-primary: {TEXT} !important;
  --selection-color: {SEL} !important;
  --scroller-color: rgba({TEXTRGB},.45) !important;
  --background-color: transparent !important;
  --background-color-alpha: rgba({PRIMARYRGB},{BGALPHA}) !important;
  --divider-color: rgba(255,255,255,.30) !important;
  --border-radius: 12px !important;
}

html, body, #root {
  background: url("data:image/jpeg;base64,{WALL}") center center / cover no-repeat !important;
  background-attachment: fixed !important;
  position: relative;
  z-index: 0;
  overflow-x: hidden;
}
::selection { background: rgba({PRIMARYRGB},.35) !important; color: {SEL} !important; }

.layout,
.layout-content,
.layout-content__left,
.layout-content__right,
.the-bar,
.the-content,
.base-page,
.base-container,
.base-page > header,
.base-page .base-container > section,
.base-content {
  background: transparent !important;
  box-shadow: none !important;
}

.layout-content__left {
  background: rgba(255,255,255,{NAV}) !important;
{BACKDROP}  border-right: 1px solid rgba(255,255,255,.35) !important;
}
.the-logo, .the-traffic { background: transparent !important; box-shadow: none !important; }

.MuiPaper-root, .MuiCard-root,
.MuiDialog-paper, .MuiDrawer-paper,
.MuiMenu-paper, .MuiPopover-paper,
.MuiAccordion-root, .MuiAccordionSummary-root, .MuiAccordionDetails-root,
.MuiAlert-root{PAPER_LIST},
.MuiSnackbar-root .MuiPaper-root {
  background: rgba(255,255,255,{CARD}) !important;
{BACKDROP}  border: 1px solid rgba(255,255,255,.55) !important;
  border-radius: 12px !important;
  box-shadow: 0 6px 18px rgba({SHADOWRGB},.14) !important;
  color: rgba({TEXTRGB},.95) !important;
}
.MuiPaper-root .MuiPaper-root,
.MuiPaper-root .MuiAccordion-root { border-color: rgba(255,255,255,.30) !important; box-shadow: none !important; }
{LIST_RULE}
.base-page .MuiGrid-root > .MuiBox-root,
.base-page .MuiGrid2-root > .MuiBox-root {
  background: rgba(255,255,255,{CARD}) !important;
{BACKDROP}  border: 1px solid rgba(255,255,255,.35) !important;
}

.base-page .MuiBox-root[aria-selected] {
  background: rgba(255,255,255,{CARD}) !important;
{BACKDROP}  border: 1px solid rgba(255,255,255,.35) !important;
}

.the-menu .MuiListItemButton-root {
  background: transparent !important;
  color: rgba({TEXTRGB},.95) !important;
  border-radius: 12px !important;
}
.the-menu .MuiListItemButton-root:hover {
  background: rgba(255,255,255,.55) !important;
}
.the-menu .MuiListItemButton-root.Mui-selected,
.the-menu .MuiListItemButton-root.Mui-selected:hover {
  background: linear-gradient(135deg, rgba({PRIMARYRGB},.92), rgba({LIGHTRGB},.92)) !important;
  color: #fff !important;
  box-shadow: 0 4px 14px rgba({SHADOWRGB},.30) !important;
}
.the-menu .MuiListItemButton-root.Mui-selected * { color: #fff !important; text-shadow: none !important; }
.the-menu .MuiListItemIcon-root { color: inherit !important; }
.MuiListItemText-root .MuiTypography-root { color: inherit !important; text-shadow: 0 1px 2px rgba(255,255,255,.6); }

.MuiOutlinedInput-root, .MuiFilledInput-root,
.MuiInputBase-root, .MuiInput-root,
.MuiSelect-select, .MuiOutlinedInput-input, .MuiInputBase-input {
  background: rgba(255,255,255,.62) !important;
  color: rgba({TEXTRGB},.95) !important;
  border-radius: 8px !important;
}
.MuiOutlinedInput-notchedOutline { border-color: rgba(255,255,255,.85) !important; }
.Mui-focused .MuiOutlinedInput-notchedOutline { border-color: {LIGHT} !important; }

.MuiTypography-root, .MuiFormLabel-root, .MuiInputLabel-root,
.MuiFormControlLabel-label, .MuiFormHelperText-root,
label, h1, h2, h3, h4, h5, h6, p, span, td, th, a {
  color: rgba({TEXTRGB},.95) !important;
  text-shadow: 0 1px 2px rgba(255,255,255,.65);
}
.MuiSvgIcon-root { color: inherit !important; }

.MuiButton-contained, .MuiButton-outlined,
button.MuiButton-root:not(.MuiIconButton-root):not(.MuiTab-root) {
  background: linear-gradient(135deg, rgba({PRIMARYRGB},.95), rgba({LIGHTRGB},.95)) !important;
  border: 1px solid rgba(255,255,255,.65) !important;
  color: #fff !important;
  border-radius: 10px !important;
  text-shadow: none !important;
}
.MuiButton-text { background: transparent !important; color: rgba({DEPTHRGB},.95) !important; }
.MuiIconButton-root { background: transparent !important; color: rgba({TEXTRGB},.92) !important; }

.MuiListItemButton-root, .MuiListItem-root,
.MuiTableCell-root, tr, td, th {
  background: transparent !important;
  color: rgba({TEXTRGB},.95) !important;
  border-color: rgba(255,255,255,.35) !important;
}
.MuiListItemButton-root:hover, tr:hover { background: rgba(255,255,255,.5) !important; }
.Mui-selected, [aria-selected="true"] {
  background: rgba({PRIMARYRGB},.92) !important; color: #fff !important;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.55) !important;
}
.Mui-selected *, [aria-selected="true"] * { color: #fff !important; text-shadow: none !important; }
.MuiChip-root { background: rgba(255,255,255,.45) !important; color: rgba({TEXTRGB},.95) !important; }
.MuiLinearProgress-root, [class*="progress"] { background: rgba(255,255,255,.4) !important; }
.MuiLinearProgress-bar, [class*="progressBar"], [class*="progress-bar"] {
  background: rgba({LIGHTRGB},.95) !important;
}

.MuiSwitch-track { background: rgba({TEXTRGB},.35) !important; }
.MuiSwitch-thumb { background: rgba(255,255,255,.95) !important; }
.Mui-checked + .MuiSwitch-track { background: rgba({LIGHTRGB},.90) !important; }
.MuiTab-root { color: rgba({TEXTRGB},.80) !important; background: transparent !important; text-shadow: none !important; }
.MuiTab-root.Mui-selected { color: #fff !important; background: rgba({PRIMARYRGB},.90) !important; border-radius: 10px !important; }
.MuiTabs-indicator { background: {LIGHT} !important; height: 3px !important; border-radius: 3px !important; }
a { color: {PRIMARY} !important; }
.MuiTooltip-tooltip { background: rgba({TEXTRGB},.94) !important; color: #fff !important; }
.MuiCheckbox-colorPrimary.Mui-checked, .MuiRadio-colorPrimary.Mui-checked { color: {PRIMARY} !important; }

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: rgba({TEXTRGB},.12) !important; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,.6) !important; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba({LIGHTRGB},.90) !important; }
"""

# ---------------------------------------------------------------- 预览 mock
BASE_CSS = r"""
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;font-family:"Microsoft YaHei","PingFang SC","Segoe UI",system-ui,sans-serif;font-size:13px}
#root{height:100%;display:flex;flex-direction:column;overflow:hidden}
.titlebar{height:38px;flex:0 0 38px;display:flex;align-items:center;gap:7px;padding:0 14px}
.dot{width:11px;height:11px;border-radius:50%;display:inline-block}
.dot.r{background:#FF5F57}.dot.y{background:#FEBC2E}.dot.g{background:#28C840}
.titlebar .ttl{margin-left:8px;font-size:12px;letter-spacing:.2px;opacity:.75}
.layout{flex:1 1 auto;min-height:0;display:flex}
.layout-content{flex:1 1 auto;display:flex;min-height:0}
.layout-content__left{width:196px;flex:0 0 196px;display:flex;flex-direction:column;padding:6px 10px 10px}
.the-logo{display:flex;align-items:center;gap:9px;padding:8px 6px 14px}
.logo-mark{width:30px;height:30px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:15px;color:#fff;flex:0 0 auto}
.logo-txt b{display:block;font-size:12.5px;font-weight:600;line-height:1.25}
.logo-txt small{display:block;font-size:9.5px;opacity:.7;line-height:1.4}
.the-menu{list-style:none;flex:1 1 auto;display:flex;flex-direction:column;gap:2px}
.MuiListItemButton-root{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:10px;cursor:pointer;font-size:12.5px}
.MuiListItemIcon-root{width:16px;flex:0 0 16px;display:flex;justify-content:center;opacity:.9}
.MuiListItemText-root{flex:1 1 auto;display:flex;align-items:center;justify-content:space-between}
.MuiListItemText-root small{font-size:9.5px;opacity:.55;letter-spacing:.2px}
.the-traffic{padding:8px 10px 2px;display:flex;flex-direction:column;gap:3px;font-size:10px;opacity:.75}
.the-traffic .row{display:flex;justify-content:space-between}
.layout-content__right{flex:1 1 auto;min-width:0;display:flex;flex-direction:column}
.the-bar{height:14px;flex:0 0 14px}
.base-page{flex:1 1 auto;min-height:0;padding:2px 22px 18px;display:flex;flex-direction:column;gap:12px;overflow:hidden}
.base-page>header{display:flex;align-items:center;justify-content:space-between;padding:2px 0 4px}
.base-page>header h1{font-size:19px;font-weight:600;letter-spacing:.5px}
.base-page>header .actions{display:flex;gap:8px}
.MuiButton-root{font-size:12px;padding:6px 13px;border-radius:9px;border:none;cursor:pointer;font-family:inherit}
.base-container{flex:1 1 auto;min-height:0}
.base-container>section{height:100%}
.base-content{display:flex;flex-direction:column;gap:12px;height:100%}
.MuiGrid2-root{display:flex;gap:12px}
.MuiGrid2-root.cards>.MuiBox-root{flex:1 1 0;min-width:0;padding:11px 13px 10px;border-radius:12px}
.MuiGrid2-root.panels>.MuiBox-root{flex:1 1 0;min-width:0;padding:12px 15px 6px;border-radius:12px}
.MuiGrid2-root.single{flex:1 1 auto;min-height:0}
.MuiGrid2-root.single>.MuiBox-root{flex:1 1 0;min-width:0;padding:12px 15px 10px;border-radius:12px;overflow:hidden}
.card-hd{display:flex;align-items:center;gap:7px;font-size:12.5px;font-weight:600;margin-bottom:5px}
.card-hd i{width:7px;height:7px;border-radius:50%;display:inline-block;flex:0 0 7px}
.card-url{font-size:10.5px;opacity:.75;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:8px}
.card-ft{display:flex;align-items:center;gap:6px}
.chip{font-size:9.5px;padding:2px 7px;border-radius:6px;white-space:nowrap}
.lat{font-size:9.5px;padding:2px 7px;border-radius:6px;white-space:nowrap;flex:0 0 auto}
.panel-hd{display:flex;align-items:center;gap:7px;font-size:12.5px;font-weight:600;padding-bottom:9px}
.rowset{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:7px 0}
.rowset .lt b{display:block;font-size:12px;font-weight:500;line-height:1.35}
.rowset .lt small{display:block;font-size:9.5px;opacity:.65;line-height:1.45}
.sw{position:relative;width:34px;height:19px;flex:0 0 34px;display:block}
.MuiSwitch-track{position:absolute;inset:0;border-radius:10px;display:block}
.sw-base{position:absolute;inset:0;border-radius:10px;display:block}
.MuiSwitch-thumb{position:absolute;top:2px;left:2px;width:15px;height:15px;border-radius:50%;display:block}
.sw.on .MuiSwitch-thumb{left:17px}
.bar{height:3px;border-radius:2px;overflow:hidden;margin-top:9px}
.bar>i{display:block;height:100%;width:62%;border-radius:2px}
"""

HTML = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<style>__BASE__</style>
<style>__THEME__</style>
</head><body>
<div id="root">
  <div class="titlebar"><span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
    <span class="ttl">Clash Verge Rev</span></div>
  <div class="layout windows">
    <div class="layout-content">
      <div class="layout-content__left">
        <div class="the-logo">
          <span class="logo-mark">__MARK__</span>
          <span class="logo-txt"><b>Clash Verge</b><small>v2.x · __ZH__</small></span>
        </div>
        <ul class="MuiList-root the-menu">__NAV__</ul>
        <div class="the-traffic">
          <div class="row"><span>__UP__</span><span>__DOWN__</span></div>
          <div class="row"><span>__TODAY__</span><span>__TOTAL__</span></div>
        </div>
      </div>
      <div class="layout-content__right">
        <div class="the-bar"></div>
        <div class="base-page">
          <header>
            <h1>__PAGETITLE__</h1>
            <div class="actions">
              <button class="MuiButton-root MuiButton-outlined">__IMPORTTXT__</button>
              <button class="MuiButton-root MuiButton-contained MuiButton-containedPrimary">__UPDATETXT__</button>
            </div>
          </header>
          <div class="base-container"><section><div class="base-content">
            <div class="MuiGrid2-root cards">__CARDS__</div>
            <div class="MuiGrid2-root panels">
              <div class="MuiBox-root"><div class="panel-hd">__PANEL1__</div>__ROWS1__</div>
              <div class="MuiBox-root"><div class="panel-hd">__PANEL2__</div>__ROWS2__<div class="bar"><i></i></div></div>
            </div>
            <div class="MuiGrid2-root single">
              <div class="MuiBox-root"><div class="panel-hd">__PANEL3__</div>__ROWS3__</div>
            </div>
          </div></section></div>
        </div>
      </div>
    </div>
  </div>
</div>
</body></html>
"""


def _card(dot, title, url, date, state):
    return ('<div class="MuiBox-root" aria-selected="false">'
            '<div class="card-hd"><i style="background:%s"></i>%s</div>'
            '<div class="card-url">%s</div>'
            '<div class="card-ft"><span class="chip">%s</span><span class="chip">%s</span></div>'
            '</div>' % (dot, title, url, date, state))


def _sw(on, primary):
    cls = "sw on" if on else "sw"
    return ('<span class="MuiSwitch-root %s"><span class="sw-base Mui-checked"></span>'
            '<span class="MuiSwitch-track"></span><span class="MuiSwitch-thumb"></span></span>' % cls)


def _row(title, sub, on, primary):
    return ('<div class="rowset"><div class="lt"><b>%s</b><small>%s</small></div>%s</div>'
            % (title, sub, _sw(on, primary)))


def _node(title, sub, lat):
    return ('<div class="rowset"><div class="lt"><b>%s</b><small>%s</small></div>'
            '<span class="lat">%s</span></div>' % (title, sub, lat))


def _nav(icon, label, en, sel=False):
    cls = "MuiListItemButton-root Mui-selected" if sel else "MuiListItemButton-root"
    return ('<li class="%s"><span class="MuiListItemIcon-root">%s</span>'
            '<span class="MuiListItemText-root"><span class="MuiTypography-root">%s</span>'
            '<small>%s</small></span></li>' % (cls, icon, label, en))


def build_preview_html(theme_css, t):
    """拼出预览页。文字可用 spec 里的 ui 字段覆盖，默认中文界面。"""
    ui = t.get("ui", {})
    cards = "".join(ui.get("cards") or [
        _card("#3FB950", "节点机场 A", "https://sub.example.com/api/v1/client/subscribe", "2026-12-01 到期", "已启用"),
        _card("#D29922", "备用线路 B", "https://backup.example.net/clash/meta", "2026-10-15 到期", "手动管理"),
        _card("#1F6FEB", "自建节点 C", "https://home.example.org/link/abcd", "长期有效", "自动更新"),
    ])
    navs = "".join(_nav(i, l, e, sel=(n == 1)) for n, (i, l, e) in enumerate([
        ("⚡", ui.get("nav1", "代理"), "Proxies"),
        ("☁", ui.get("nav2", "订阅"), "Profiles"),
        ("🔗", ui.get("nav3", "连接"), "Connections"),
        ("📐", ui.get("nav4", "规则"), "Rules"),
        ("🗂", ui.get("nav5", "日志"), "Logs"),
        ("⚙", ui.get("nav6", "设置"), "Settings"),
    ]))
    p = t["primary"]
    rows1 = "".join([
        _row("系统代理", "开启后接管系统流量", True, p),
        _row("Tun 模式", "虚拟网卡全局接管", False, p),
        _row("开机自启", "随系统启动", True, p),
    ])
    rows2 = "".join([
        _row("主题语言", "跟随主题设置", True, p),
        _row("自动更新", "订阅定时拉取", True, p),
    ])
    rows3 = "".join([
        _node("节点选择", "自动 · 延迟最低", "48 ms"),
        _node("香港 IPLC 01", "hk01.example.com:443", "42 ms"),
        _node("日本 东京 02", "jp02.example.com:443", "76 ms"),
        _node("新加坡 03", "sg03.example.com:443", "112 ms"),
        _node("美国 洛杉矶 04", "us04.example.com:443", "168 ms"),
    ])
    return (HTML.replace("__BASE__", BASE_CSS).replace("__THEME__", theme_css)
            .replace("__MARK__", ui.get("mark", "◆"))
            .replace("__ZH__", "%s %s" % (t["zh"], t["en"]))
            .replace("__NAV__", navs).replace("__CARDS__", cards)
            .replace("__UP__", "↑ 2.4 MB/s").replace("__DOWN__", "↓ 18.6 MB/s")
            .replace("__TODAY__", "今日 1.2 GB").replace("__TOTAL__", "总计 34.8 GB")
            .replace("__PAGETITLE__", ui.get("page_title", "订阅"))
            .replace("__IMPORTTXT__", ui.get("import_btn", "导入订阅"))
            .replace("__UPDATETXT__", ui.get("update_btn", "更新全部"))
            .replace("__PANEL1__", ui.get("panel1", "⚙ 系统设置"))
            .replace("__PANEL2__", ui.get("panel2", "🎨 外观"))
            .replace("__PANEL3__", ui.get("panel3", "⚡ 代理组"))
            .replace("__ROWS1__", rows1).replace("__ROWS2__", rows2).replace("__ROWS3__", rows3))


# ---------------------------------------------------------------- README
TIER_TABLE = """| 文件 | 风格 |
|---|---|
| [`clash-verge-{S}-ultra.css`](clash-verge-{S}-ultra.css) | **纯透明无磨砂**：卡片只是一层薄雾白纱 + 细描边，透过去直接看到清晰壁纸，全屏无一处模糊 |
| [`clash-verge-{S}-high.css`](clash-verge-{S}-high.css) | 高透明磨砂：卡片内轻微虚化（blur 10px），轮廓通透 |
| [`clash-verge-{S}-normal.css`](clash-verge-{S}-normal.css) | 正常磨砂（推荐）：磨砂 18px，通透与可读平衡 |"""


def build_readme(t):
    pal = t.get("palette") or [
        ("主色 / 选中态 / 按钮", t["primary"], "取自壁纸主体色块"),
        ("主色亮部（渐变端点）", t["light"], "同色相提亮"),
        ("正文文字", t["text"], "画面最深暗部"),
    ]
    pal_rows = "\n".join("| %s | `%s` | %s |" % (a, b, c) for a, b, c in pal)
    return ("""# {ZH} · {EN}

> {DESC}三档透明度任选，整段粘贴即用。

![preview](previews/normal.jpg)

## 档位 · Tiers

{TT}

> 三档文件均含内嵌壁纸，单文件约 100–300 KB（视壁纸细节而定）。

## 预览 · Previews

| Ultra（纯透明） | High（高透明磨砂） | Normal（正常磨砂） |
|:---:|:---:|:---:|
| ![ultra](previews/ultra.jpg) | ![high](previews/high.jpg) | ![normal](previews/normal.jpg) |

## 配色 · Palette

| 用途 | 色值 | 来源 |
|---|---|---|
{PAL}

## 设计说明 · Notes

{NOTE}

三档的白雾参数沿用全主题统一基线：ultra 卡片 `.08`／侧栏 `.20`，high 卡片 `.08`／侧栏 `.22`，normal 卡片 `.20`／侧栏 `.30`。换主题不换档位手感，切主题时透明度不用重新适应。

## 安装 · Install

1. 打开 Clash Verge Rev → **设置** → **外观**
2. 找到 **自定义 CSS** 输入框
3. 打开本目录下任意一档 CSS，**全选复制，整段粘贴**
4. 界面立即生效；换档位直接替换粘贴内容

## 换壁纸 · Change Wallpaper

壁纸以 base64 内嵌在 CSS 中（离线可用、无外链依赖）：

1. 准备一张 1600px 宽左右的 JPG
2. 转成 base64（`base64 wall.jpg` / [在线工具](https://base64.guru/converter/encode/image)）
3. 替换 CSS 中 `html, body, #root {{ background: url("data:image/jpeg;base64,……")` 里那一长串 base64 即可

## 特性 · Features

- **三档任选**：纯透明 / 高透明 / 正常磨砂，一段 CSS 粘贴即用，随时切换
- **壁纸清晰**：{ZH}壁纸全程锐利显示（ultra 档全屏无一处模糊）
- **{PALSRC}主色**：`{P}` 取自画面本身，与壁纸同源不打架
- **换壁纸方便**：替换一段 base64 就能换成任意喜欢的壁纸
- **离线可用**：单文件 CSS，壁纸内嵌，复制粘贴就能用

## 兼容性 · Compatibility

针对 **Clash Verge Rev**（基于官方 `dev` 分支前端源码类名核对）。若客户端大版本升级后个别区块样式丢失，F12 查看该元素类名提 issue 即可。
""".replace("{ZH}", t["zh"]).replace("{EN}", t["en"]).replace("{DESC}", t.get("desc", ""))
    .replace("{TT}", TIER_TABLE.replace("{S}", t["slug"])).replace("{PAL}", pal_rows)
    .replace("{NOTE}", t.get("note", "主色取自壁纸主体色块，亮部同色相提亮，文字取画面最深暗部。"))
    .replace("{PALSRC}", pal[0][2]).replace("{P}", t["primary"]))


# ---------------------------------------------------------------- 主流程


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


def prepare_wallpaper(src, out_dir, budget, slug):
    """压缩成内嵌壁纸：优先降分辨率保质量，返回 jpg 路径。"""
    from PIL import Image
    im = Image.open(src).convert("RGB")
    w, h = im.size
    path = os.path.join(out_dir, slug + ".jpg")
    best = None
    done = False
    for nw in (1600, 1500, 1400, 1300, 1200):
        r = im.resize((nw, round(h * nw / w)), Image.LANCZOS)
        for q in (82, 80, 78, 76, 74, 72, 70):
            r.save(path, "JPEG", quality=q, optimize=True, progressive=True)
            n = os.path.getsize(path)
            b64 = (n + 2) // 3 * 4
            best = (nw, q, n, b64)
            if b64 <= budget:
                done = True
                break
        if done:
            break
    return path, best, done


def build_css(t, tier, wall_b64):
    spec = TIERS[tier]
    px = spec["blur"]
    if px:
        bd = ("  backdrop-filter: blur(%dpx) saturate(150%%) !important;\n"
              "  -webkit-backdrop-filter: blur(%dpx) saturate(150%%) !important;\n" % (px, px))
        paper_list = ", .MuiList-root"
        list_rule = ""
    else:
        bd, paper_list = "", ""
        list_rule = "\n.MuiList-root { background: transparent !important; }"
    P = hex2rgb(t["primary"])
    L = hex2rgb(t["light"])
    X = hex2rgb(t["text"])
    S = t["shadow"]
    D = derive_depth(P)
    SEL = mix(P, (255, 255, 255), 0.88)
    return (CSS_TEMPLATE
            .replace("{PRIMARY}", t["primary"]).replace("{LIGHT}", t["light"])
            .replace("{TEXT}", t["text"])
            .replace("{PRIMARYRGB}", rgb_s(P)).replace("{LIGHTRGB}", rgb_s(L))
            .replace("{TEXTRGB}", rgb_s(X)).replace("{SHADOWRGB}", rgb_s(S))
            .replace("{DEPTHRGB}", rgb_s(D)).replace("{SEL}", rgb2hex(SEL))
            .replace("{NAV}", spec["nav"]).replace("{CARD}", spec["card"])
            .replace("{BGALPHA}", spec["bgalpha"])
            .replace("{BACKDROP}", bd).replace("{PAPER_LIST}", paper_list)
            .replace("{LIST_RULE}", list_rule).replace("{WALL}", wall_b64))


def normalize(t, out_root):
    """补齐缺失字段：light / text / shadow / slug / emoji / palette。"""
    if "primary" not in t:
        raise SystemExit("主题 %r 缺少 primary（主色）" % t.get("zh", t.get("src")))
    P = hex2rgb(t["primary"])
    t["light"] = t.get("light") or rgb2hex(derive_light(P))
    t["text"] = t.get("text") or rgb2hex(derive_text(P))
    t["shadow"] = tuple(t.get("shadow") or [int(round(c)) for c in derive_shadow(P)])
    t["slug"] = (t.get("slug") or (t.get("en", "theme").lower().replace(" ", "-")))
    t["emoji"] = t.get("emoji", "🎨")
    t["zh"] = t.get("zh") or t["slug"]
    t["en"] = t.get("en") or t["slug"]
    t.setdefault("desc", "")
    t.setdefault("note", "")
    return t


def main():
    ap = argparse.ArgumentParser(description="生成 Clash Verge Rev 主题（3 档 CSS + 预览 + README）")
    ap.add_argument("--spec", required=True, help="spec.json 路径")
    ap.add_argument("--out", default=None, help="主题输出目录，默认取 spec 的 out 字段或 themes")
    ap.add_argument("--no-preview", action="store_true", help="跳过预览图渲染")
    ap.add_argument("--chrome", default=None, help="Chrome 可执行文件路径")
    ap.add_argument("--root-readme", default=None, help="把新主题追加到该根 README")
    ap.add_argument("--wall-budget", type=int, default=260000, help="内嵌壁纸 base64 字符上限")
    ap.add_argument("--preview-format", choices=["jpg", "png"], default="jpg",
                    help="预览图格式，默认 jpg（q95，肉眼无损且体积只有真彩 PNG 的 1/3）")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    spec = json.load(open(args.spec, encoding="utf-8"))
    # 必须绝对路径：Chrome 只接受绝对的 file:// URL，相对路径会静默截图失败
    out_root = os.path.abspath(args.out or spec.get("out", "themes"))
    spec_dir = os.path.dirname(os.path.abspath(args.spec))
    themes = [normalize(t, out_root) for t in spec["themes"]]
    tmp = os.path.abspath(os.path.join(out_root, ".build_tmp"))
    os.makedirs(tmp, exist_ok=True)

    chrome = None if args.no_preview else find_chrome(args.chrome)

    for t in themes:
        src = t["src"]
        if not os.path.exists(src) and os.path.exists(os.path.join(spec_dir, src)):
            src = os.path.join(spec_dir, src)   # 相对路径按 spec.json 所在目录解析
        # 1. 重命名源图（可选）
        if t.get("new_name") and os.path.exists(src):
            d = os.path.dirname(os.path.abspath(src))
            newp = os.path.join(d, t["new_name"] + os.path.splitext(src)[1])
            if os.path.abspath(newp) != os.path.abspath(src):
                if os.path.exists(newp):
                    os.remove(newp)
                os.rename(src, newp)
                src = newp
            if not args.quiet:
                print("[rename] %s -> %s" % (t["src"], os.path.basename(newp)))
        if not os.path.exists(src):
            raise SystemExit("找不到壁纸：%s" % src)

        # 2. 壁纸压缩
        wpath, info, ok = prepare_wallpaper(src, tmp, args.wall_budget, t["slug"])
        wall_b64 = base64.b64encode(open(wpath, "rb").read()).decode()
        if not args.quiet:
            print("[wall]   %-14s %dx%d q=%d %.0fKB b64=%d%s" %
                  (t["slug"], info[0], round(info[0] * 0.5625), info[1], info[2] / 1024,
                   info[3], "" if ok else " [超预算]"))

        # 3. 三档 CSS
        d = os.path.join(out_root, t["slug"])
        os.makedirs(os.path.join(d, "previews"), exist_ok=True)
        for tier in ("ultra", "high", "normal"):
            css = build_css(t, tier, wall_b64)
            with open(os.path.join(d, "clash-verge-%s-%s.css" % (t["slug"], tier)),
                      "w", encoding="utf-8", newline="\n") as f:
                f.write(css)
            if not args.quiet:
                print("[css]    %-14s %-7s %.0fKB" % (t["slug"], tier, len(css.encode()) / 1024))

        # 4. 预览
        if chrome:
            for tier in ("ultra", "high", "normal"):
                hp = os.path.join(tmp, "%s-%s.html" % (t["slug"], tier))
                with open(hp, "w", encoding="utf-8") as f:
                    f.write(build_preview_html(
                        open(os.path.join(d, "clash-verge-%s-%s.css" % (t["slug"], tier)),
                             encoding="utf-8").read(), t))
                # Chrome 只能截 PNG；默认转成 JPEG q95（4:4:4）落盘——
                # 真彩 PNG 单张可达 1.5MB，而 q95 JPEG 在 44–48dB（肉眼无损）只要 1/3 体积。
                # 千万别用 256 色量化代替：渐变和磨砂层会出现明显抖动噪点与色带。
                ext = "png" if args.preview_format == "png" else "jpg"
                shot = os.path.join(tmp, "%s-%s-shot.png" % (t["slug"], tier))
                out_img = os.path.join(d, "previews", tier + "." + ext)
                r = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                                    "--force-device-scale-factor=1", "--window-size=1200,700",
                                    "--screenshot=" + shot, "file:///" + hp.replace("\\", "/")],
                                   capture_output=True)
                if os.path.exists(shot):
                    if ext == "jpg":
                        from PIL import Image
                        Image.open(shot).convert("RGB").save(
                            out_img, "JPEG", quality=95, optimize=True, subsampling=0)
                        os.remove(shot)
                    else:
                        os.replace(shot, out_img)
                if not args.quiet:
                    if os.path.exists(out_img):
                        print("[preview] %-13s %-7s OK  %.0fKB" %
                              (t["slug"], tier, os.path.getsize(out_img) / 1024))
                    else:
                        print("[preview] %-13s %-7s FAIL %s" % (
                            t["slug"], tier, r.stderr.decode("utf-8", "ignore")[:120]))
        elif not args.no_preview:
            print("[preview] 未找到 Chrome，跳过（可用 --chrome 指定，或 --no-preview）")

        # 5. README
        with open(os.path.join(d, "README.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(build_readme(t))
        if not args.quiet:
            print("[readme] %s/README.md" % t["slug"])

    # 6. 根 README
    if args.root_readme:
        append_root_readme(args.root_readme, themes, out_root)

    if not args.quiet:
        print("\n完成：%d 套主题 × 3 档 → %s/" % (len(themes), out_root))
        print("下一步：python scripts/verify_theme.py --dir %s/<slug> 逐档校验" % out_root)


def append_root_readme(path, themes, out_root):
    """在第一个「## 安装」之前插入主题小节；没有就追加到末尾。"""
    if not os.path.exists(path):
        print("[root] 根 README 不存在：%s" % path)
        return
    s = open(path, encoding="utf-8").read()
    # 链接必须相对 README 所在目录，否则提交后路径失效
    rel = os.path.relpath(out_root, os.path.dirname(os.path.abspath(path))).replace("\\", "/")
    blocks = []
    for t in themes:
        blocks.append("\n## {e} {zh} {en}\n\n{d}\n\n![{zh}]({o}/{s}/previews/normal.jpg)\n\n"
                      "**[查看主题与下载 →]({o}/{s}/)**\n".format(
                          e=t["emoji"], zh=t["zh"], en=t["en"], d=t.get("desc", ""),
                          s=t["slug"], o=rel))
    add = "".join(blocks)
    marker = s.find("\n## ")
    idx = None
    for line_start in range(len(s)):
        if s.startswith("\n## ", line_start) and "安装" in s[line_start:line_start + 40]:
            idx = line_start
            break
    pos = idx if idx is not None else (marker if marker >= 0 else len(s))
    if idx is None and marker >= 0:
        pos = len(s.rstrip())
        add = "\n" + add
    s = s[:pos] + add + s[pos:]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print("[root] 已更新 %s（+%d 节）" % (path, len(themes)))


if __name__ == "__main__":
    main()
