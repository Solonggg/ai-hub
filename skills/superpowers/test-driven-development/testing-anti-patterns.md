# 测试反模式

**在以下场景下加载本参考：**编写或修改测试、准备加入 mock、或想把“测试专用方法”加进生产代码时。

测试必须验证**真实行为**，不是验证 mock 自己是否按你写的那样工作。mock 只是隔离手段，不是被测对象本身。

**核心原则：**测代码做了什么，不测 mock 做了什么。

**严格执行 TDD，本来就能挡住大多数反模式。**

## 铁律

1. 不要测 mock 行为
2. 不要给生产类加仅供测试使用的方法
3. 不要在没搞清依赖关系前就乱 mock
4. mock 数据结构必须尽量贴近真实结构
5. 测试不是实现后的附属品

## 反模式 1：测的是 mock，不是行为

```typescript
// 错误：只是证明 mock 存在
test('renders sidebar', () => {
  render(<Page />);
  expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();
});
```

问题在于：

- 你验证的是 mock 是否被渲染，不是页面真实行为
- mock 在时测试就过，mock 不在时测试就挂
- 这几乎不能说明真实组件是否正常

用户常见纠偏句式：

```text
“我们现在测的是 mock 的行为吗？”
```

正确做法：

```typescript
// 正确：测真实组件行为，或者根本不要 mock
test('renders sidebar', () => {
  render(<Page />);
  expect(screen.getByRole('navigation')).toBeInTheDocument();
});
```

### 闸门问题

在对任何 mock 元素做断言前，先问自己：

```text
我是在验证真实组件行为，还是只在验证 mock 存在？
```

如果只是后者，就回退，改成测真实行为。

## 反模式 2：把测试专用方法塞进生产代码

```typescript
// 错误：destroy() 只在测试里用
class Session {
  async destroy() {
    await this._workspaceManager?.destroyWorkspace(this.id);
  }
}
```

问题在于：

- 生产类被测试逻辑污染
- 生产环境误调用会有风险
- 违反 YAGNI 和职责分离
- 容易混淆“对象生命周期”和“测试清理动作”

正确做法通常是把这些逻辑放进测试工具：

```typescript
export async function cleanupSession(session: Session) {
  const workspace = session.getWorkspaceInfo();
  if (workspace) {
    await workspaceManager.destroyWorkspace(workspace.id);
  }
}
```

### 闸门问题

在给生产类新增方法前，先问：

1. 这个方法是不是只有测试会用？
2. 这个类真的拥有这份资源的生命周期吗？

只要有一个答案是否定的，就不该把方法加进生产类。

## 反模式 3：不理解依赖链就乱 mock

```typescript
// 错误：mock 把测试依赖的副作用也一起抹掉了
test('detects duplicate server', async () => {
  vi.spyOn(serverManager, 'addServer').mockResolvedValue(undefined);
  await addServer(config);
  await addServer(config); // 本应抛错，但不会
});
```

问题在于：

- 被 mock 的真实方法原本带有测试依赖的副作用（例如写配置）
- “为了安全起见先 mock 掉”会直接破坏实际行为
- 测试可能因错误原因通过，也可能莫名其妙失败

正确做法是：mock 真正慢或外部的那一层，而不是把关键行为也一并抹掉。

### 闸门问题

在 mock 某个方法前，先问：

1. 真实方法有哪些副作用？
2. 当前测试是否依赖其中某些副作用？
3. 我是否真正理解这个测试在依赖什么？

如果答案不明确，先在**真实实现**下跑一遍，看清楚系统真实行为，再决定最小 mock 点。

## 反模式 4：不完整 mock

```typescript
// 错误：只 mock 你眼前觉得会用到的字段
const mockResponse = {
  id: '123',
  status: 'ok',
  // 缺少 metadata 等下游代码会访问的字段
};
```

问题在于：

- 你只模拟了自己知道的字段，隐藏了结构假设
- 下游代码可能依赖你没填的字段
- 测试通过了，但集成时会炸
- 这种测试会制造虚假信心

**铁规则：**mock 的数据结构应尽量镜像真实返回结构，而不是只保留当前断言要用的几个字段。

### 闸门问题

在手写 mock 响应前，先确认：

1. 真实 API / 返回体完整结构是什么？
2. 系统下游可能消费哪些字段？
3. 当前 mock 是否与真实 schema 足够一致？

如果拿不准，优先把文档里定义的字段全部带上。

## 反模式 5：把测试当成实现后的附属品

```text
✅ 功能写完了
❌ 还没写测试
❌ 但已经准备宣称完成
```

问题在于：

- 测试是实现的一部分，不是事后补件
- 这类情况本可被 TDD 提前拦住
- 没测试就不能说“做完了”

正确顺序应是：

1. 写失败测试
2. 看它失败
3. 写最小实现
4. 看它通过
5. 然后才允许说完成

## 当 mock 变得过于复杂

下面这些信号说明你可能根本不该继续堆 mock：

- mock 搭建代码比测试逻辑还长
- 为了让测试通过把一切都 mock 掉
- mock 缺少真实组件实际拥有的方法
- mock 一变，测试就碎

用户常见提醒：

```text
“这里真的需要 mock 吗？”
```

很多时候，用真实组件做集成测试，比维护复杂 mock 更简单、更可信。

## 为什么 TDD 能挡住这些反模式

1. **先写测试**：逼你先想清楚到底在测什么
2. **先看失败**：确认测试测中了真实行为，而不是 mock 假象
3. **最小实现**：减少测试专用 API 混进生产代码
4. **先看真实依赖**：你会先理解系统，再决定是否 mock

如果你发现自己在测试 mock 行为，通常说明你已经偏离了 TDD。

## 快速参考

| 问题 | 修正方式 |
|------|----------|
| 对 mock 元素做断言 | 改为测真实组件行为，或取消该 mock |
| 给生产代码加测试专用方法 | 挪到测试工具层 |
| 不理解依赖就 mock | 先理解依赖链，再做最小 mock |
| mock 结构不完整 | 尽量镜像真实 API 结构 |
| 测试作为事后补充 | 回到 TDD 流程 |
| mock 过于复杂 | 考虑改为集成测试 |

## 红旗

- 断言的是 `*-mock` 测试 ID
- 某个方法只在测试文件里会被调用
- mock 搭建占了测试的大半篇幅
- 去掉 mock 之后测试完全失真

## 底线

如果 TDD 暴露出你实际上在测 mock，而不是测系统行为，那说明你已经走偏了。

修正方法只有两个方向：

- 改成测真实行为
- 或者重新质疑这里到底是否应该 mock
