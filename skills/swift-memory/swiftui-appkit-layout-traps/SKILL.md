---
name: swiftui-appkit-layout-traps
description: 在 SwiftUI（尤其嵌入在 NSHostingView 内）写布局时出现 toolbar 莫名吃掉整个父容器垂直空间、ScrollViewProxy.scrollTo 悄无反应、Environment/主题/语言切换后视图不更新、中文输入法组字被自定义键盘 monitor 吞掉等反直觉症状时使用
---

# SwiftUI × AppKit 嵌入场景下的布局与事件陷阱

## 何时使用

在 SwiftUI 代码里看到下面任一症状：

- 加了个小组件（如左上角关闭按钮），父容器其他 sibling 被挤扁或挤出视口
- `ScrollViewProxy.scrollTo(...)` 被调用但视图不滚
- 改了 `@State theme` / `@State language` 后部分视图保留旧值
- 自定义 `NSEvent.addLocalMonitor` 监听箭头键后，中文输入法候选被误切换

## 陷阱清单

### 1. `VStack { A; Spacer() }` 让父容器变 flex-height

**现象**：为了把小组件钉到顶部，写了：

```swift
ZStack {
    HStack { tabs }
    VStack {
        HStack { closeButton; Spacer() }
        Spacer(minLength: 0)   // ← 毒药
    }
}
```

VStack 里的 `Spacer()` 让整个 ZStack 在**父**布局协商时被标为"愿意扩展垂直空间"。toolbar 贪婪吃掉父 VStack 几乎所有高度，ScrollView 被挤出视口。

**修**：改用 `.overlay(alignment: .topLeading)`——overlay 不参与父测量。

```swift
HStack { tabs }
    .overlay(alignment: .topLeading) {
        CloseButton()
            .padding(.leading, 10).padding(.top, 10)
    }
```

### 2. `ForEach(_.enumerated())` 的 `id:` 只做 diff，不保证可滚定位

**现象**：`ScrollViewProxy.scrollTo(item.id, anchor: .center)` 对 LazyVStack 的未实例化行无效。

**修**：每行**额外**显式 `.id(item.id)`；`scrollTo` 前 `DispatchQueue.main.async` 让 state 先 apply：

```swift
ForEach(Array(items.enumerated()), id: \.element.id) { idx, item in
    Row(item: item)
        .id(item.id)   // ← 这一行不能省
}
// 调用处
DispatchQueue.main.async {
    withAnimation { proxy.scrollTo(targetId, anchor: .center) }
}
```

### 3. Environment 一次性解析

**现象**：切换主题 / 语言后，NSPopUpButton（Picker.menu 背后的 AppKit 控件）、缓存 Color、`String(localized:)` 不重新取值。

**修**：给受影响子树加 `.id("\(theme)-\(language)")` 组合键，强制 remount。

### 4. `NSEvent.addLocalMonitor(.keyDown)` 会吞 IME 组字

**现象**：在 SwiftUI 里装全局快捷键监听，中文输入法输入时候选被 ↑↓ 当成应用导航键误切换。

**修**：monitor 回调**第一行**放行 IME：

```swift
keyMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { event in
    if NSTextInputContext.current?.client.hasMarkedText() == true {
        return event   // 让 IME 先拿到
    }
    // ... 自己的处理
}
```

### 5. 用 `DragGesture` / `mouseDownCanMoveWindow` 拖 borderless 窗口

**现象**：在 NSHostingView 里用这两条路，拖拽经常静默失效。

**修**：包一层 `NSViewRepresentable`，`mouseDown` 里调 `window?.performDrag(with: event)`。完整模板见 `liquid-glass-window` skill 的 `window-drag-catcher.swift.txt`。

## 快速参考

| 症状 | 哪条陷阱 |
|---|---|
| 顶部小组件把 ScrollView 挤没 | 陷阱 1 |
| scrollTo 不生效 | 陷阱 2 |
| 主题/语言切了但部分视图陈旧 | 陷阱 3 |
| 中文输入被吞 | 陷阱 4 |
| 面板拖不动 | 陷阱 5 |

## 代码模板

- `references/overlay-vs-zstack.swift.txt` — 顶贴 overlay 模板（陷阱 1）
- `references/scroll-to-selected.swift.txt` — 键盘选中滚动到可视（陷阱 2）
- `references/ime-safe-key-monitor.swift.txt` — IME 友好键盘监听（陷阱 4）
