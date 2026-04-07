# dist

## 用途

`dist` 是面向具体 AI 工具的分发产物目录。这里的内容由 `skills/`、`agents/` 和 `adapters/` 生成，供后续安装到 `~/.codex`、IDE 插件目录等目标位置。

## 目录内容

- `codex/`、`gpt-idea/`：生成 `AGENTS.md`、`skills/`、`index.json`。
- `claude-code/`、`claude-ide/`：生成 `CLAUDE.md`、`skills/`、`index.json`。

每个工具目录通常包含：

- 引导文件：`AGENTS.md` 或 `CLAUDE.md`
- `skills/`：按适配器整理后的技能目录
- `index.json`：当前工具启用的 skill 清单与路径索引
- `agents/`：仅当存在全局代理时才会出现

## 用法

1. 从真源重新生成产物：

```bash
/Users/wangjie/ai-hub/bin/publish-skills/publish-skills
```

2. 把某个工具的产物安装到目标目录：

```bash
/Users/wangjie/ai-hub/bin/install-target/install-target --tool codex --target ~/.codex
```

3. 通过 `index.json` 快速检查某个工具当前分发了哪些 skill。

## 注意事项

- `dist/<tool>` 会在同步时被删除并重建，禁止在这些工具子目录中手工维护长期文件。
- 如果你要改技能内容，请改 `skills/` 真源；如果要改产物结构，请改 `adapters/`。
