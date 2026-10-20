# 灯宵夏祭 · LanternFest

> 夏日祭灯笼串 × 蓝紫黄昏，浴衣少女插画，主色取灯笼的暖橘。三档透明度任选，整段粘贴即用。

![preview](previews/normal.png)

## 档位 · Tiers

| 文件 | 风格 |
|---|---|
| [`clash-verge-lantern-fest-ultra.css`](clash-verge-lantern-fest-ultra.css) | **纯透明无磨砂**：卡片只是一层薄雾白纱 + 细描边，透过去直接看到清晰壁纸，全屏无一处模糊 |
| [`clash-verge-lantern-fest-high.css`](clash-verge-lantern-fest-high.css) | 高透明磨砂：卡片内轻微虚化（blur 10px），轮廓通透 |
| [`clash-verge-lantern-fest-normal.css`](clash-verge-lantern-fest-normal.css) | 正常磨砂（推荐）：磨砂 18px，通透与可读平衡 |

> 三档文件均含内嵌壁纸，单文件约 90–260 KB（视壁纸细节而定）。

## 预览 · Previews

| Ultra（纯透明） | High（高透明磨砂） | Normal（正常磨砂） |
|:---:|:---:|:---:|
| ![ultra](previews/ultra.png) | ![high](previews/high.png) | ![normal](previews/normal.png) |

## 配色 · Palette

| 用途 | 色值 | 来源 |
|---|---|---|
| 主色 / 选中态 / 按钮 | `#CF6A22` | 纸灯笼暖橘 |
| 主色亮部（渐变端点） | `#F0A24D` | 灯芯高光 |
| 正文文字 | `#2A1F28` | 暮色暗紫黑 |
| 备选主色 | `#4A5C9E` | 夜空蓝（未启用） |

## 设计说明 · Notes

黄昏蓝紫与灯笼暖橘天然互补，主色取橘、背景留蓝紫，冷暖对撞最出彩。

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
3. 替换 CSS 中 `html, body, #root { background: url("data:image/jpeg;base64,……")` 里那一长串 base64 即可

## 特性 · Features

- **三档任选**：纯透明 / 高透明 / 正常磨砂，一段 CSS 粘贴即用，随时切换
- **壁纸清晰**：灯宵夏祭壁纸全程锐利显示（ultra 档全屏无一处模糊）
- **纸灯笼暖橘主色**：`#CF6A22` 取自画面本身，与壁纸同源不打架
- **换壁纸方便**：替换一段 base64 就能换成任意喜欢的壁纸
- **离线可用**：单文件 CSS，壁纸内嵌，复制粘贴就能用

## 兼容性 · Compatibility

针对 **Clash Verge Rev**（基于官方 `dev` 分支前端源码类名核对）。若客户端大版本升级后个别区块样式丢失，F12 查看该元素类名提 issue 即可。
