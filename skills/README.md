# 技能集合

Oh My Pi (omp) 的 [Agent Skills](https://agentskills.io) 集合。

- **crawl4ai** — 基于 Crawl4AI 的网站抓取与结构化抽取
- **create-skill** — 从零新建技能（含自检闭环，直修至 §8 全部 PASS）
- **review-skill** — 审计并规范化存量/外部技能（校验、写法、描述优化、evals）
- **install-skill** — 链接技能集到 omp 并验证可发现性
- **svgjs** — 使用 SVG.js v3 编程创建、操作与动画 SVG
- **userscript** — 编写、调试与增强油猴脚本（Tampermonkey / ScriptCat / ...）

每个目录即一个完整技能：合规的 `SKILL.md` + `LICENSE`/`README.md`/`evals/` 与可选 `references/`。通过软链安装整个集合：

```bash
ln -s ~/workspace/my-omp-config/skills ~/.omp/agent/skills   # 用户级
ln -s ~/workspace/my-omp-config/skills <project>/.omp/skills  # 项目级
```

omp 按 `<skills-root>/<name>/SKILL.md` 发现技能；新增后重启 omp（或 reload skills）生效。技能标准见 `create-skill/references/standard.md`（§8 验收清单）。
