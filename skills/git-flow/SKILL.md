---
name: git-flow
description: 用户说"提交代码"、"合并到dev"、"合并到master"时，按预定义的 git 工作流执行操作。
---

# Git Flow 工作流

## 概览

三个操作场景，通过用户关键词路由。所有操作前先确认当前工作目录对应的项目名（取工作目录最后一级目录名，如 `iho-nursing`）。

---

## 场景一：提交代码

**触发词**：`提交代码 [注释]`

**执行步骤**：

1. 检查当前分支，若不是 `dev_wangjie` 则自动切换：`git checkout dev_wangjie`
2. `git add -A`
3. 确定 commit message：
   - 用户提供了注释（如 `提交代码 feat:统一打印接口`）→ 使用用户给的注释
   - 用户只说 `提交代码` → 从 memory 读取该项目上次的提交注释，路径为 `~/.claude/projects/-Users-wangjie-workspace-project-{项目名}/memory/last_commit_msg.md`；若 memory 不存在则提示用户提供注释
4. `git commit -m "注释"`
5. `git push origin dev_wangjie`
6. 提交成功后，将本次注释写入对应项目的 memory 文件 `last_commit_msg.md`，格式：

```markdown
---
name: last_commit_msg
description: 该项目上次 git commit 的注释，用于"提交代码"时无注释的默认值
type: project
---

{commit message}
```

**注意**：
- 提交前不需要用户确认，直接执行
- push 也直接执行，不需要确认

---

## 场景二：合并到 dev

**触发词**：`合并到dev`

**执行步骤**：

1. `git pull origin dev_wangjie`（拉取开发分支最新代码）
2. `git checkout develop`
3. `git pull origin develop`（拉取目标分支最新代码）
4. `git merge dev_wangjie`
5. 若合并无冲突：`git push origin develop`，然后 `git checkout dev_wangjie` 切回开发分支
6. 报告合并及 push 结果

**冲突处理**：若合并产生冲突，停下来告知用户冲突文件列表，不自动解决，不 push，不切换分支。

---

## 场景三：合并到 master

**触发词**：`合并到master`

**执行步骤**：

1. `git pull origin dev_wangjie`（拉取开发分支最新代码）
2. `git checkout master`
3. `git pull origin master`（拉取目标分支最新代码）
4. `git merge dev_wangjie`
5. 报告合并结果，**不执行 push**，提示用户自行 push

**冲突处理**：若合并产生冲突，停下来告知用户冲突文件列表，不自动解决。

---

## 通用规则

- 合并完成后（场景二、三），**不要**自动切回 dev_wangjie，保持在目标分支上，方便用户检查后 push。
- 每个项目的 memory 路径互相独立，项目名从当前工作目录推断。
- 执行过程中如遇到异常（未提交的变更导致 checkout 失败等），停下来告知用户，不强制操作。
