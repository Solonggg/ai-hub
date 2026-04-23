---
name: swift-runtime-localization
description: SwiftUI + AppKit macOS 应用需要不重启即时切换应用内显示语言（而非只依赖系统语言），发现切换后 String(localized:) / NSMenu / NSPopUpButton / NSWindow 标题不更新或仍指向旧 lproj 时使用
---

# Swift macOS 应用的运行时国际化

## 背景

macOS 没有"不重启切换 app 内显示语言"的一等 API：

- `String(localized:)` 经由 `Bundle.main` 的 development-region 解析链在**调用时**取值
- `Bundle.main` 的当前 lproj 由启动时的系统语言决定，之后改不了
- `.environment(\.locale, ...)` 只影响 SwiftUI 层的某些格式化，不影响 `String(localized:)`

要实现应用内"中 / 英 / 跟随系统"三档可选切换，需要从运行时层面拦截 bundle 查询。

## 核心方案

### 1. Swizzle `Bundle.localizedString(forKey:value:table:)`

第一次访问 `LanguageManager` 时交换实现：

```swift
let cls: AnyClass = Bundle.self
let originalSel = #selector(Bundle.localizedString(forKey:value:table:))
let swizzledSel = #selector(Bundle._trace_localizedString(forKey:value:table:))
method_exchangeImplementations(
    class_getInstanceMethod(cls, originalSel)!,
    class_getInstanceMethod(cls, swizzledSel)!
)
```

交换后：

- 业务代码 `Bundle.main.localizedString(...)` → 进入自己的 wrapper
- wrapper 判断是否有 override bundle：有就转发到 override；没就走原实现
- 每个 `String(localized:)` 在**调用时**拿到所选 lproj 的文案

### 2. 切换时发自定义 Notification

```swift
extension Notification.Name {
    static let traceLanguageDidChange = Notification.Name("TraceLanguageDidChange")
}
```

`apply(_:)` 里换完 override bundle 就 post 一次。

### 3. 视图层强制 remount

已经 render 过的 SwiftUI 视图不会自动重取 `String(localized:)`。给受影响子树加 `.id("...-\(language)")` 组合键，通知到了 remount：

```swift
SettingsView()
    .id("settings-\(settings.language)")
```

### 4. AppKit 原生控件手动同步

NSWindow.title、NSMenu item title、NSStatusItem 的 label 等在 `traceLanguageDidChange` 回调里手动重赋值。

## 启动时序关键

`LanguageManager.shared.apply(settings.language)` 必须在 **`applicationDidFinishLaunching` 的最前面**调用，早于任何 `String(localized:)` 读取。否则早期字符串（状态栏菜单项、首次显示的窗口标题）会仍是系统语言，直到用户主动切换才刷。

## 完整实现

见 `references/language-manager.swift.txt`。

## 常见错误

- swizzle 触达时机太晚 → 早期 UI 字符串固化成系统语言
- 没加 `.id(language)` → SwiftUI 视图陈旧
- override bundle 没处理 `"system"` 分支 → 跟随系统时路由错误。明确：`"system"` → override 为 `nil`，走原始实现
- 只 swizzle 不发通知 → AppKit 控件（NSMenu、NSWindow.title）不自动更新

## 相关 skill

视图 remount / Environment 一次性解析的更多细节在 `swiftui-appkit-layout-traps`。
