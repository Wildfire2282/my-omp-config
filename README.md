# my-omp-config

Oh My Pi (omp) 配置仓库 — 技能、扩展、规则的单一事实来源。所有目录通过**软链**安装到 `~/.omp/agent/`，编辑即生效。

## 结构

```
my-omp-config/
├── skills/       # Agent Skills（SKILL.md 格式，6 个）
│   ├── crawl4ai/      # Crawl4AI 抓取与结构化抽取
│   ├── create-skill/  # 新建技能（含自检闭环）
│   ├── review-skill/  # 存量技能审计与规范化
│   ├── install-skill/ # 链接与可用性验证
│   ├── svgjs/         # SVG.js v3 编程
│   └── userscript/    # 油猴脚本
├── extensions/   # omp 扩展（bash-bang-complete.ts）
├── rules/        # agent 规则（当前为空）
└── scripts/      # 工具脚本（install-omp-usage.py）
```

## 安装（软链，非拷贝）

```bash
ln -s ~/workspace/my-omp-config/skills     ~/.omp/agent/skills
ln -s ~/workspace/my-omp-config/extensions ~/.omp/agent/extensions
ln -s ~/workspace/my-omp-config/rules      ~/.omp/agent/rules
```

相对目标 `../../workspace/my-omp-config/...`，用户名变化不失效；仓库需保持在 `~/workspace/my-omp-config`。

## 约定

- **改即生效**：编辑 `skills/<name>/` 实时生效；新增需重启 omp 或 reload skills
- **新建技能**：`~/workspace/my-omp-config/skills/<name>/`，遵循 `create-skill/references/standard.md` §8 清单
- **审查存量**：`/skill:review-skill` 指向已存在目录，只出报告与 diff，确认后写回
- **安装**：`/skill:install-skill` 确保集合软链并 `test -f ~/.omp/agent/skills/<name>/SKILL.md`
- **发现**：`omp` 扫描 `<skills-root>/<name>/SKILL.md`
- **触发**：`disable-model-invocation: true`，手动 `/skill:<name>`，路径一律用 `~`

## 注意

- `~/.omp/agent/managed-skills` 为 `manage_skill` 工具管理区，与 `~/.omp/agent/skills` 无关
- 重装 omp 后运行 `python3 scripts/install-omp-usage.py` 恢复用量显示补丁
