---
name: liquid-glass-window
description: 在 macOS 26+ 上用 SwiftUI + NSWindow/NSPanel 做 Liquid Glass 玻璃窗口时，出现窗口四周暗色描边、四角硬阴影，或电脑重启后首次打开窗口材质变灰块/纯色等症状时使用
---

# Liquid Glass 玻璃窗口稳定配方

## 何时使用

用 `NSPanel` / `NSWindow` + `NSHostingView` 承载 SwiftUI `.glassEffect(_:in:)`，命中任一症状：

- 窗口四周有 1-2px 暗色边 / hairline 黑框
- 四角出现方形硬阴影
- 冷启动或系统重启后首次渲染时玻璃变成灰块 / 纯色
- 圆角外边缘露出一圈暗色

## 症状 → 根因对照

| 症状 | 根因 |
|---|---|
| 四周 hairline 暗描边 | styleMask 含 `.titled`，AppKit themeFrame 画出来的 |
| 四角方形硬阴影 | `hasShadow = true` 采样的是方形 backing alpha |
| 冷启动首帧灰块 | WindowServer / Metal 合成器未热身，`.glassEffect` 首次采样失败 |
| 圆角外露暗色 | SwiftUI `.glassEffect(in:)` 的 R 与 CALayer `cornerRadius` 不一致，中间出现 alias 缝 |

## 核心规则（缺一不可）

1. **styleMask 必须 `.borderless`**（不要 `.titled`）
2. **窗口透明三件套**：`backgroundColor = .clear` + `isOpaque = false` + `hasShadow = true`
3. **NSHostingView CALayer 层裁圆**：
   - `wantsLayer = true`
   - `layer?.cornerRadius = R` / `cornerCurve = .continuous` / `masksToBounds = true`
   - `layer?.backgroundColor = NSColor.clear.cgColor`
4. **SwiftUI `.glassEffect(in: RoundedRectangle(cornerRadius: R))` 的 R 必须等于 CALayer cornerRadius**
5. **首帧唤醒合成器**：`makeKeyAndOrderFront(nil)` 后 `DispatchQueue.main.async` 执行 `invalidateShadow() + displayIfNeeded()`
6. **borderless 窗口需能成为 key**：子类化 NSWindow/NSPanel 覆盖 `canBecomeKey: Bool { true }`，否则 TextField/快捷键录入收不到输入

## 为什么要两层裁圆（SwiftUI + CALayer）

`.glassEffect(in: RoundedRectangle(cornerRadius: R))` 只把**材质**限在圆角内，不裁 NSHostingView 整体 backing；material composite 会在 1-2px 内渗到方形窗口边缘，在透明窗口上叠加成暗边。CALayer 的 `cornerRadius + masksToBounds` 从**合成层**再裁一次，保证 backing store 的 alpha 就是圆角形状 —— `hasShadow` 自然跟随圆角，不会在四角堆方形硬阴影。

## 代码模板

- `references/borderless-glass-window.swift.txt` — NSWindow + SwiftUI 内容的完整样板
- `references/floating-panel.swift.txt` — 非激活浮动面板（HUD 风格）
- `references/window-drag-catcher.swift.txt` — borderless 窗口自绘拖拽区

## 常见错误

- 只改 styleMask 到 borderless、不加 CALayer 裁圆 → material 外溢成暗边
- 只加 CALayer、不 async invalidateShadow → 冷启动首帧仍灰块
- SwiftUI 和 CALayer 两处 cornerRadius 写得不一样 → 圆弧衔接处出暗边
- 忘记 `canBecomeKey` → 窗口内 TextField 完全无法聚焦
