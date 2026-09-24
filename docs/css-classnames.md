# Clash Verge Rev CSS 类名开发文档

> 本文档记录主题所依赖的 Clash Verge Rev 前端真实 CSS 类名、来源文件与覆盖策略。写新主题、排查样式失效时先读这份。

## 一、核心原则

1. **只用真实稳定类名，不用 `css-xxxxxx` 哈希类**。MUI/Emotion 的哈希类随客户端构建变化，换版本即失效；下表列出的语义类名（`.layout-content__left`、`.base-page` 等）来自官方源码手写定义，跨版本稳定。
2. **所有覆盖规则加 `!important`**。客户端自定义 CSS 在 Emotion 样式之后注入，`!important` 稳胜 MUI/Emotion 普通规则与内联样式（如设置页面板 sx 写死的 `#ffffff`），因此不需要脆弱的全局 `:root *` 清底。
3. **严格限定作用域**：
   - 壁纸只挂根容器 `html, body, #root`，**绝不挂后代**（否则每个列表行/卡片都被涂壁纸）
   - 卡片、面板等表面规则一律限定在 `.base-page` 之下，不触碰 `.layout` 外壳

## 二、类名清单（按区块）

### 外壳布局 —— 来源 `src/assets/styles/layout.scss`

| 选择器 | 说明 |
|---|---|
| `.layout` | 应用最外层（`.layout.windows`） |
| `.layout-content` | 主体行容器（侧栏 + 内容区） |
| `.layout-content__left` | **左侧栏**：磨砂玻璃底 + `border-right: 1px solid var(--divider-color)` |
| `.layout-content__right` | 右侧内容区 |
| `.the-logo` / `.the-menu` / `.the-traffic` | 侧栏内部：Logo / 导航菜单 / 底部流量条 |
| `.the-bar` / `.the-content` | 内容区内部：顶栏（拖拽条）/ 页面容器 |

### 导航菜单 —— 来源 `src/components/layout/layout-sidebar.tsx`、`layout-item.tsx`

| 选择器 | 说明 |
|---|---|
| `.the-menu .MuiListItemButton-root` | 导航项（`.the-menu` 是 MUI `List`） |
| `.the-menu .MuiListItemButton-root.Mui-selected` | **选中态**：官方浅色模式 `alpha(primary.main,.15)`，主题改为天空蓝渐变 |
| `.MuiListItemIcon-root` / `.MuiListItemText-root` | 图标 / 文字 |

### 页面骨架 —— 来源 `src/assets/styles/page.scss`

| 选择器 | 说明 |
|---|---|
| `.base-page` | 每个页面的根（须保持透明让壁纸透出） |
| `.base-page > header` | 页标题行 |
| `.base-container` → `section` → `.base-content` | 内容嵌套层 |

### 卡片 / 面板（重点，最容易漏覆盖）

| 选择器 | 来源文件 | 说明 |
|---|---|---|
| `.MuiPaper-root` | MUI 通用 | 常规 Paper 卡片 |
| `.base-page .MuiGrid-root > .MuiBox-root`<br>`.base-page .MuiGrid2-root > .MuiBox-root` | `src/pages/settings.tsx` | **设置页四面板**：裸 `Box` 硬编码 `backgroundColor:'#ffffff'`，是 Grid v2（DOM 类 `MuiGrid2-root`）直接子级 |
| `.base-page .MuiBox-root[aria-selected]` | `src/components/profile/profile-box.tsx` | **订阅卡片**（ProfileItem）与部分卡片表面：`ProfileBox = styled(Box)` 硬编码白底，嵌套在拖拽根 Box 之下、**不是** Grid 直接子级；React 对 `false` 也渲染 `aria-selected="false"`，属性选择器可全量命中 |

> 坑：MUI 里「看着像卡片」的容器不一定是 Paper。排查顺序：页面源码 → 容器组件 → styled 内层，逐层扒到底。

### 表单 / 控件 —— MUI 稳定类

| 选择器 | 说明 |
|---|---|
| `.MuiOutlinedInput-root` / `.MuiOutlinedInput-input` | 输入框（浅玻璃底 + 深字） |
| `.MuiChip-root` / `.MuiSwitch-root` / `.MuiTabs-root` | 标签 / 开关 / 页签 |
| `.MuiButton-containedPrimary` | 主按钮 |

### 主题变量 —— 来源 `src/assets/styles/index.scss` `:root`

| 变量 | 官方默认 | 主题覆盖 |
|---|---|---|
| `--primary-main` | `#5b5c9d` | 天空蓝 `#1E6FD9` |
| `--text-primary` | `#1f1f1f` | 深藏青 `#0B2545` |
| `--background-color` | `#f5f5f5` | `transparent`（露出壁纸） |
| `--divider-color` | 灰 | `rgba(255,255,255,.30)` |
| `--border-radius` | `8px` | `12px` |

其余：`--background-color-alpha`、`--selection-color`、`--scroller-color` 按需覆盖。

## 三、档位参数约定

主题 CSS 由生成器参数化产出，各档位只差玻璃浓度：

| Token | 含义 | summer-sky high | summer-sky normal |
|---|---|---|---|
| `CARD` | 卡片白底 alpha | `.12` | `.20` |
| `CARD_BLUR` | 卡片 backdrop blur(px) | `14` | `18` |
| `NAV` | 侧栏白底 alpha | `.30` | `.42` |

## 四、排查与扩展流程

1. 客户端里某块样式不对 → F12 选中该元素，看 computed 的 `background-color`/`backdrop-filter` 和命中的规则
2. 找它的稳定类名（`MuiXxx-root` 或语义类），对照上表确认来源
3. 在 `.base-page` 作用域下加规则 + `!important`，若在主题生成器中则加 token 占位
4. 本地验证：构建同结构 DOM mock，Chrome headless `--dump-dom` 读 computed style 断言（注意 Chrome 会归一化 `0.30→0.3`、`saturate(150%)→saturate(1.5)`）
5. **mock 必须复刻真实嵌套层级**——选择器命中路径与线上不同会「假 PASS」

## 五、参考

- 官方仓库：https://github.com/clash-verge-rev/clash-verge-rev （默认分支 `dev`）
- 关键源码路径：`src/assets/styles/{layout,page,index}.scss`、`src/components/layout/layout-sidebar.tsx`、`src/pages/settings.tsx`、`src/components/profile/{profile-item,profile-box,profile-more}.tsx`
