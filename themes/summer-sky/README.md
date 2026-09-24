# 夏日晴空 · SummerGlass

> 夏日晴空 × 玻璃拟态主题：壁纸清晰锐利、天空蓝点缀。三档透明度任选，整段粘贴即用。

![preview](previews/normal.png)

## 档位 · Tiers

| 文件 | 风格 | 参数 |
|---|---|---|
| [`clash-verge-summer-sky-ultra.css`](clash-verge-summer-sky-ultra.css) | **纯透明无磨砂**（壁纸最清晰）：卡片只是一层薄雾白纱 + 细描边，透过去直接看到清晰壁纸，无任何模糊 | 白纱 8% · 侧栏 20% |
| [`clash-verge-summer-sky-high.css`](clash-verge-summer-sky-high.css) | 高透明磨砂：卡片内轻微虚化，轮廓通透 | 白底 12% · blur 14px |
| [`clash-verge-summer-sky-normal.css`](clash-verge-summer-sky-normal.css) | 正常磨砂（推荐）：通透与可读平衡 | 白底 20% · blur 18px |

- **ultra** 适合"壁纸就是主角"：全屏无一处模糊，文字靠深藏青 + 白微光保证可读
- **high / normal** 是磨砂玻璃档：卡片区域虚化、玻璃外壁纸依然清晰

设计原型全页预览（7 页）见 [`previews/pages/`](previews/pages/)。

## 安装 · Install

1. 打开 Clash Verge Rev → **设置** → **外观**
2. 找到 **自定义 CSS** 输入框
3. 打开本目录下任意一档 CSS，**全选复制，整段粘贴**
4. 界面立即生效；换档位直接替换粘贴内容

## 换壁纸 · Change Wallpaper

壁纸以 base64 内嵌在 CSS 中（离线可用、无外链依赖）：

1. 准备一张 1600px 宽左右的 JPG（建议 ≤ 200KB）
2. 转成 base64（`base64 wall.jpg` / [在线工具](https://base64.guru/converter/encode/image)）
3. 替换 CSS 中 `html, body, #root { background: url("data:image/jpeg;base64,……")` 里那一长串 base64 即可

## 特性 · Features

- **壁纸清晰优先**：壁纸只挂在根容器（`html/body/#root`），固定 `cover` 锐利显示，不随滚动
- **真实类名稳定覆盖**：选择器依据 Clash Verge Rev 官方源码（`layout.scss` / `page.scss` / `settings.tsx` / `profile-box.tsx`）的真实稳定类名（`.layout-content__left` / `.base-page` / `.MuiPaper-root` / `.MuiBox-root[aria-selected]` 等）+ `!important`，不依赖随构建变化的 `css-xxxxxx` 哈希类，客户端小版本升级不易失效
- **覆盖面全**：侧栏、导航选中天空蓝渐变药丸、订阅卡片 / 设置面板 / Merge & Script 卡、输入框浅底深字、深藏青正文保证可读
- **零依赖**：单文件 CSS，壁纸内嵌，离线可用

## 兼容性 · Compatibility

针对 **Clash Verge Rev**（基于官方 `dev` 分支前端源码类名核对）。若客户端大版本升级后个别区块样式丢失，F12 查看该元素类名提 issue 即可。
