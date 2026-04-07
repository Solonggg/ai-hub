# 代码质量评审提示词模板

当你要分派一个代码质量评审子代理时，使用这个模板。

**目的：**确认实现不仅“做对了”，而且“写得可靠、可维护、可测试”。

**只有在规格一致性评审通过后，才能分派这个评审。**

```text
Task 工具（superpowers:code-reviewer）：
  使用 `../requesting-code-review/code-reviewer.md` 模板

  WHAT_WAS_IMPLEMENTED: [来自实现者报告]
  PLAN_OR_REQUIREMENTS: [plan-file] 中的任务 N
  BASE_SHA: [任务开始前的提交]
  HEAD_SHA: [当前提交]
  DESCRIPTION: [任务摘要]
```

**除标准代码质量检查外，还应额外关注：**

- 每个文件是否都只有一个清晰职责，并暴露清晰接口？
- 各个单元是否被拆分到足够容易理解和单独测试？
- 实现是否遵循了计划中给定的文件结构？
- 这次改动是否新建了已经过大的文件，或显著把现有文件继续做大？
  不要对历史遗留的大文件吹毛求疵，只关注这次改动新增的问题。

**评审者应返回：**Strengths、Issues（Critical / Important / Minor）、Assessment
