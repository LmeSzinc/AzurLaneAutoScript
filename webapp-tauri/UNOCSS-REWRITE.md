# UnoCSS 从零重写方案（v2）——已实施

> 状态：**已实施**（P1–P4 完成，验收见 §5）。本文是「把旧 CSS 翻译进 UnoCSS」（当前 `uno.config.ts` + `theme.css` 的
> 1:1 移植方案）的替代设计：保留视觉设计（配色、布局节奏、字重、主题机制），
> 以 UnoCSS 惯用方式重建实现，并系统清除旧债。
>
> 验收口径：**视觉等观**（非逐像素）——允许 1–2px 级差异与「清债」带来的有意变化，
> 全部记录在 §5 豁免表；像素门禁阈值相应放宽。

---

## 1. 原则

1. **工具类优先**：组件标记直接用工具类组合表达，状态用 `hover:`/`active:`/`disabled:` 变体；
   不再为旧类名（`btn-off`、`arg-container`、`hr-group`…）建立 1:1 别名。
2. **语义 token**：token 按「原始色板 → 语义角色」两层组织；主题只覆盖原始色板 + 少量语义角色，
   不再每主题平铺 60+ 个派生值（hover/active 色阶用 `color-mix` 从色板推导）。
3. **shortcut 只留给真复合件**：解剖结构在多处重复出现的（按钮骨架、面板、表格），
   以「解剖基类 + 工具类变体」的形式保留；一次性样式全部内联为工具类。
4. **重置最小化**：`base.css` 只保留平台归一化（box-sizing、表单字体长写、按钮光标、滚动条、关键帧），
   不再逐条复刻 Bootstrap reboot（h4/p 边距等移到使用处用工具类表达）。
5. **旧债清单化清理**：`!important`、UA 边框 hack、`min-width:992px!important`、magic number、
   硬编码色值，逐个删除并在豁免表登记视觉影响。

## 2. Token 体系 v2（`src/styles/theme.css` 重写）

### 2.1 两层结构

**第一层：原始色板**（每主题一组，共 ~8 个值）

```css
:root { /* default / light */
  --color-primary: #007bff;
  --color-success: #28a745;
  --color-info:    #17a2b8;
  --color-danger:  #dc3545;
  --gray-300: #dee2e6; --gray-400: #ced4da; --gray-500: #adb5bd; --gray-600: #6c757d;
}
```

**第二层：语义角色**（壳层明暗 × 调色板主题，每主题块 ~15–20 行）

```css
:root {
  /* surfaces */
  --surface-app: #f9f9f9;  --surface-panel: #fff;  --surface-side: #fff;
  --surface-insert: #fff;  --surface-hover: #fff;
  /* lines */
  --line-panel: lightgrey; --line-soft: rgba(0,0,0,.1); --line-control: var(--gray-600);
  /* text */
  --text-body: #212529; --text-muted: #777;
  /* accent & status（明暗壳二态）*/
  --accent: #4e4c97; --status-idle/running/warning/updating: …;
  --ansi-*（明暗二态，保持现状——这是数据不是设计）;
}
:root[data-theme='dark'] { …覆盖 surface/line/text/accent/ansi… }
:root[data-theme='minty'] { --color-*: …; }
```

对比现状：dark 主题块从 ~60 个平铺 token 降到 ~20 个语义覆盖。

### 2.2 派生状态色（替代 12 个 hover/active/border token）

按钮 hover/active 色不再手工搬运 Bootswatch 的三个色阶，而是从色板推导：

```ts
// uno.config.ts theme.colors
primary: 'var(--color-primary)',
'primary-hover': 'color-mix(in srgb, var(--color-primary) 88%, #000)',
'primary-active': 'color-mix(in srgb, var(--color-primary) 80%, #000)',
```

- Chromium 130（构建 target）原生支持 `color-mix`，Tauri WebView 无兼容问题；
- 与旧手调色阶的偏差 ≤ 若干 RGB 步（视觉等观可接受，豁免表登记）；
- 个别主题若你希望严格保留（如 sketchy 全黑系），该主题显式覆盖 2–3 个值即可（混合策略）。

### 2.3 UnoCSS `theme` 映射（工具类即语义）

```ts
theme: {
  colors: {
    surface: { app: 'var(--surface-app)', panel: 'var(--surface-panel)', side: 'var(--surface-side)',
               insert: 'var(--surface-insert)', hover: 'var(--surface-hover)' },
    line:    { panel: 'var(--line-panel)', soft: 'var(--line-soft)', control: 'var(--line-control)' },
    text:    { body: 'var(--text-body)', muted: 'var(--text-muted)' },
    accent:  'var(--accent)',
    status:  { idle: 'var(--status-idle)', running: 'var(--status-running)', … },
    primary: …, 'primary-hover': …, 'primary-active': …, /* success/info/danger 同理 */
  },
}
```

