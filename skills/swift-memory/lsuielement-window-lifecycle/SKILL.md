---
name: lsuielement-window-lifecycle
description: 在 LSUIElement（菜单栏驻留、无 Dock 图标）macOS app 中打开设置或面板窗口时出现窗口被其他前台 app 盖住、从一个窗口跳另一个窗口时第二个不出现、切换 Dock 图标显隐时当前窗口消失、重复打开窗口内容错乱、或自动粘贴粘到自己等症状时使用
---

# LSUIElement 应用的窗口生命周期

## 为什么 LSUIElement 特殊

`Info.plist` 的 `LSUIElement = YES` 让 app 成为菜单栏驻留进程：不在 Dock 出现、默认非活动。很多 `NSApp` API 对非活动 app 有"降级"行为，需要显式激活 + 显式 orderFront + 时序协调，不能像普通 app 那样拉就来。

## 四个必修动作

### 1. show 前先 `NSApp.activate(ignoringOtherApps: true)`

LSUIElement app 在收到"打开某窗口"事件时自身可能不活动。跳过 activate 直接 `makeKeyAndOrderFront`，窗口会被当前 frontmost app 盖住。

### 2. 从 A 窗口跳 B 窗口要延一帧

典型场景：面板点"设置"按钮 → 关面板 → 开设置窗口。三步挤在同一 runloop tick，AppKit 还没处理完 A 的关闭循环，B 会跑到旧 frontmost app 之下。

```swift
panelWindow.close()
DispatchQueue.main.async {
    self.settingsWindow.show(...)
}
```

### 3. 窗口实例复用

窗口设 `isReleasedWhenClosed = false`；`show()` 时先判断实例是否还在，在就 `makeKeyAndOrderFront`，不要每次重建 `NSHostingView`——重建会丢状态、可能触发 NSPopUpButton 缓存错乱。

### 4. 切 `setActivationPolicy` 时快照 + 恢复

`setActivationPolicy(.accessory)` 会短暂 deactivate app，**当前 key 窗口被 AppKit 带走**。用户切"显示 Dock 图标"开关时，他们正打开的设置窗口会凭空消失。

```swift
let visibleWindows = NSApp.windows.filter { $0.isVisible }
NSApp.setActivationPolicy(newPolicy)
NSApp.activate(ignoringOtherApps: true)
for w in visibleWindows { w.makeKeyAndOrderFront(nil) }
```

## 自动粘贴时序（剪贴板类 app）

关自己 → 激活之前的 app → 模拟 ⌘V，三段时序硬控：

```swift
close()
DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) {
    previousApp?.activate(options: .activateIgnoringOtherApps)
    DispatchQueue.main.asyncAfter(deadline: .now() + 0.06) {
        simulatePaste()
    }
}
```

50ms + 60ms 是实测下来最稳的值。少于这个值，目标 app 没激活完，粘贴会打到自己。

## 菜单栏图标深色下被染黑

AppKit 会根据菜单栏当前深浅把 `template` 图像自动反色；深色菜单栏下白线图标会被染黑看不清。

**修法**：预渲染一份纯白副本，`isTemplate = false` 跳过 AppKit 自动 tint。见 `references/menubar-fixed-white-icon.swift.txt`。

## 快速参考

| 症状 | 对应动作 |
|---|---|
| 点按钮打开窗口，窗口在别的 app 背后 | show 前 `NSApp.activate(ignoringOtherApps: true)` |
| 面板点按钮关自己 → 开设置，设置没出现 | `DispatchQueue.main.async` 延一帧再开 |
| 切 Dock 图标时当前窗口没了 | 切 policy 前快照，切后重 `makeKeyAndOrderFront` |
| 重开设置窗口内容错乱 | `isReleasedWhenClosed = false` 复用实例 |
| 自动粘贴粘到自己 app | 三段延时（50ms + 60ms） |
| 菜单栏图标深色下看不清 | 预渲染白色 + `isTemplate = false` |

## 代码模板

- `references/settings-window-reuse.swift.txt` — 复用实例的 show()
- `references/policy-switch-preserving-windows.swift.txt` — setDockIconVisible 保窗口
- `references/paste-automation-timing.swift.txt` — 自动粘贴三段延时
- `references/menubar-fixed-white-icon.swift.txt` — 菜单栏白图标

## 相关 skill

窗口玻璃/圆角细节见 `liquid-glass-window`；窗口 key 输入相关的 `canBecomeKey` 子类同样定义在那里。
