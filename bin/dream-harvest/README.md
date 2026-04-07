# dream-harvest

## 用途

`dream-harvest` 目录提供 AI 会话归档命令，用于扫描本地会话源文件，并把结果整理到 `/Users/wangjie/ai-hub/.dream/`。

## 目录内容

- `dream-harvest`：可执行入口文件。
- `dream_harvest.py`：命令实现，负责解析会话文件、合并摘要、增量扫描和归档写入。

## 用法

常见命令：

```bash
/Users/wangjie/ai-hub/bin/dream-harvest/dream-harvest --archive-dir /Users/wangjie/ai-hub/.dream
/Users/wangjie/ai-hub/bin/dream-harvest/dream-harvest --archive-dir /Users/wangjie/ai-hub/.dream --source codex
/Users/wangjie/ai-hub/bin/dream-harvest/dream-harvest --archive-dir /Users/wangjie/ai-hub/.dream --source-root /tmp/demo-sources
```

默认支持的来源：

- `codex`
- `claude-code`
- `jetbrains-ai`

## 输出结果

- 归档 Markdown：`/Users/wangjie/ai-hub/.dream/YYYY-MM-DD-<agent>.md`
- 增量扫描状态：`/Users/wangjie/ai-hub/.dream/.state/*.json`
- 运行日志通常由 `launchd` 写入 `.dream/*.log`

## 注意事项

- 该命令会根据文件大小和修改时间做增量处理，不会每次全量重扫。
- 如果归档结果异常，先检查 `.dream/.state` 和源日志格式，再决定是否强制重扫。
