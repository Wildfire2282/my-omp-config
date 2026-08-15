# my-omp-config

Oh My Pi (omp) 配置仓库 —— 技能、扩展、规则的单一事实来源。所有目录通过**软链**安装到 `~/.omp/agent/` 对应位置，编辑即生效。

## 结构

```
my-omp-config/
├── skills/       # Agent Skills 集合（SKILL.md 格式）
├── extensions/   # omp 扩展（bash-bang-complete.ts）
├── rules/        # agent 规则（当前为空）
└── scripts/      # 工具脚本（install-omp-usage.py，见 scripts/README.md）
```

## 安装方式（软链，非拷贝）

```bash
ln -s ~/workspace/my-omp-config/skills     ~/.omp/agent/skills
ln -s ~/workspace/my-omp-config/extensions ~/.omp/agent/extensions
ln -s ~/workspace/my-omp-config/rules      ~/.omp/agent/rules
```

活体软链使用相对目标（`../../workspace/my-omp-config/...`），用户名变化不失效；前提是仓库保持在 `~/workspace/my-omp-config`。

## 操作约定

- **改技能即生效**：编辑 `skills/<name>/` 实时生效（软链指向源），无需重装；新增目录需重启 omp 或 reload skills 注册
- **新建技能**：固定放 `~/workspace/my-omp-config/skills/<name>/`，遵循 `create-agent-skill` 标准（`skills/create-agent-skill/references/standard.md`，§8 验收清单）
- **发现机制**：omp 扫描 `<skills-root>/<name>/SKILL.md`
- **技能手动触发**：`disable-model-invocation: true`，用 `/skill:<name>` 调用，agent 不自动激活
- **路径一律用 `~`**：禁止写死 `/home/<user>/...`

## 注意事项

- `~/.omp/agent/managed-skills` 是 omp 内置 `manage_skill` 工具管理区，与用户技能 `~/.omp/agent/skills` 互不相干，勿动
- 重装 omp 后运行 `python3 scripts/install-omp-usage.py` 恢复用量显示补丁（详见 scripts/README.md）
