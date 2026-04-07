# adapters

## 用途

`adapters` 存放面向不同 AI 工具的分发适配配置，定义技能真源如何同步到 `dist/<tool>`，以及每个工具启动时要注入的引导文件。

## 目录内容

- `codex.yaml`、`gpt-idea.yaml`、`claude-code.yaml`、`claude-ide.yaml`：工具适配配置。
- `bootstrap/AGENTS.md`、`bootstrap/CLAUDE.md`：共享的引导模板，会在分发时复制到目标产物目录。

这些适配文件虽然扩展名是 `.yaml`，但当前内容实际采用 JSON 结构，发布与诊断命令都会按 JSON 解析它们。

## 用法

1. 新增一个工具适配时，先复制一个现有 `*.yaml`，再调整以下关键字段：

- `tool`
- `output_dir`
- `skill_dir_name`
- `agent_dir_name`
- `bootstrap_file`
- `bootstrap_source`
- `preserve_skill_agents`
- `flatten_global_agents`

2. 修改引导文案时，优先改 `bootstrap/` 下的模板，再重新同步分发目录：

```bash
/Users/wangjie/ai-hub/bin/publish-skills/publish-skills --tool codex
```

3. 变更后可用诊断命令检查配置完整性：

```bash
/Users/wangjie/ai-hub/bin/doctor/doctor --tool codex
```

## 注意事项

- `output_dir` 对应的产物目录会在同步时被重建，不要把手工文件放到 `dist/<tool>` 里。
- 如果适配器字段缺失，`doctor` 会直接报错。
