# Codex 工具映射

这套 skills 来自跨平台来源，部分文档里仍会出现旧工具名。  
在 Codex 中按下表理解即可：

| skill 中的写法 | Codex 对应方式 |
|----------------|----------------|
| `Task`（分派子代理） | `spawn_agent` |
| 多次 `Task` 并行调用 | 多次 `spawn_agent` 并行分派 |
| 等待 Task 返回结果 | `wait` |
| Task 自动结束 | `close_agent` |
| `TodoWrite`（任务追踪） | `update_plan` |
| `Skill` 工具 | Codex 原生按需加载 skills |
| `Read` / `Write` / `Edit` | 使用 Codex 原生文件能力 |
| `Bash` | 使用 Codex 原生 shell 能力 |

## 子代理前提

如果要使用 `dispatching-parallel-agents`、`subagent-driven-development` 等依赖多代理的 skill，请在 `~/.codex/config.toml` 中启用：

```toml
[features]
multi_agent = true
```

## 具名代理的处理方式

某些 skill 会引用具名代理模板，例如 `code-reviewer.md`。  
Codex 当前没有同等的“具名代理注册表”，因此处理方式是：

1. 找到对应提示词文件，例如 `skills/requesting-code-review/code-reviewer.md`
2. 读取模板内容
3. 填入模板占位符
4. 用填充后的完整消息分派一个 `worker` 子代理

| skill 中的指令 | Codex 对应做法 |
|----------------|----------------|
| `Task tool (superpowers:code-reviewer)` | `spawn_agent(agent_type=\"worker\", message=...)` |
| `Task tool (general-purpose)` | 直接将完整任务说明作为 `spawn_agent(..., message=...)` 的消息体 |

### 建议的消息包装方式

`message` 属于用户级输入，建议显式包裹规则块，提高遵循率：

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
