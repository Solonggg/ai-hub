# Superpowers Skills 说明

`superpowers` 下的 skills 主要是流程型能力，用来约束任务应该如何推进，而不是限定某个技术栈的实现细节。

一般可以按这个顺序理解：

1. 先决定当前任务属于哪种流程。
2. 再加载对应的 superpower skill。
3. 最后再叠加领域型 skill，例如 Java、数据库或项目规范类 skill。

## 各 Skill 作用

| Skill | 作用 | 典型使用场景 |
| --- | --- | --- |
| `using-superpowers` | 会话入口规则，要求先检查可能适用的 skills，避免跳过流程。 | 每次对话开始时先使用。 |
| `brainstorming` | 用于发散方案、澄清方向和探索备选设计。 | 新功能构思、交互设计、行为改造前。 |
| `writing-plans` | 把已有需求和设计拆成可执行任务计划。 | 文档齐全但还没开始编码时。 |
| `executing-plans` | 按既定实现计划逐步落地，并在检查点之间推进。 | 已经有明确计划，需要进入执行阶段时。 |
| `subagent-driven-development` | 把一个会话中的多项独立子任务拆开并行推进。 | 同一需求下有多个可以分开实现的任务时。 |
| `dispatching-parallel-agents` | 在多个彼此独立、无顺序依赖的任务之间并行分派。 | 两个以上任务互不影响，可以同时处理时。 |
| `test-driven-development` | 先写失败测试，再实现，再回归验证。 | 新功能开发或缺陷修复，且尚未开始写实现时。 |
| `systematic-debugging` | 先定位根因，再决定修复方案，避免拍脑袋改代码。 | 遇到 bug、测试失败、异常行为时。 |
| `receiving-code-review` | 消化评审意见，先判断反馈是否准确，再决定是否采纳。 | 收到 review 评论准备修改时。 |
| `requesting-code-review` | 在实现完成后组织一次结构化代码评审。 | 功能完成、准备合并或需要他人确认质量时。 |
| `verification-before-completion` | 在宣称完成前做最终验证，确保结论有证据支撑。 | 准备说“已修复”“已完成”“可提交”之前。 |
| `finishing-a-development-branch` | 在开发收尾阶段决定如何整理、合并和交付分支。 | 功能完成且测试通过，准备集成时。 |
| `using-git-worktrees` | 为隔离开发环境或并行处理任务创建独立工作区。 | 需要和当前工作区隔离，或同时处理多项开发工作时。 |
| `writing-skills` | 用于编写、修改和验证 skill 本身的内容与质量。 | 新建 skill、维护 skill、发布前检查 skill 时。 |

## 快速选择建议

- 不确定先做什么：先看 `using-superpowers`。
- 需要想方案：用 `brainstorming`。
- 已有方案要拆任务：用 `writing-plans`。
- 已有计划要开始干：用 `executing-plans`。
- 发现问题要修：先用 `systematic-debugging`，再根据情况配合 `test-driven-development`。
- 准备收尾：先做 `verification-before-completion`，再考虑 `requesting-code-review` 或 `finishing-a-development-branch`。
- 要维护 skill 自己：用 `writing-skills`。

## 补充说明

- `superpowers` 更偏“过程控制”。
- 领域规范仍应由对应 skill 补充，例如项目规范、语言规范、数据库规范等。
- 多个 skill 可以组合使用，但应优先使用能决定流程的那个 skill。
