---
name: macos-appearance-switching
description: 在 SwiftUI + AppKit 混用的 macOS app 中实现浅色/深色/跟随系统三档主题切换，出现从手动深色切回"跟随系统"仍停留在深色、NSPopUpButton(Picker.menu) 不跟随主题、或切主题后子视图保留陈旧外观等症状时使用
---

# macOS 三档主题切换的两个坑

## 何时使用

做 menu-bar app / NSPanel + NSWindow + NSHostingView 的 macOS app，要支持 Light / Dark / 跟随系统三档可靠切换。典型症状：

- 从手动"深色"切回"跟随系统"，UI 仍停留在深色
- NSPopUpButton（SwiftUI `Picker` 的 `.menu` 样式）背景色不跟随主题
- 某些 SwiftUI 子视图在切换主题后保留陈旧 Color

**关键认识**：这不是一个坑，而是**两个独立的坑叠加**，只修其中一个都不够。

## 坑 1：`NSApp.effectiveAppearance` 在清空 override 后不立刷新

### 现象

```swift
NSApp.appearance = nil             // 想清掉手动深色 override
let app = NSApp.effectiveAppearance // ← 可能仍然返回 darkAqua
```

macOS 26 实测可复现：刚清掉 `NSApp.appearance` 的瞬间读 `effectiveAppearance`，AppKit 的内部缓存还没刷，拿到的是上一次被 pin 住的值。

### 修法：直接读全局偏好

```swift
let isDark = UserDefaults.standard
    .string(forKey: "AppleInterfaceStyle") == "Dark"
```

这个 key 由 macOS 维护在 `.GlobalPreferences`，深色时为 `"Dark"`，浅色时 key 不存在——也是 `AppleInterfaceThemeChangedNotification` 通知同源的值，保证一致。

## 坑 2：SwiftUI `.preferredColorScheme` 污染 NSHostingView.appearance

### 现象

- 当视图层写了 `.preferredColorScheme(.dark)`，SwiftUI 会在底层把 **`NSHostingView`（= `window.contentView`）自身 `appearance`** 设成 `.darkAqua`
- NSView 的 `appearance` 是**自下而上继承**的：contentView **优先级高于** window
- 之后切 `.preferredColorScheme(nil)` 回"跟随系统"时，SwiftUI **不会**主动清 contentView 残留
- 只写 `window.appearance = aqua` 会被 contentView 的 darkAqua 盖住，界面继续深色

### 修法：集中 apply 函数同时刷两处

```swift
for window in NSApp.windows {
    window.appearance = resolved
    window.contentView?.appearance = resolved   // ← 关键：盖掉 SwiftUI 残留
    window.contentView?.needsDisplay = true
}
```

## 运行时同步

订阅 `DistributedNotificationCenter` 的 `AppleInterfaceThemeChangedNotification`，当用户当前是 `.system` 时重新 `applyTheme(.system)`。

## 完整实现

见 `references/appearance-manager.swift.txt`。

## 核心检查清单

- [ ] 主题逻辑集中在单一 `applyTheme` 函数里
- [ ] `.system` 分支**先**清 `NSApp.appearance = nil`，**再**读 `UserDefaults` 而不是 `effectiveAppearance`
- [ ] 循环刷所有 `window.appearance` **和** `window.contentView?.appearance`
- [ ] 订阅 `AppleInterfaceThemeChangedNotification`，`.system` 时重 apply
- [ ] 视图层配合 `.id("\(theme.rawValue)-\(language)")` 让 NSPopUpButton 等原生控件在主题/语言切换时 remount

## 常见错误

- 只改 `NSApp.appearance` 忘刷 contentView → 深色切系统回不来
- 用 `NSApp.effectiveAppearance` 采样 system 外观 → 立即读可能仍是旧值
- 仅靠 SwiftUI `.preferredColorScheme` → NSPopUpButton / NSMenu 等 AppKit 控件保留旧外观
