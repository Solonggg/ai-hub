---
name: using-git-worktrees
description: 在开始需要与当前工作区隔离的功能开发，或在执行实现计划之前需要隔离环境时使用
---

# 使用 Git Worktrees

## 概览

Git worktree 允许你在共享同一个仓库对象库的前提下，开出多个彼此隔离的工作目录，并在不同分支上并行工作，而不需要来回切分支。

**核心原则：**目录选择要系统化，安全校验要先做足，隔离环境才可靠。

**开始时要明确说明：**“我正在使用 `using-git-worktrees` skill 来建立隔离工作区。”

## 目录选择流程

按以下优先级依次判断：

### 1. 先检查现有目录

```bash
ls -d .worktrees 2>/dev/null
ls -d worktrees 2>/dev/null
```

**如果存在：**

- 优先使用 `.worktrees`
- 只有 `worktrees` 存在时才使用它

### 2. 检查 `AGENTS.md`

```bash
grep -i "worktree.*director" AGENTS.md 2>/dev/null
```

**如果用户已有偏好：**直接按偏好走，不需要再问。

### 3. 问用户

如果本地没有现成目录，`AGENTS.md` 里也没有偏好，则询问用户：

```text
没有发现现成的 worktree 目录。你希望我把 worktree 建在哪里？

1. .worktrees/（项目内、隐藏目录）
2. ~/.config/superpowers/worktrees/<project-name>/（全局目录）

请选择一个。
```

## 安全校验

### 针对项目内目录（`.worktrees` 或 `worktrees`）

**在创建 worktree 之前，必须确认该目录已被 git 忽略。**

```bash
git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
```

**如果没有被忽略：**

根据“发现坏的东西要立刻修”的原则：

1. 在 `.gitignore` 中加入对应目录
2. 提交该变更
3. 再继续创建 worktree

为什么必须这样做：否则 worktree 目录里的内容可能污染仓库状态，甚至被误提交。

### 针对全局目录（`~/.config/superpowers/worktrees`）

因为目录本身不在项目仓库内，所以不需要做 `.gitignore` 校验。

## 创建步骤

### 1. 识别项目名

```bash
project=$(basename "$(git rev-parse --show-toplevel)")
```

### 2. 创建 worktree

```bash
case $LOCATION in
  .worktrees|worktrees)
    path="$LOCATION/$BRANCH_NAME"
    ;;
  ~/.config/superpowers/worktrees/*)
    path="~/.config/superpowers/worktrees/$project/$BRANCH_NAME"
    ;;
esac

git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"
```

### 3. 执行项目初始化

自动根据项目类型执行对应初始化：

```bash
# Node.js
if [ -f package.json ]; then npm install; fi

# Rust
if [ -f Cargo.toml ]; then cargo build; fi

# Python
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f pyproject.toml ]; then poetry install; fi

# Go
if [ -f go.mod ]; then go mod download; fi
```

### 4. 验证干净基线

创建完 worktree 后，先跑一遍项目测试，确认当前基线是干净的：

```bash
npm test
cargo test
pytest
go test ./...
```

**如果测试失败：**

汇报失败内容，并询问用户是继续还是先排查基线问题。

**如果测试通过：**

说明环境已就绪。

### 5. 汇报结果

```text
worktree 已就绪：<full-path>
测试通过（<N> 个测试，0 失败）
可以开始实现 <feature-name>
```

## 快速参考

| 情况 | 处理方式 |
|------|----------|
| `.worktrees/` 存在 | 用它，并确认已被忽略 |
| `worktrees/` 存在 | 用它，并确认已被忽略 |
| 两者都存在 | 优先 `.worktrees/` |
| 两者都不存在 | 查 `AGENTS.md`，再问用户 |
| 目录未被忽略 | 先改 `.gitignore` 并提交 |
| 基线测试失败 | 汇报失败并询问是否继续 |
| 没有常见项目文件 | 跳过依赖安装 |

## 常见错误

### 跳过忽略校验

- 问题：worktree 内容被 git 跟踪，污染状态
- 修正：项目内目录必须先 `git check-ignore`

### 擅自决定目录位置

- 问题：破坏项目约定，导致团队不一致
- 修正：严格遵守“现有目录 > `AGENTS.md` > 询问用户”的顺序

### 基线失败还硬着头皮继续

- 问题：后续新问题和旧问题混在一起，无法分辨
- 修正：先汇报，再由用户决定是否继续

### 初始化命令写死

- 问题：跨语言项目容易失效
- 修正：根据项目文件自动判断

## 示例流程

```text
你：我正在使用 using-git-worktrees skill 建立隔离工作区。

[检查到 .worktrees/ 存在]
[确认 git check-ignore 表明 .worktrees/ 已被忽略]
[执行 git worktree add .worktrees/auth -b feature/auth]
[运行 npm install]
[运行 npm test，47 个通过]

worktree 已就绪：/Users/jesse/myproject/.worktrees/auth
测试通过（47 个测试，0 失败）
可以开始实现 auth 功能
```

## 红线

**绝不要：**

- 在项目内目录未确认被忽略前就创建 worktree
- 跳过基线测试
- 基线失败仍不询问就继续
- 目录位置有歧义时擅自决定
- 跳过 `AGENTS.md` 检查

**必须做到：**

- 按优先级选择目录：现有目录 > `AGENTS.md` > 询问用户
- 项目内目录先做忽略校验
- 自动识别并执行初始化
- 验证干净测试基线

## 集成关系

**谁会调用它：**

- **`brainstorming`**：设计确认后，如需进入实现阶段
- **`subagent-driven-development`**：开始执行任务前必须先建隔离工作区
- **`executing-plans`**：开始执行任务前必须先建隔离工作区
- 任何需要隔离环境的其他 skill

**常配合：**

- **`finishing-a-development-branch`**：开发结束后负责收尾与清理
