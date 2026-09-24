# 夏日晴空 · SummerGlass

> 夏日晴空 × 磨砂玻璃拟态主题：壁纸清晰锐利、卡片磨砂通透、天空蓝点缀。两档透明度任选，整段粘贴即用。

![preview](previews/normal.png)

## 预览 · Previews

| 高透明 High | 正常 Normal（推荐） |
|:---:|:---:|
| 壁纸最透，卡片近乎隐形 | 通透与可读平衡 |
| ![high](previews/high.png) | ![normal](previews/normal.png) |

设计原型全页预览（7 页）见 [`previews/pages/`](previews/pages/)。

## 安装 · Install

1. 打开 Clash Verge Rev → **设置** → **外观**
2. 找到 **自定义 CSS** 输入框
3. 打开本目录下任意一档 CSS，**全选复制，整段粘贴**
4. 界面立即生效

| 文件 | 效果 |
|---|---|
| [`clash-verge-summer-sky-high.css`](clash-verge-summer-sky-high.css) | 高透明：卡片白底 12% · blur 14px，壁纸最清晰 |
| [`clash-verge-summer-sky-normal.css`](clash-verge-summer-sky-normal.css) | 正常（推荐）：白底 20% · blur 18px |

## 换壁纸 · Change Wallpaper

壁纸以 base64 内嵌在 CSS 中（离线可用、无外链依赖）：

1. 准备一张 1600px 宽左右的 JPG（建议 ≤ 200KB）
2. 转成 base64（`base64 wall.jpg` / [在线工具](https://base64.guru/converter/encode/image)）
3. 替换 CSS 中 `html, body, #root { background: url("data:image/jpeg;base64,……")` 里那一长串 base64 即可

## 特性 · Features

- **壁纸清晰优先**：壁纸只挂在根容器（`html/body/#root`），固定 `cover` 锐利显示，不随滚动；卡片靠 `backdrop-filter` 磨砂透出背景
- **真实类名稳定覆盖**：选择器依据 Clash Verge Rev 官方源码（`layout.scss` / `page.scss` / `settings.tsx` / `profile-box.tsx`）的真实稳定类名（`.layout-content__left` / `.base-page` / `.MuiPaper-root` / `.MuiBox-root[aria-selected]` 等）+ `!important`，不依赖随构建变化的 `css-xxxxxx` 哈希类，客户端小版本升级不易失效
- **覆盖面全**：侧栏磨砂、导航选中天空蓝渐变药丸、订阅卡片 / 设置面板 / Merge & Script 卡玻璃、输入框浅底深字、深藏青正文保证可读
- **零依赖**：单文件 CSS，壁纸内嵌，离线可用

## 兼容性 · Compatibility

针对 **Clash Verge Rev**（基于官方 `dev` 分支前端源码类名核对）。若客户端大版本升级后个别区块样式丢失，F12 查看该元素类名提 issue 即可。
