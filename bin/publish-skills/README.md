# publish-skills

## 用途

`publish-skills` 目录提供技能发布命令，用于把 `skills/` 真源按 `registry.yaml` 和 `adapters/*.yaml` 的定义生成到 `dist/<tool>/`。

## 目录内容

- `publish-skills`：可执行入口文件。
- `publish_skills.py`：命令实现，负责按工具筛选 skill、复制目录、写引导文件和生成 `index.json`。

## 用法

常见命令：

```bash
/Users/wangjie/ai-hub/bin/publish-skills/publish-skills
/Users/wangjie/ai-hub/bin/publish-skills/publish-skills --tool codex
/Users/wangjie/ai-hub/bin/publish-skills/publish-skills --tool codex --tool gpt-idea
```

输出是 JSON，包含每个工具的：

- `tool`
- `output_dir`
- `skill_count`

## 发布规则

- skill 真源来自 `/Users/wangjie/ai-hub/skills/`
- 启用范围来自 `/Users/wangjie/ai-hub/registry.yaml`
- 产物结构来自 `/Users/wangjie/ai-hub/adapters/*.yaml`
- 发布目标写入 `/Users/wangjie/ai-hub/dist/<tool>/`

## 注意事项

- 这是“生成产物”命令，不要在 `dist/` 下手工长期维护文件。
- 发布后如果还要给具体工具使用，通常下一步是执行 `install-target`。