标记里即可写 `bg-surface-panel border-line-panel text-muted bg-primary hover:bg-primary-hover`。

### 2.4 间距/尺寸 token（吸收 magic number）

```css
--space-section: 7.75rem;   /* 旧 running-section 高度 */
--w-aside: 4rem; --w-menu: 12rem; --h-header: 50px; --w-form-col: 13rem;
--text-sm: .8rem; --text-base: 1rem; …（如需）
```

布局微调从此改 token 而非扫改组件。

## 3. 标记重写规范（组件映射）

| 旧类（现状） | v2 写法 | 说明 |
|---|---|---|
| `btn`（骨架） | 保留**一个**解剖基类 `btn`：`inline-flex items-center justify-center gap-1 select-none border-solid border border-transparent rounded-[--radius-btn] px-3 py-1.5 text-[--text-btn] leading-6 transition-colors focus:outline-none disabled:opacity-65` | 骨架重复 20+ 次，属正当复合件；变体一律在标记里用工具类叠加 |
| `btn-primary/success/info` | `class="btn bg-primary text-white hover:bg-primary-hover active:bg-primary-active"` | 变体 = 工具类，不再是别名类 |
| `btn-off` / `btn-on`（开关） | `class:bg-surface-app={alive} class:bg-accent={!alive} …` 或 `class="btn {alive ? A : B}"`（`$derived` 字符串，safelist 登记） | 意图直白 |
| `btn-menu` / `btn-menu-active` | `class="btn w-full justify-start rounded-none border-0 border-l-3 border-transparent px-3 py-[1px] bg-transparent hover:border-l-accent hover:text-accent"` + `class:font-bold` `class:text-accent` 状态组 | 左竖条选中态用变体表达 |
| `btn-aside` / `btn-aside-active` | 同上模式（`w-16 flex-col text-[0.8rem] py-1.5 pb-3`，图标+文字竖排） | |
| `btn-adaptive` | `class="btn border-line-control bg-transparent text-body hover:border-gray-500 hover:bg-black/10"` | |
| `btn-navigator` | `class="btn w-full justify-start rounded-none bg-surface-panel text-body hover:font-bold hover:text-accent"` | |
| `form-control` | DynamicForm 内联：`class="block w-full rounded-none border-0 bg-surface-insert px-3 py-1.5 h-auto text-body focus:bg-surface-hover focus:outline-none"` | 只此一处组件，不需要别名类 |
| `form-check(-input)` | `class="relative block pl-5"` + `class="absolute mt-1.2 -ml-5 h-5 w-5 accent-[--accent-check]"` | `--accent-check: #7a77bb` 常量（旧明壳硬编码，登记） |
| `state-display(-bold/-light)` | `class="truncate border border-b-0 border-line-control px-2"` + `class:font-bold={bold}` `class:text-accent={bold}` / `class:text-muted={light}` | |
| `table` / `table-sm` | 保留薄复合件 `table`：`w-full mb-4 border-collapse text-text-body [&_th,&_td]:p-3 [&_th,&_td]:border-t [&_th,&_td]:border-line-soft [&_thead_th]:border-b-2`；`table-sm` 仅覆盖 cell padding | 三处复用，含子元素选择器，正当 |
| `alert` / `alert-danger` | `class="relative mb-4 border border-solid px-5 py-3"` + `class="border-danger bg-[--surface-danger] text-[--text-danger-strong]"` | |
| `spinner-border(-sm)` | `class="inline-block animate-[spinner-border_.75s_linear_infinite] rounded-full border-[.25em] border-solid border-r-transparent h-8 w-8"` | 尺寸 `h-4 w-4` 变体 |
| `group-card(-title/-help)` | `class="panel my-2 p-4"`（`panel` = `border border-solid border-line-panel bg-surface-panel`）+ `class="text-[1.25rem] font-medium mx-1"` / `class="text-[0.8rem] text-muted mx-1"` | `panel` 为保留复合件之一 |
| `scheduler-bar` / `log-bar` / 三个 section | `panel` + `flex items-center justify-between m-1.25 p-2.5` / section 网格与 `h-[--space-section]` 等工具类 | |
| `hr-group` | `class="my-1 border-0 border-t border-line-soft bg-[--surface-hr]"` | |
| `log-view` / `tool-log` | LogView 的 props `class` 由父组件传工具类字符串：`grow min-h-0 overflow-y-auto m-1.25 p-2.5 font-mono text-[0.85rem] leading-[1.2] whitespace-pre panel` / `col-[2] min-h-60 max-h-[40vh] rounded bg-[--surface-log] p-2 text-xs whitespace-pre-wrap` | |
| `header-state-*` | 点：`h-2 w-2 rounded-full bg-status-idle`；状态：`class:bg-status-running={state===1}`…（AppHeader 内 `$derived` 状态组，safelist 登记） | |
| `aside-icon` | `class="mx-auto mb-1.5 block h-8 w-8 bg-[--icon-fill] [mask:center/contain_no-repeat] [mask-image:url(…)]"` | |

