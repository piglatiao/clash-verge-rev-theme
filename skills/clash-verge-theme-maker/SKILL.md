---
name: clash-verge-theme-maker
description: 根据一张（或多张）壁纸图片，为 Clash Verge Rev 生成开箱即用的自定义 CSS 主题——每图一套，每套 ultra/high/normal 三档，壁纸 base64 内嵌、单文件粘贴即用，并产出预览图与 README。当用户提到「Clash Verge 主题 / 自定义 CSS 主题 / 用这张图做个主题 / 给我的壁纸配主题」，或要求把图片做成 Clash Verge Rev 界面主题时使用。
agent_created: true
---

# Clash Verge Rev 主题生成

## 用途

把任意一张壁纸变成一套可直接粘贴的 Clash Verge Rev 自定义 CSS 主题：三档透明度
（ultra 纯透明 / high blur 10px / normal blur 18px），壁纸 base64 内嵌无外链，附预览图与 README。

产出遵循仓库既有框架：稳定语义类名 + `!important`、壁纸只挂根容器、档位白雾参数为全主题统一基线。
这些约束的来龙去脉在 `references/css-classnames.md`，**改任何 CSS 模板前先读它**。

## 工作流

### 1. 收集输入

确认两件事：图片路径、输出目录（默认 `themes/`）。
用户只扔一句话 + 一张图时，直接往下走，不要追问风格细节——取色和命名由本 skill 的规则决定。

### 2. 分析图片，定配色

```bash
python scripts/analyze_image.py 图片.jpg
```

拿到主色板、主色候选（按「面积 × 饱和度」排序）和风险提示。

然后**对照图片本身**定三个色（候选只是起点，占比最大的往往是背景墙/天空，未必适合当主色）：

- `primary` 主色 —— 画面最稳的色块：人像取服装/主体色，插画取主体或关键道具色，风景取天空/植被主色
- `light` 亮部 —— 同色相提亮（脚本可自动推导）
- `text` 正文 —— 画面最深暗部的近黑版（脚本可自动推导）

铁律：**主色必须与壁纸同源**。卡片是半透明白雾，壁纸会透过卡片和主色同屏出现，
凭空挑的主色会立刻显脏。判断标准见 `references/design-guide.md` 第二节。

### 3. 命名

统一「四字中文 + 英文驼峰」：`白墙学园 WhiteCampus`、`灯宵夏祭 LanternFest`。
命名要能反推画面；同批主题之间不要撞意境。完整规范见 `references/design-guide.md` 第一节。

### 4. 写 spec.json

最小只需 `src` + `primary`，其余自动推导：

```json
{
  "out": "themes",
  "themes": [
    {"src": "目标/我的猫.jpg", "zh": "午后橘猫", "en": "CatNap",
     "slug": "cat-nap", "emoji": "🐱", "primary": "#C08040",
     "new_name": "午后橘猫-CatNap",
     "desc": "窗台橘猫 × 午后斜光，主色取猫身的暖橘。",
     "note": "画面 70% 是暖灰墙，主色必须在猫身上，否则整屏发闷。"}
  ]
}
```

字段表见 `references/design-guide.md` 第四节。多张图就往 `themes` 数组里堆，一次跑完。

### 5. 构建

```bash
python scripts/build_theme.py --spec spec.json --out themes --root-readme README.md
```

一条命令完成：源图重命名 → 壁纸压缩内嵌 → 3 档 CSS → 3 张预览 → 主题 README → 追加根 README 小节。

- 缺 Pillow 会直接报错，先 `pip install Pillow`
- 找不到 Chrome 会自动跳过预览图并提示，**不会失败**；可用 `--chrome` 指定路径
- 壁纸太大时脚本自动降分辨率保质量；仍想更小就加 `--wall-budget 160000`
- 不想动根 README 就去掉 `--root-readme`

### 6. 校验（不可跳过）

```bash
python scripts/verify_theme.py --dir themes/cat-nap
```

逐档读 Chrome computed style 断言：白雾 α 是否等于档位基线、ultra 是否零模糊、
high/normal 是否分别是 blur(10px)/blur(18px)、渐变是否生效、有无溢出或卡片坍塌。
退出码非 0 就是有问题，修完重跑。

## 交付前自查

- [ ] 三档 CSS 都生成了，且 `verify_theme.py` 三档全 PASS
- [ ] 每个 CSS 只有一段 base64，没有外链
- [ ] 主题名是四字中文 + 英文驼峰，源图已按新名重命名
- [ ] 主色能在图里找到出处（README 配色表写明了来源）
- [ ] 主题 README 与根 README 都更新了

## 给用户的说明要点

交付时主动讲清两件事：

1. **预览图是 DOM mock 渲染的，不是真客户端截图。** mock 复刻了真实嵌套层级，
   所以能通过 computed style 反证选择器命中，但排版细节可能与客户端有出入。
2. **换壁纸的方法**：替换 CSS 里 `data:image/jpeg;base64,……` 那一串即可。

## 不要做的事

- 不要用 `css-xxxxxx` 哈希类名（升级即失效）
- 不要把壁纸挂到 `#root` 的后代元素上（每个列表行都会被涂壁纸）
- 不要给 `.MuiList-root` 或嵌套在磨砂容器内的元素加 `backdrop-filter`（会触发合成缺陷，产生糊斑）
- 不要擅自改档位白雾基线（ultra .08/.20、high .08/.22、normal .20/.30），改了就和既有主题观感不一致
