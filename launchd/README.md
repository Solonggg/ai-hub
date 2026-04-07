# launchd

## 用途

`launchd` 存放 macOS 的定时任务定义，目前用于定期执行会话归档采集。

## 目录内容

- `com.wangjie.ai-hub.dream-harvest.plist`：每天 `06:00` 和 `20:00` 各执行一次 `/Users/wangjie/ai-hub/bin/dream-harvest/dream-harvest`，输出日志写入 `.dream/`。

## 用法

1. 加载定时任务：

```bash
launchctl load /Users/wangjie/ai-hub/launchd/com.wangjie.ai-hub.dream-harvest.plist
```

2. 卸载定时任务：

```bash
launchctl unload /Users/wangjie/ai-hub/launchd/com.wangjie.ai-hub.dream-harvest.plist
```

3. 查看任务效果时，重点检查以下文件：

- `/Users/wangjie/ai-hub/.dream/dream-harvest.log`
- `/Users/wangjie/ai-hub/.dream/dream-harvest.err.log`

## 注意事项

- 这是 macOS 专用目录；如果迁移到其他系统，需要用系统对应的调度器替代。
- 修改 plist 后通常需要重新 load/unload 才会生效。
- `launchd` 的日历触发适合“固定时点”任务；如果机器在触发时休眠或关机，可能不会在错过后立即补跑。
