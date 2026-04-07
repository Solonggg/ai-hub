# tests

## 用途

`tests` 保存这个仓库的自动化测试，重点覆盖两类能力：技能分发链路，以及会话归档采集链路。

## 目录内容

- `test_skills_hub.py`：验证 `sync_tool`、`doctor`、`install_target` 等核心行为。
- `test_dream_harvest.py`：验证会话解析、增量扫描、归档写入和状态续扫逻辑。

## 用法

运行全部测试：

```bash
cd /Users/wangjie/ai-hub && python3 -m unittest discover -s tests -p 'test_*.py'
```

只跑单个测试文件：

```bash
cd /Users/wangjie/ai-hub && python3 -m unittest tests/test_skills_hub.py
cd /Users/wangjie/ai-hub && python3 -m unittest tests/test_dream_harvest.py
```

## 注意事项

- 这套测试使用临时目录构造样例仓库，不依赖真实安装目录。
- 修改 `bin/` 下命令实现、`registry.yaml` 处理逻辑或归档格式后，应优先回跑这里的测试。
