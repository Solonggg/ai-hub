# Claude Code 工具映射

这套 skills 来自跨平台来源，部分文档里仍会出现旧工具名。
在 Claude Code 中按下表理解即可：

| skill 中的写法 | Claude Code 对应方式 |
|----------------|----------------------|
| `Task`（分派子代理） | `Agent` tool |
| 多次 `Task` 并行调用 | 在同一条消息中发起多个 `Agent` tool 调用 |
| 等待 Task 返回结果 | Agent 完成后自动返回结果（前台模式），或使用 `run_in_background` 后台运行并等待通知 |
| Task 自动结束 | Agent 执行完毕后自动结束 |
| `TodoWrite`（任务追踪） | `TodoWrite` tool（名称相同） |
| `Skill` 工具 | `Skill` tool（调用 `~/.claude/skills/` 下已注册的 skill） |
| `Read` / `Write` / `Edit` | `Read` / `Write` / `Edit`（名称相同） |
| `Bash` | `Bash` tool（名称相同） |
| `Grep` / `Glob` | `Grep` / `Glob`（名称相同） |

## 子代理使用

Claude Code 原生支持 `Agent` tool 分派子代理，无需额外配置。

常用参数：
- `subagent_type`：可选 `general-purpose`、`Explore`、`Plan` 等
- `run_in_background`：设为 `true` 可后台运行，适合并行分派
- `isolation: "worktree"`：在独立 git worktree 中执行，适合需要隔离的任务

使用 `dispatching-parallel-agents`、`subagent-driven-development` 等 skill 时，直接使用 `Agent` tool 即可。

## 具名代理的处理方式

某些 skill 会引用具名代理模板，例如 `code-reviewer.md`。
Claude Code 的处理方式是：

1. 找到对应提示词文件，例如 `skills/requesting-code-review/code-reviewer.md`
2. 读取模板内容
3. 填入模板占位符
4. 用填充后的完整消息作为 `Agent` tool 的 `prompt` 参数分派子代理

| skill 中的指令 | Claude Code 对应做法 |
|----------------|----------------------|
| `Task tool (superpowers:code-reviewer)` | `Agent(prompt=<填充后的 code-reviewer.md 内容>)` |
| `Task tool (general-purpose)` | `Agent(prompt=<完整任务说明>)` |

### 建议的 prompt 包装方式

`prompt` 参数应包含完整上下文和明确指令：

```text
你的任务是立即执行下面的工作，并严格遵循说明。

<agent-instructions>
[填充后的代理提示词内容]
</agent-instructions>

现在开始执行，并且只按上面的要求输出结构化结果。
```

## 环境检查建议

涉及 worktree、分支收尾或提交前判断时，可先运行：

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

- `GIT_DIR != GIT_COMMON`：说明当前已经在 linked worktree 中
- `BRANCH` 为空：说明当前是 detached HEAD

遇到这类环境差异，应按实际状态调整 skill 落地方式，而不是机械执行。
