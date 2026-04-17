---
name: using-superpowers
description: 在每次对话开始时使用，包括回答任何澄清问题之前
---

<SUBAGENT-STOP>
如果你是被分派出来执行某个具体任务的子代理，则跳过本 skill。
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
只要你觉得某个 skill 有哪怕 1% 的可能适用，就必须先检查它。

如果某个 skill 适用于当前任务，你没有选择权，必须使用。
</EXTREMELY-IMPORTANT>

# 使用 Superpowers

## 指令优先级

对 Claude Code 来说，优先级如下：

1. 用户显式指令（`CLAUDE.md`、直接要求）
2. Superpowers skills
3. 默认系统行为

如果 `CLAUDE.md` 说”不要用 TDD”，而某个 skill 写着”始终使用 TDD”，听用户的。

## 在 Claude Code 中如何访问 skills

使用 `Skill` tool 调用。调用后 skill 的内容会被加载并展示——直接遵循即可。不要用 Read tool 读取 skill 文件。

做法是：

1. 先判断当前任务是否可能命中某个 skill
2. 一旦命中，就通过 `Skill` tool 调用该 skill
3. 不要凭记忆假设 skill 内容没变

如需看工具映射，查看 `references/claude-code-tools.md`。

## 总规则

**在做出任何回复或动作之前，先检查相关或被点名的 skill。**

- 哪怕只有 1% 的可能适用，也先检查
- 检查后如果发现不适用，可以不用继续沿用
- 但“先检查”这一步不能省

## 危险信号

一旦脑中出现下面这些想法，说明你在为绕过流程找借口，应立刻停下：

- “这只是个简单问题”
- “我先随便看看代码再说”
- “我记得这个 skill 怎么写”
- “这次不需要正式流程”
- “我先做一小步，等下再补”

这些都不成立。只要有对应 skill，就先加载。

## 技能优先级

多个 skill 同时可能适用时：

1. 先流程型 skill，例如 `brainstorming`、`systematic-debugging`
2. 再实现型或领域型 skill

流程型 skill 决定“怎么做”，实现型 skill 决定“具体怎么落地”。

## 关于用户指令

用户指令定义“做什么”，skill 定义“怎么做”。

“加个功能”“修个问题”“写个计划”都不意味着可以跳过 skill 流程。
