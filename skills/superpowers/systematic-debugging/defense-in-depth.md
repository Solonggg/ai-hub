# 纵深防御式校验

## 概览

当一个 bug 是由非法数据引起时，只在一个地方加校验通常看起来已经够了。但单点校验很容易被其他代码路径、重构或 mock 绕过去。

**核心原则：**数据经过的每一层都应做校验，把 bug 从“容易漏过”变成“结构上不可能发生”。

## 为什么要多层校验

单层校验的心态是：

- “这个 bug 我们修掉了”

多层校验的目标是：

- “这个 bug 以后很难再以同样方式出现”

不同层能拦住不同问题：

- 入口校验挡住大多数非法输入
- 业务层校验挡住上下文相关的边界情况
- 环境保护挡住特定运行环境下的危险行为
- 调试日志在前几层漏过时，留下法证线索

## 四层防线

### 第 1 层：入口校验

**目的：**在 API 边界就拒绝明显非法的输入

```typescript
function createProject(name: string, workingDirectory: string) {
  if (!workingDirectory || workingDirectory.trim() === '') {
    throw new Error('workingDirectory cannot be empty');
  }
  if (!existsSync(workingDirectory)) {
    throw new Error(`workingDirectory does not exist: ${workingDirectory}`);
  }
  if (!statSync(workingDirectory).isDirectory()) {
    throw new Error(`workingDirectory is not a directory: ${workingDirectory}`);
  }
  // ... proceed
}
```

### 第 2 层：业务逻辑校验

**目的：**确保数据对当前操作来说是合理的

```typescript
function initializeWorkspace(projectDir: string, sessionId: string) {
  if (!projectDir) {
    throw new Error('projectDir required for workspace initialization');
  }
  // ... proceed
}
```

### 第 3 层：环境保护

**目的：**在特定上下文中阻止危险操作

```typescript
async function gitInit(directory: string) {
  if (process.env.NODE_ENV === 'test') {
    const normalized = normalize(resolve(directory));
    const tmpDir = normalize(resolve(tmpdir()));

    if (!normalized.startsWith(tmpDir)) {
      throw new Error(
        `Refusing git init outside temp dir during tests: ${directory}`
      );
    }
  }
  // ... proceed
}
```

### 第 4 层：调试留痕

**目的：**当前三层都没挡住时，至少留下足够上下文用于定位

```typescript
async function gitInit(directory: string) {
  const stack = new Error().stack;
  logger.debug('About to git init', {
    directory,
    cwd: process.cwd(),
    stack,
  });
  // ... proceed
}
```

## 如何应用这个模式

发现 bug 后：

1. **先追数据流**：坏值从哪里来，最后在哪里被用到？
2. **列出所有检查点**：数据经过了哪些层？
3. **每层都补校验**：入口、业务、环境、调试
4. **逐层测试**：尝试绕过第 1 层，确认第 2 层还能拦住

## 来自会话的例子

问题：空的 `projectDir` 导致 `git init` 在源码目录执行

**数据流：**

1. 测试初始化 -> 传入空字符串
2. `Project.create(name, '')`
3. `WorkspaceManager.createWorkspace('')`
4. `git init` 实际在 `process.cwd()` 执行

**补上的四层防线：**

- 第 1 层：`Project.create()` 校验非空、存在、可写
- 第 2 层：`WorkspaceManager` 校验 `projectDir` 非空
- 第 3 层：`WorktreeManager` 在测试中拒绝对临时目录外执行 `git init`
- 第 4 层：执行 `git init` 前打出栈信息和上下文日志

**结果：**1847 个测试全部通过，且原问题无法再复现

## 关键洞见

四层都需要。实际调试中，每一层都曾拦下过其他层没挡住的问题：

- 不同代码路径绕过了入口校验
- mock 绕过了业务层检查
- 不同平台上的边界情况需要环境保护
- 调试留痕帮助识别结构性误用

**不要在单点校验处停下。**  
能做成多层防线，就不要只留一个门卫。
