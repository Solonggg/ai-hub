# 基于条件的等待

## 概览

遇到异步测试或时序问题时，优先等待“某个条件成立”，而不是写死等待时间。

**核心原则：**等待你真正关心的状态变化，而不是赌一个固定 timeout 恰好足够。

## 何时使用

以下情况通常应使用条件等待，而不是任意 `sleep` / `setTimeout`：

- 测试偶发失败
- 异步状态更新不稳定
- 事件处理完成时机不固定
- CI 比本地慢，固定等待经常不够
- 本地机器快，固定等待又显得过长

## 核心模式

```typescript
await waitFor(() => {
  expect(screen.getByText('Completed')).toBeInTheDocument();
});
```

要点是：  
**写出“完成时应该成立的条件”，然后等它成立。**

## 常见模式

### 等待元素出现

```typescript
await waitFor(() => {
  expect(screen.getByRole('dialog')).toBeInTheDocument();
});
```

### 等待元素消失

```typescript
await waitFor(() => {
  expect(screen.queryByText('Loading')).not.toBeInTheDocument();
});
```

### 等待状态值变化

```typescript
await waitFor(() => {
  expect(store.getState().status).toBe('ready');
});
```

### 等待异步副作用完成

```typescript
await waitFor(() => {
  expect(apiMock).toHaveBeenCalledTimes(1);
});
```

## 实现建议

- 条件必须描述真实业务状态，而不是描述“等一会儿”
- 等待条件应尽量小、单一、可验证
- 如果一个条件很难写，通常意味着你对系统完成态定义不清晰

## 常见错误

### 错误：固定等待

```typescript
await sleep(500);
```

问题：

- 机器慢时 500ms 不够
- 机器快时 500ms 又浪费时间
- 测试会变慢且仍不稳定

### 错误：等待与目标无关的条件

```typescript
await waitFor(() => {
  expect(true).toBe(true);
});
```

这不叫等待，只是自欺欺人。

### 错误：一次等待塞多个关注点

```typescript
await waitFor(() => {
  expect(a).toBe(1);
  expect(b).toBe(2);
  expect(c).toBe(3);
});
```

如果可以拆，尽量拆。这样失败时更容易知道卡在哪。

## 什么时候固定 timeout 反而是对的

固定 timeout 只在少数场景下合理：

- 你就是在测试 timeout 行为本身
- 协议规范明确要求“等待至少 N 毫秒”
- 产品逻辑真的依赖固定冷却时间

除此之外，默认认为固定等待是可疑的。

## 实际效果

把任意 timeout 改成条件等待，通常会带来：

- 更稳定的测试
- 更快的测试执行
- 更容易定位失败原因
- 更少的 CI 偶发红灯