**通用约定**
- 动态类（`class:xxx={…}` 或模板字符串）一律进 `uno.config.ts` 的 `safelist`，并在组件内注释说明；
- 禁用 `!` 前缀与 `!important`：冲突靠「变体类不重叠」设计规避（解剖基类只含结构，不含可被变体覆盖的颜色/尺寸）；
- 任意属性 `[prop:value]` 仅用于 CSS 变量引用与平台专属（`-webkit-app-region`、mask）等，不再作为普通声明的载体。

## 4. 全局归一化（`base.css` v2，仅保留）

```css
*,*::before,*::after { box-sizing: border-box; }
html,body,#app { margin:0; padding:0; height:100vh; overflow:hidden; }
body { background:var(--surface-app); color:var(--text-body); font-size:…; font-weight:…; line-height:1.5; }
#app { font-family: …栈…; }
button { color:inherit; }  button:not(:disabled){ cursor:pointer; }
button,input,optgroup,select,textarea { font-family:inherit; font-size:inherit; line-height:inherit; }
a / a:hover 颜色（token 化）
::-webkit-scrollbar… select option…
@keyframes spinner-border
```

**删除**（旧 quirk，豁免登记）：`min-width:992px!important`（响应式解放）、h4/p 全局边距（移到使用处）。

## 5. 视觉等观验收与豁免登记（实施后实测）

- 门禁：与 `dev_tools/webui/baseline-old`（迁移前 UI）像素比对，1280×800、4 路由 × 5 主题；
  **实测结果（v2 最终构建）**：develop 0.37–1.51%、home 0.67–2.63%、manage 0.73–1.91% ✓；
  settings 5.15–6.97%（豁免 #7，阈值放宽至 ≤7%）。
- 豁免表（有意差异，评审已确认 #1/#2/#3，其余实施中登记）：

| # | 差异 | 视觉影响 | 理由 |
|---|---|---|---|
| 1 | hover/active 由 `color-mix` 推导，替代手调色阶 | 个别主题 hover 色偏差 ≤ 3 RGB 步 | token 数 −40 |
| 2 | 移除 `min-width:992px!important` | 窄窗口不再强制横向滚动（1280 捕获无差异） | 响应式负债 |
| 3 | `!important` 全部移除 | 无（级联等价） | 可维护性 |
| 4 | 按钮 UA 2px 边框改由全局 reset 一次归零 | 无 | 集中而非散落 |
| 5 | checkbox `accent` 常量 token 化（`--accent-check`） | 无（值不变） | 单源 |
| 6 | 组件样式单源化（旧壳 CSS 与作用域双写合并） | 无 | 漂移风险 |
| 7 | settings 表单控件的亚像素垂直定位：旧实现的复选框以行内 line-box 参与行高（31px）且控件 margin 参与塌陷；新实现以 `min-h-[31px]` + 相对定位对齐，控件垂直偏差 ~6–10px 累计 | settings 页 5.2–7.0% diff（各控件单看为 1–2px 级） | 旧实现依赖 UA 行内布局细节，无法以工具类精确表达；视觉等观口径下可接受 |

- 附加门禁：svelte-check 0 错、8/8 测试、biome 错误数 ≤ 基线（15）。
- 人工复核：与 `baseline-old` 的并排 diff 热力图 + 关键截图（`dev_tools/webui/baseline-new/_diff/`）。

## 6. 实施状态

| 阶段 | 内容 | 状态 |
|---|---|---|
| P1 | token v2（语义两层 + color-mix 派生）、`uno.config.ts` theme 映射、`base.css` v2 最小归一化 | ✅ 已实施 |
| P2 | 全部组件改为工具类优先标记；旧 shortcuts 删除（仅留 `btn`/`btn-sm`/`panel`/`table` 四个真复合件）；safelist 收敛 | ✅ 已实施 |
| P3 | 清债：`!important` 全清、992px min-width 移除、UA 按钮边框全局 reset、magic number → 尺寸 token | ✅ 已实施 |
| P4 | 文档更新（本文件为实施记录） | ✅ 本文件 |

回滚：`git revert`；如需恢复逐主题手调色阶，回退 P1 的 color-mix 配置即可。
