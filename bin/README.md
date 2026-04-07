# bin

## 用途

`bin` 是这个仓库的命令入口目录，当前每个命令目录都自带入口文件和自包含实现。

## 目录内容

- `publish-skills`：把 `skills/` 真源发布到 `dist/`。
- `install-target`：把 `dist/<tool>` 安装到目标工具目录，默认用软链接。
- `doctor`：检查 `registry.yaml`、适配器、产物目录和安装状态。
- `dream-harvest`：采集本地 AI 会话，写入 `.dream/`。
- 各命令目录下的 `*.py`：各自自包含的命令实现。

## 常用命令

```bash
/Users/wangjie/ai-hub/bin/publish-skills/publish-skills
/Users/wangjie/ai-hub/bin/publish-skills/publish-skills --tool codex
/Users/wangjie/ai-hub/bin/install-target/install-target --tool codex --target ~/.codex
/Users/wangjie/ai-hub/bin/install-target/install-target --tool codex --target ~/.codex --copy
/Users/wangjie/ai-hub/bin/doctor/doctor
/Users/wangjie/ai-hub/bin/doctor/doctor --tool codex --target ~/.codex
/Users/wangjie/ai-hub/bin/dream-harvest/dream-harvest --archive-dir /Users/wangjie/ai-hub/.dream
```

## 使用顺序

1. 先维护 `skills/`、`registry.yaml`、`adapters/`。
2. 运行 `publish-skills` 生成分发产物。
3. 运行 `doctor` 检查结果。
4. 需要接入具体工具时，再执行 `install-target`。

## 注意事项

- `install-target` 遇到目标目录已有文件时会先备份为 `*.bak.<timestamp>`。
- `dream-harvest` 默认采集 `codex`、`claude-code`、`jetbrains-ai` 三类来源。
