# install-target

## 用途

`install-target` 目录提供安装命令，用于把 `dist/<tool>` 下的产物安装到目标工具目录，默认使用软链接，也支持复制模式。

## 目录内容

- `install-target`：可执行入口文件。
- `install_target.py`：命令实现，负责生成安装条目、备份原文件并执行软链接或复制。

## 用法

常见命令：

```bash
/Users/wangjie/ai-hub/bin/install-target/install-target --tool codex --target ~/.codex
/Users/wangjie/ai-hub/bin/install-target/install-target --tool codex --target ~/.codex --copy
```

行为说明：

- 默认模式：创建软链接，便于后续更新 `dist/` 后立即生效
- `--copy`：复制文件到目标目录，适合不希望保留软链接的场景

## 安装内容

通常会安装以下条目：

- `skills/`
- 引导文件，如 `AGENTS.md` 或 `CLAUDE.md`
- `agents/`，如果该工具产物中存在全局代理目录

## 注意事项

- 如果目标位置已有同名文件或目录，会先备份为 `*.bak.<timestamp>`。
- 安装前最好先运行 `publish-skills`，确保 `dist/` 是最新的。
