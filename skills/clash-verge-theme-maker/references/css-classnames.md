# Clash Verge Rev CSS 类名与覆盖策略

> 写主题、排查样式失效前先读这份。类名来自官方源码手写定义（跨版本稳定），
> 不用 MUI/Emotion 的 `css-xxxxxx` 哈希类——那类随客户端构建变化，升级即失效。

来源仓库：https://github.com/clash-verge-rev/clash-verge-rev （默认分支 `dev`）

## 一、三条硬规则

1. **只用稳定语义类名**，全部规则加 `!important`。
   客户端自定义 CSS 在 Emotion 之后注入，`!important` 能稳胜 MUI/Emotion 普通规则与
   内联样式（如设置页面板 sx 写死的 `#ffffff`）。因此不需要脆弱的全局 `:root *` 清底。
2. **壁纸只挂根容器 `html, body, #root`**，绝不挂后代——否则每个列表行、每张卡片都会被涂一遍壁纸。
3. **表面规则限定在 `.base-page` 之下**，不触碰 `.layout` 外壳。

## 二、类名清单

### 外壳布局 —— `src/assets/styles/layout.scss`

| 选择器 | 说明 |
|---|---|
| `.layout` | 应用最外层（`.layout.windows`） |
| `.layout-content` | 主体行容器（侧栏 + 内容区） |
| `.layout-content__left` | **左侧栏**：磨砂底 + `border-right` |
| `.layout-content__right` | 右侧内容区 |
| `.the-logo` / `.the-menu` / `.the-traffic` | 侧栏内部：Logo / 导航菜单 / 底部流量条 |
| `.the-bar` / `.the-content` | 内容区内部：顶栏（拖拽条）/ 页面容器 |

### 导航菜单 —— `layout-sidebar.tsx`、`layout-item.tsx`

| 选择器 | 说明 |
|---|---|
| `.the-menu .MuiListItemButton-root` | 导航项（`.the-menu` 是 MUI `List`） |
| `.the-menu .MuiListItemButton-root.Mui-selected` | **选中态**：官方浅色为 `alpha(primary.main,.15)`，主题改为渐变 |
| `.MuiListItemIcon-root` / `.MuiListItemText-root` | 图标 / 文字 |

### 页面骨架 —— `src/assets/styles/page.scss`

| 选择器 | 说明 |
|---|---|
| `.base-page` | 每页根节点（须保持透明让壁纸透出） |
| `.base-page > header` | 页标题行 |
| `.base-container` → `section` → `.base-content` | 内容嵌套层 |

### 卡片 / 面板（最容易漏覆盖）

| 选择器 | 来源 | 说明 |
|---|---|---|
| `.MuiPaper-root` | MUI 通用 | 常规 Paper 卡片 |
| `.base-page .MuiGrid-root > .MuiBox-root`<br>`.base-page .MuiGrid2-root > .MuiBox-root` | `src/pages/settings.tsx` | **设置页四面板**：裸 `Box` 硬编码 `backgroundColor:'#ffffff'`，是 Grid v2（DOM 类 `MuiGrid2-root`）的直接子级 |
| `.base-page .MuiBox-root[aria-selected]` | `src/components/profile/profile-box.tsx` | **订阅卡片**：`ProfileBox = styled(Box)` 硬编码白底，嵌套在拖拽根 Box 之下、**不是** Grid 直接子级；React 对 `false` 也渲染 `aria-selected="false"`，属性选择器可全量命中 |

> 坑：MUI 里「看着像卡片」的容器不一定是 Paper。排查顺序：页面源码 → 容器组件 → styled 内层，逐层扒到底。

### 表单 / 控件 —— MUI 稳定类

| 选择器 | 说明 |
|---|---|
| `.MuiOutlinedInput-root` / `.MuiOutlinedInput-input` | 输入框（浅玻璃底 + 深字） |
| `.MuiChip-root` / `.MuiSwitch-root` / `.MuiTabs-root` | 标签 / 开关 / 页签 |
| `.MuiButton-containedPrimary` | 主按钮 |

### 主题变量 —— `src/assets/styles/index.scss` `:root`

| 变量 | 官方默认 | 主题做法 |
|---|---|---|
| `--primary-main` | `#5b5c9d` | 取壁纸主色 |
| `--text-primary` | `#1f1f1f` | 取画面最深暗部 |
| `--background-color` | `#f5f5f5` | `transparent`（露出壁纸） |
| `--divider-color` | 灰 | `rgba(255,255,255,.30)` |
| `--border-radius` | `8px` | `12px` |

其余：`--background-color-alpha`、`--selection-color`、`--scroller-color` 按需覆盖。

## 三、档位基线（改动前先想清楚）

| 档位 | CARD（卡片白雾） | NAV（侧栏白雾） | BGALPHA | 磨砂 |
|---|---|---|---|---|
| ultra | .08 | .20 | .08 | 无（纯透明） |
| high | .08 | .22 | .18 | blur 10px |
| normal | .20 | .30 | .18 | blur 18px |

这套参数是**全主题统一基线**：切主题不换手感，用户不用重新适应透明度。改任何一个值都会导致
新旧主题观感不一致，除非有明确理由，否则不要动。

## 四、磨砂实现的坑（重要）

**背景教训**：磨砂最初用 `backdrop-filter`，真实客户端里会触发 Chromium 合成缺陷——
**嵌套结构 + 多个 backdrop-filter 元素**（侧栏内嵌菜单 `ul`、`.MuiMenu-paper` 内嵌 `.MuiList-root`）
会把整块背景纹理损坏成与元素边界无关的大面积糊斑。

由此定下的规则：

1. **不给 `.MuiList-root` 或任何嵌套在磨砂容器内的元素加 `backdrop-filter`**
   ——ultra 档干脆不给任何元素加，`.MuiList-root` 显式 `background: transparent`。
2. 需要磨砂就用「预烘焙模糊图 + `fixed` 对齐」双背景，而不是裸 backdrop-filter
   （现阶段 high/normal 仍用 backdrop-filter，但只加在非嵌套的顶层表面上）。
3. 白雾 α 在明亮壁纸上低于 .10 基本不可见，**档位间 α 差至少 .15 才有可感知区分**。
4. 内嵌图 URL 用 CSS 变量去重时：部分客户端注入环境对超长 `var()` 支持不稳，稳妥做法是直接内嵌（文件会大 ~250KB）。

## 五、排查流程

1. 客户端里某块样式不对 → F12 选中该元素，看 computed 的 `background-color` / `backdrop-filter` 和命中的规则
2. 找稳定类名（`MuiXxx-root` 或语义类），对照上表确认来源
3. 在 `.base-page` 作用域下加规则 + `!important`
4. 本地验证：构建同结构 DOM mock，Chrome headless `--dump-dom` 读 computed style 断言
   （注意 Chrome 会归一化 `0.30→0.3`、`saturate(150%)→saturate(1.5)`）
5. **mock 必须复刻真实嵌套层级**——选择器命中路径与线上不同会「假 PASS」

## 六、关键源码路径

```
src/assets/styles/{layout,page,index}.scss
src/components/layout/layout-sidebar.tsx
src/pages/settings.tsx
src/components/profile/{profile-item,profile-box,profile-more}.tsx
```
