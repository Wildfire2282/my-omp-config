# opencode-go 用量显示样式修改说明

## 目标与现状

omp TUI 顶部 status line(俗称 footer)原本在 `cost` 位置显示模型费用。本方案改为显示 opencode-go 套餐用量,格式为紧凑的三窗口百分比:

```
0%-8%-4%
```

三个数字分别是 **5 小时 / 一周 / 一个月** 滚动窗口的已用百分比(服务端下取整,不带单位)。约 11 字符,窄窗口下比默认格式(`5h 0% (3h 12m) · 7d 8% (1d 12h) · mo 4% (29d 2h)`)更不易被 status line 宽度裁剪。

完整显示约需 **118 列**窗口;更窄时 usage 会被宽度裁剪(尾部 segment 从后往前丢弃,原 `cost` 行为相同)。

## 为什么不能靠扩展插件实现

- 扩展 API 的 `ctx.ui.setStatus(key, text)` 在 omp 内部实现为 `setHookStatus` —— 渲染在 status line **下方**单独一行,永远进不了 status line 内部;
- `setFooter` / `setHeader` 在 TUI 模式下是 no-op;
- 扩展 API 没有注册/覆盖 status segment 的任何机制。

结论:扩展只能显示在错误位置。**status line 内部只有 omp 内置的 `usage` segment 能占据 `cost` 槽位**。

## 实现的两层

### 1. 显示位置 —— 配置

`~/.omp/agent/config.yml`:

```yaml
statusLine:
  preset: custom
  leftSegments: [pi, model, mode, collab, path, git, pr, context_pct, usage]
  rightSegments: [session_name]
  separator: powerline-thin
```

`usage` 加在末尾,即原来 `cost` 的位置(默认 preset 中 cost 本就在该区段末尾)。数据流全内置:

```
status line 渲染 → refreshUsageInBackground() → session.fetchUsageReports()
  → model registry 内置 opencode-go usage provider
  → GET https://opencode.ai/zen/go/v1/usage (Bearer <OPENCODE_API_KEY>)
  → 解析 {fiveHour, sevenDay, monthly} → usage segment 渲染
```

凭证来自 omp 的 `auth_credentials` 表,无需额外配置。可先用 `omp usage --provider opencode-go --json` 验证数据源可用。

### 2. 显示格式 —— 补丁内置渲染代码

内置 `usage` segment 默认渲染长格式(图标 + 窗口标签 + 重置倒计时)。扩展改不了它,所以直接修改 omp 打包产物:

```
~/.bun/install/global/node_modules/@oh-my-pi/pi-coding-agent/dist/cli.js
```

`cli.js` 是压缩后的单行 JS。补丁用 python 定位并整体替换 usage segment 对象:

- **定位**:字符串字面量 `id:"usage",render(...)` —— 压缩器不改字符串,但会改变量名(`H0u`、`y8i`、`Q.fg` 等),因此补丁代码**零内部符号依赖**(纯文本模板字符串),升级后只要 segment 对象结构还在就能重打;
- **替换**:从 `id:"usage"` 前最近的 `{` 开始做花括号配对,取出整个对象,换成:

```js
{id:"usage",render(_i){
  let n=_i.usage;
  if(!n||!n.fiveHour&&!n.sevenDay&&!n.monthly) return {content:"",visible:!1};
  let h=[];
  if(n.fiveHour) h.push(`${Math.round(n.fiveHour.percent)}%`);
  if(n.sevenDay) h.push(`${Math.round(n.sevenDay.percent)}%`);
  if(n.monthly)  h.push(`${Math.round(n.monthly.percent)}%`);
  return {content:h.join("-")/*omp-usage-compact*/,visible:!0}
}}
```

`/*omp-usage-compact*/` 是"已补丁"检测标记。

## 一劳永逸:自愈 wrapper

omp 升级会用新文件覆盖 `cli.js`,手工补丁会丢失。方案是自愈 wrapper:

```
~/.local/bin/omp   (PATH 中排在 ~/.bun/bin 之前)
```

每次启动:

```
检测 cli.js 是否含标记 /*omp-usage-compact*/
  ├─ 有 → 已补丁,直接 exec 真 omp
  └─ 无(升级覆盖)→ 自动重打补丁 → exec 真 omp
```

关键设计:

| 点 | 做法 |
|---|---|
| 单一事实来源 | 补丁逻辑只有 `apply_patch()` 一个函数;安装脚本用 `inspect.getsource()` 把它内嵌进 wrapper,不会两处漂移 |
| 原子写 | `tempfile.mkstemp` + `os.replace`,避免污染 bun cache 硬链接副本(实测 cache 保持原始 inode) |
| 权限保留 | `os.fchmod(fd, 原文件 mode)`,否则替换后 cli.js 失去执行位(`exec` 报 Permission denied) |
| 安全降级 | 定位不到 usage segment(omp 大重构)时打印警告、按未补丁版启动,不崩溃 |

## 使用方法

```bash
# 换环境/重装 omp 后:
python3 scripts/install-omp-usage.py
# 可选参数:
#   --bin-dir DIR   wrapper 安装目录(默认自动选 PATH 优先可写目录,首选 ~/.local/bin)
#   --cli PATH      显式指定 cli.js(默认自动检测)
```

幂等,可重复运行。安装后**重启 omp** 生效。

## 相关文件清单

| 文件 | 作用 |
|---|---|
| `scripts/install-omp-usage.py` | 安装器:定位 cli.js → 打补丁 → 装 wrapper |
| `~/.local/bin/omp` | 自愈 wrapper(由安装器生成,勿手改) |
| `~/.bun/install/global/node_modules/@oh-my-pi/pi-coding-agent/dist/cli.js` | 被打补丁的 omp 打包产物 |
| `~/.omp/agent/config.yml` | `statusLine.leftSegments` 中的 `usage` segment |
| `~/.bun/install/cache/@oh-my-pi/pi-coding-agent@<ver>@@@1/dist/cli.js` | bun 缓存(硬链接,补丁采用原子写保证其保持原始) |

## 故障排查

- **升级后格式变回长格式**:wrapper 应已自动重打;手动确认 `grep -c omp-usage-compact <cli.js>`(应为 1);若为 0 且启动日志有 `[omp-usage] patch failed`,说明 omp 重构了 segment 结构,需更新 `apply_patch()` 的定位正则;
- **窄窗口看不到用量**:status line 宽度裁剪,属正常行为;可精简 `leftSegments`(如去掉 `mode`/`collab`)或拉宽窗口;
- **用量不刷新**:先 `omp usage --provider opencode-go --json` 验证数据源;status line 有 5 分钟节流(失败后也进入节流),等待或重启 omp。
