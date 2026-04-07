# doctor

## 用途

`doctor` 目录提供仓库健康检查命令，用于校验 `registry.yaml`、`adapters/`、`dist/` 产物以及目标安装目录状态是否一致。

## 目录内容

- `doctor`：可执行入口文件，负责启动诊断命令。
- `doctor.py`：命令实现，包含 `doctor()` 和 `main_doctor()`。

## 用法

直接执行入口文件：

```bash
/Users/wangjie/ai-hub/bin/doctor/doctor
/Users/wangjie/ai-hub/bin/doctor/doctor --tool codex
/Users/wangjie/ai-hub/bin/doctor/doctor --tool codex --target ~/.codex
```

返回结果是 JSON：

- `ok: true` 表示没有发现问题
- `ok: false` 表示存在缺失、路径错误、软链接失效等问题

## 适用场景

- 修改 `registry.yaml` 后确认 skill 配置是否完整
- 修改 `adapters/*.yaml` 后确认产物结构是否正确
- 安装到目标目录后确认软链接或复制结果是否有效

## 注意事项

- `doctor.py` 是自包含实现，不再依赖共享库兼容层。
- 这是只读检查命令，不负责修复问题。
