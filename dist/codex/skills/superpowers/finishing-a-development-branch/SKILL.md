---
name: finishing-a-development-branch
description: 在实现已完成、测试全部通过，且需要决定如何集成这部分工作时使用
---

# 完成开发分支

## 概览

这个 skill 用于在开发完成后，以清晰、受控的方式结束当前分支上的工作，并按用户选择完成集成或清理。

**核心原则：**先验证测试，再给出选项，然后执行用户选择，最后做必要清理。

**开始时要明确说明：**“我正在使用 `finishing-a-development-branch` skill 来完成这项工作。”

## 执行流程

### 第 1 步：验证测试

**在给用户任何后续选项之前，必须先确认测试通过。**

```bash
# 运行项目测试
npm test / cargo test / pytest / go test ./...
```

**如果测试失败：**

```text
测试失败（<N> 个失败项）。在完成收尾前必须先修复：

[展示失败内容]

在测试通过前，不能继续执行合并或创建 PR。
```

此时停止，不进入第 2 步。

**如果测试通过：**继续第 2 步。

### 第 2 步：确定基线分支

```bash
# 尝试推断基线分支
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
```

如果不能确认，也可以直接问用户：

```text
当前分支看起来是从 <base-branch> 切出来的，这个判断对吗？
```

### 第 3 步：给出固定选项

必须严格给出下面这 4 个选项，不要擅自加解释或扩展：

```text
实现已经完成。接下来你希望怎么处理？

1. 本地合并回 <base-branch>
2. 推送并创建 Pull Request
3. 保持当前分支不动（我之后再处理）
4. 丢弃这部分工作

请选择一个选项。
```

### 第 4 步：执行用户选择

#### 选项 1：本地合并

```bash
git checkout <base-branch>
git pull
git merge <feature-branch>
<test command>
git branch -d <feature-branch>
```

合并后测试仍需再次验证。完成后进入第 5 步清理。

#### 选项 2：推送并创建 PR

```bash
git push -u origin <feature-branch>

gh pr create --title "<title>" --body "$(cat <<'EOF'
## 摘要
<2-3 条变更摘要>

## 验证计划
- [ ] <验证步骤>
EOF
)"
```

完成后进入第 5 步清理。

#### 选项 3：保持现状

直接汇报：

```text
保留分支 <name>。worktree 保留在 <path>。
```

**不要清理 worktree。**

#### 选项 4：丢弃工作

必须先做显式确认：

```text
这会永久删除以下内容：
- 分支 <name>
- 所有提交：<commit-list>
- worktree：<path>

请输入 `discard` 以确认。
```

只有在用户给出**精确确认**后才能继续：

```bash
git checkout <base-branch>
git branch -D <feature-branch>
```

然后进入第 5 步清理。

### 第 5 步：清理 worktree

**适用于选项 1、2、4。**

先检查当前分支是否位于某个 worktree 中：

```bash
git worktree list | grep $(git branch --show-current)
```

如果是：

```bash
git worktree remove <worktree-path>
```

**选项 3 不清理。**

## 快速参考

| 选项 | 是否合并 | 是否推送 | 是否保留 Worktree | 是否清理分支 |
|------|----------|----------|-------------------|--------------|
| 1. 本地合并 | 是 | 否 | 否 | 是 |
| 2. 创建 PR | 否 | 是 | 是 | 否 |
| 3. 保持现状 | 否 | 否 | 是 | 否 |
| 4. 丢弃工作 | 否 | 否 | 否 | 是（强制） |

## 常见错误

**跳过测试验证**

- 问题：把坏代码合并掉，或者提交出失败 PR
- 修正：给选项前必须先跑测试

**问开放式问题**

- 问题：“接下来怎么办？”太模糊
- 修正：严格给出 4 个固定选项

**错误清理 worktree**

- 问题：在本不该删除的时候把工作区删掉
- 修正：只在选项 1、2、4 进入清理步骤；选项 3 保留

**丢弃前未确认**

- 问题：误删用户工作
- 修正：必须要求用户输入精确确认词 `discard`

## 红线

**绝不能：**

- 在测试失败时继续收尾流程
- 合并后不重新验证结果
- 未经确认就删除工作
- 未经明确要求就强推

**必须做到：**

- 先验证测试，再给选项
- 始终给出固定 4 选项
- 丢弃前必须拿到精确确认
- 仅在需要时清理 worktree

## 集成关系

**谁会调用它：**

- **`subagent-driven-development`**：所有任务完成后
- **`executing-plans`**：所有批次执行结束后

**常与之配合的 skill：**

- **`using-git-worktrees`**：本 skill 负责清理它创建出的隔离工作区
