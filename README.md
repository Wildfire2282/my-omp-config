# my-omp-config

[English](#english)

Oh My Pi (omp) 个人配置仓库，集中管理 Skills、Extensions、Rules，通过软链实现编辑即生效。

> [!WARNING]
> 仅在 WSL (Windows Subsystem for Linux) 环境测试过

---

## 简介

本仓库是 `~/.omp/agent/` 的单一事实来源。所有目录以软链形式安装，无需拷贝，改动实时生效。

## 目录结构

```
my-omp-config/
├── skills/       # Agent Skills
│   ├── crawl4ai/      # 网页抓取与结构化抽取
│   ├── create-skill/  # 创建新技能
│   ├── install-skill/ # 软链安装与校验
│   ├── review-skill/  # 存量技能审计
│   ├── svgjs/         # SVG.js 编程
│   ├── userscript/    # 油猴脚本开发
│   └── omp-guide/     # omp 使用指引
├── extensions/   # omp 扩展
│   └── bash-bang-complete.ts
├── rules/        # 全局规则
│   └── language.md
└── scripts/      # 工具脚本
    └── install-omp-usage.py  # 状态栏用量显示补丁
```

## 快速开始

```bash
ln -s ~/workspace/my-omp-config/skills     ~/.omp/agent/skills
ln -s ~/workspace/my-omp-config/extensions ~/.omp/agent/extensions
ln -s ~/workspace/my-omp-config/rules      ~/.omp/agent/rules
```

仓库需固定在 `~/workspace/my-omp-config`，使用相对路径软链，跨用户名不失效。

## 使用约定

- 编辑 `skills/<name>/` 或 `rules/` 后实时生效，新增需重启 omp
- 新建技能遵循 `create-skill` 规范，审计存量使用 `review-skill`
- 安装校验：`/skill:install-skill`

## 工具

`scripts/install-omp-usage.py` 将 omp 状态栏的费用显示替换为 opencode-go 套餐用量的紧凑格式 `5h%-7d%-mo%`，并通过 `~/.local/bin/omp` wrapper 实现升级后自动重打补丁。详见 `scripts/README.md`。

---

<a id="english"></a>

## English

Personal configuration repository for [Oh My Pi](https://github.com/nicepkg/oh-my-pi), centrally managing Skills, Extensions and Rules. Installed via symlinks — edits take effect instantly.

> [!WARNING]
> Tested on WSL (Windows Subsystem for Linux) only

### Overview

This repository is the single source of truth for `~/.omp/agent/`. All directories are symlinked, no copying needed.

### Structure

```
my-omp-config/
├── skills/       # Agent Skills
│   ├── crawl4ai/      # Web crawling & structured extraction
│   ├── create-skill/  # Create new skills
│   ├── install-skill/ # Symlink install & verification
│   ├── review-skill/  # Audit existing skills
│   ├── svgjs/         # SVG.js programming
│   ├── userscript/    # Userscript development
│   └── omp-guide/     # omp usage guide
├── extensions/   # omp extensions
│   └── bash-bang-complete.ts
├── rules/        # Global rules
│   └── language.md
└── scripts/      # Utilities
    └── install-omp-usage.py  # Status line usage patch
```

### Quick Start

```bash
ln -s ~/workspace/my-omp-config/skills     ~/.omp/agent/skills
ln -s ~/workspace/my-omp-config/extensions ~/.omp/agent/extensions
ln -s ~/workspace/my-omp-config/rules      ~/.omp/agent/rules
```

Keep the repository at `~/workspace/my-omp-config`. Symlinks use relative paths and remain valid across usernames.

### Conventions

- Edits to `skills/<name>/` or `rules/` take effect instantly; new entries require an omp restart
- Create skills following `create-skill` standard, audit with `review-skill`
- Verify install: `/skill:install-skill`

### Utilities

`scripts/install-omp-usage.py` replaces the cost display in the omp status line with a compact opencode-go usage format `5h%-7d%-mo%` and auto-repatches after upgrades via a `~/.local/bin/omp` wrapper. See `scripts/README.md` for details.
