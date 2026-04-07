---
name: requesting-code-review
description: 在任务完成后、实现重大功能后，或合并前需要确认结果符合要求时使用
---

# 请求代码评审

在问题扩散之前，尽早分派 `superpowers:code-reviewer` 子代理做审查。评审者应拿到**精确构造的上下文**，而不是继承你的整个会话历史。这样能让评审聚焦在代码产物本身，而不是你的思考过程，也能保留你的上下文用于后续协同。

**核心原则：**尽早评审，频繁评审。

## 何时请求评审

**必须请求：**

- 在 `subagent-driven-development` 中，每完成一个任务之后
- 完成一个较大的功能之后
- 合并到主分支前

**可选但很有价值：**

- 卡住时，借助新视角排查问题
- 重构前，先做一次基线检查
- 修完复杂 bug 后，确认没有埋下新问题

## 如何请求评审

### 1. 获取 git SHA

```bash
BASE_SHA=$(git rev-parse HEAD~1)  # 或 origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

### 2. 分派 `code-reviewer` 子代理

使用 Task 工具，并填写 `code-reviewer.md` 模板中的占位符。

需要提供：

- `{WHAT_WAS_IMPLEMENTED}`：这次具体实现了什么
- `{PLAN_OR_REQUIREMENTS}`：它原本应该实现什么
- `{BASE_SHA}`：起始提交
- `{HEAD_SHA}`：结束提交
- `{DESCRIPTION}`：简短摘要

### 3. 对反馈采取动作

- `Critical`：立即修复
- `Important`：继续推进前修复
- `Minor`：可以记录待后续处理
- 如果评审有误：用技术理由反驳

## 示例

```text
[刚完成任务 2：补充验证功能]

你：在继续之前，我先请求一次代码评审。

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[分派 superpowers:code-reviewer 子代理]
  WHAT_WAS_IMPLEMENTED: 会话索引的验证与修复函数
  PLAN_OR_REQUIREMENTS: doc/specs/<需求目录名>/tasks.md 中的任务 2
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661
  DESCRIPTION: 新增 verifyIndex() 与 repairIndex()，覆盖 4 类问题

[子代理返回]
  Strengths: 架构清晰，测试扎实
  Issues:
    Important: 缺少进度提示
    Minor: 报告间隔使用了魔法数字 100
  Assessment: 可以继续，但建议先修 Important 问题

你：[修复进度提示]
[继续任务 3]
```

## 与工作流的集成

### 子代理驱动开发

- 每个任务后都做一次评审
- 尽早拦截问题，避免问题层层叠加
- 修完再进入下一个任务

### 执行计划模式

- 每个批次（例如 3 个任务）后做一次评审
- 根据反馈修正，再继续下一批

### 临时开发

- 合并前评审
- 卡住时评审

## 红线

**绝不要：**

- 因为“这很简单”就跳过评审
- 忽略 `Critical` 级别问题
- 带着未修复的 `Important` 问题继续推进
- 对有效的技术反馈强词夺理

**如果评审错了：**

- 用技术理由明确反驳
- 展示代码或测试证据
- 必要时请求进一步澄清

模板位置：`./code-reviewer.md`
