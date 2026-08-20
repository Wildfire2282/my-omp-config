# my-omp-config

[English](#english)

Oh My Pi (omp) 个人配置仓库，集中管理 Skills、Extensions、Rules，通过软链实现编辑即生效。

---

## 简介

本仓库是 `~/.omp/agent/` 的单一事实来源。所有目录以软链形式安装，无需拷贝，改动实时生效。

## 目录结构

```
my-omp-config/
├── LICENSE
├── skills/            # 全局技能集（软链至 ~/.omp/agent/skills）
│   ├── crawl4ai/      # 网页抓取与结构化抽取
│   ├── create-skill/  # 创建新技能（含模板与校验）
│   ├── install-skill/ # 软链安装与可用性校验
│   ├── review-skill/  # 存量技能审计与规范化
│   ├── userscript/    # 油猴脚本开发
│   └── omp-guide/     # omp 使用指引
├── project-skills/    # 项目级技能集（不软链，手动复制到项目使用）
│   └── svgjs/         # SVG.js 矢量图形编程
├── extensions/   # omp 扩展
│   └── bash-bang-complete.ts  # Shell 补全增强
├── rules/        # 全局规则
│   └── language.md  # 语言与术语规则
└── scripts/      # 工具脚本
    └── install-omp-usage.py  # 状态栏用量显示补丁 (Opencode Go)
```

## 快速开始

```bash
ln -s ~/workspace/my-omp-config/skills     ~/.omp/agent/skills
ln -s ~/workspace/my-omp-config/extensions ~/.omp/agent/extensions
ln -s ~/workspace/my-omp-config/rules      ~/.omp/agent/rules
```

仓库固定在 ~/workspace/my-omp-config，使用相对路径软链。

## 使用约定

- 编辑 `skills/<name>/` 或 `rules/` 后实时生效，新增需重启 omp
- 新建技能遵循 `create-skill` 规范，审计存量使用 `review-skill`
- 安装校验：`/skill:install-skill`

## 工具

`scripts/install-omp-usage.py` 将 omp 状态栏的费用显示替换为 opencode-go 套餐用量的紧凑格式 `5h%-7d%-mo%`，并通过 `~/.local/bin/omp` wrapper 实现升级后自动重打补丁。详见 `scripts/README.md`。

## 许可证

MIT License — 详见 [LICENSE](LICENSE)

---

<a id="english"></a>

## English
Personal configuration repository for [Oh My Pi](https://github.com/nicepkg/oh-my-pi), centrally managing Skills, Extensions and Rules. Installed via symlinks — edits take effect instantly.

### Overview
This repository is the single source of truth for `~/.omp/agent/`. All directories are symlinked, no copying needed, and edits take effect instantly.

### Structure
```
my-omp-config/
├── LICENSE
├── skills/            # Global Skills (symlinked to ~/.omp/agent/skills)
│   ├── crawl4ai/      # Web crawling & structured extraction
│   ├── create-skill/  # Create new skill (template & validation)
│   ├── install-skill/ # Symlink install & verification
│   ├── review-skill/  # Audit existing skills and normalization
│   ├── userscript/    # Userscript development
│   └── omp-guide/     # omp usage guide
├── project-skills/    # Project-level Skills (not symlinked, copy manually to project)
│   └── svgjs/         # SVG.js vector graphics
├── extensions/   # omp extensions
│   └── bash-bang-complete.ts  # Shell completion enhancement
├── rules/        # Global rules
│   └── language.md  # Language & terminology rules
└── scripts/      # Utilities
    └── install-omp-usage.py  # Status line usage patch (Opencode Go)
```

### Quick Start

```bash
ln -s ~/workspace/my-omp-config/skills     ~/.omp/agent/skills
ln -s ~/workspace/my-omp-config/extensions ~/.omp/agent/extensions
ln -s ~/workspace/my-omp-config/rules      ~/.omp/agent/rules
```

The repository is fixed at ~/workspace/my-omp-config, using relative symlinks.

### Conventions

- Edits to `skills/<name>/` or `rules/` take effect instantly; new entries require an omp restart
- Create skills following `create-skill` standard, audit with `review-skill`
- Verify install: `/skill:install-skill`

### Utilities

`scripts/install-omp-usage.py` replaces the cost display in the omp status line with a compact opencode-go usage format `5h%-7d%-mo%` and auto-repatches after upgrades via a `~/.local/bin/omp` wrapper. See `scripts/README.md` for details.

### License

MIT License — see [LICENSE](LICENSE)
