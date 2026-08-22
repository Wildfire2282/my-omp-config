---
description: 现代化程序安装规则
alwaysApply: true
---

# 现代化程序安装

需要安装外部程序/依赖时，优先使用现代、幂等、非交互的包管理器；避免遗留/低效方式。已安装即复用，不重复安装；需新装时按生态选择。

## 通用原则

- 非交互：所有安装加静默/自动确认参数（` -y` / `--yes` / `-f`），不在安装过程中等待输入
- 幂等：先 `which` / `<tool> --version` 检测是否已满足版本要求，已满足则跳过
- 固定版本：优先锁定版本或使用 lockfile，避免 `latest` 漂移
- 不污染系统：不 `sudo pip` / `sudo npm`；系统级仅 `apt` 使用 `sudo`，语言级包管理保持用户态
- 可追溯：记录安装来源与版本，便于复现

## 按生态优先级

### Node.js / 前端

| 场景 | 优先 | 避免 |
|------|------|------|
| 项目依赖 | `bun install` > `pnpm install` > `npm install` | `yarn` (除非项目已用) |
| 添加依赖 | `bun add <pkg>` / `pnpm add <pkg>` | `npm install <pkg>` |
| 全局工具/临时执行 | `bunx <pkg>` / `pnpm dlx <pkg>` / `npx --yes <pkg>` | `npm install -g <pkg>` / `sudo npm i -g` |
| Node 版本管理 | 复用 `bun` 自带 | 不新增 `nvm`/`fnm`/`volta`，除非项目强制；如需多版本统一管理则用 `mise` |

> 本机已可用 `bun 1.4.0`、`pnpm 10.12.1`、`npm 9.2.0`，默认 `bun` 优先。

### Python

| 场景 | 优先 | 避免 |
|------|------|------|
| 项目依赖/虚拟环境 | `uv add` / `uv sync` / `uv pip install` | `pip install` / `pip3 install` / `poetry` (除非项目已用) |
| 工具隔离运行 | `uvx <tool>` | `pipx` (本机未装) / `pip install --user` |
| 全局工具安装 | `uv tool install <pkg>` | `sudo pip install` / `--break-system-packages` |

> 本机已可用 `uv 0.12.5` + `uvx`，Python 相关一律走 `uv`。

### Rust

| 场景 | 优先 | 避免 |
|------|------|------|
| 预编译二进制 | `cargo binstall <crate>` | 直接 `cargo install`（编译慢） |
| 无 binstall 时 | `cargo install --locked <crate>` | 不加 `--locked` |

> 本机已可用 `cargo`/`rustc 1.93.1`，如未装 `cargo-binstall` 则先 `cargo install --locked cargo-binstall`。

### 系统级 (Ubuntu/Debian WSL)

- 使用 `apt-get` / `apt`，全程 `-y` 且先 `apt-get update`（24h 内已更新可跳过）
- 最小化安装：`apt-get install -y --no-install-recommends <pkg>`
- 避免 `snap` / 源码编译，除非 apt 无包或版本过旧

### Go

- 本机暂未安装 Go；如需则先装 `golang`（`apt-get install -y golang` 或 `mise use go@latest`），再 `go install <pkg>@latest`

## 执行示例

```bash
# 检测后安装
command -v rg >/dev/null 2>&1 || cargo binstall --no-confirm ripgrep
command -v ruff >/dev/null 2>&1 || uv tool install ruff
which node >/dev/null 2>&1 || { curl -fsSL https://bun.sh/install | bash; }
bunx --yes cowsay "hello"
uvx --from httpie http --version
sudo apt-get update && sudo apt-get install -y --no-install-recommends jq
```

## 禁止项

- `sudo npm install -g` / `sudo pip install`
- `pip install --break-system-packages`
- 无 `-y` 的交互式 `apt install`
- 为单次执行而全局污染（能 `*x`/`dlx` 就不 `install -g`）
