---
name: xcode-build-signing-dynamic
description: 本机 Xcode + xcodegen 工程出现证书轮换后构建失败、SPM 包与 app target 签名冲突（conflicting provisioning settings）、pbxproj 里硬编码 SHA-1 在不同机器失效、或 Release 冷编译输出被 tail 截断看起来"卡住"等工程化症状时使用
---

# Xcode 项目本机签名与构建脚本稳定配方

## 何时使用

个人开发的 macOS / iOS Xcode 项目，用 xcodegen 维护 `project.yml`，在**本机**（不走 CI）构建，遇到其中之一：

- Apple Development 证书轮换后 xcodebuild 报找不到签名身份
- SPM 包对 `CODE_SIGN_IDENTITY` 报 `conflicting provisioning settings`
- pbxproj 里硬编码了 SHA-1，换机器或重建证书后整个工程不能用
- `xcodebuild | tail -5` 式调用让冷编译看起来卡死 3-5 分钟

## 四个做法

### 1. 证书 SHA-1 从 keychain 现查

`build.sh` 顶部：

```bash
SIGN_LINE=$(security find-identity -p codesigning -v 2>/dev/null \
    | awk -F'"' '/Apple Development/ {print $0; exit}')
MYAPP_CODE_SIGN_IDENTITY=$(echo "$SIGN_LINE" | awk '{print $2}')
export MYAPP_CODE_SIGN_IDENTITY
```

### 2. `project.yml` 用 `${VAR}` 展开

xcodegen 会把环境变量展开到 pbxproj：

```yaml
settings:
  base:
    CODE_SIGN_STYLE: Manual
    DEVELOPMENT_TEAM: TEAMID12AB
# ⚠️ 全局 settings.base 里不要写 CODE_SIGN_IDENTITY，会把 SPM 包也拉进来 Manual

targets:
  MyApp:
    settings:
      base:
        CODE_SIGN_IDENTITY: ${MYAPP_CODE_SIGN_IDENTITY}   # ← 只写到 app target
        PROVISIONING_PROFILE_SPECIFIER: ""
```

**关键**：`CODE_SIGN_IDENTITY` 只写到 **app target** 下。SPM 依赖自动保持 Automatic 签名，不与 manual 冲突。

### 3. 按需 regenerate

两条触发条件：

- `project.yml` 比 pbxproj 新
- 当前 keychain 证书 SHA 不在 pbxproj 中（证书已轮换）

```bash
NEED_REGEN=0
if [ ! -f "$PROJECT/project.pbxproj" ] \
   || [ "project.yml" -nt "$PROJECT/project.pbxproj" ]; then
    NEED_REGEN=1
elif ! grep -q "$MYAPP_CODE_SIGN_IDENTITY" "$PROJECT/project.pbxproj"; then
    NEED_REGEN=1
fi

if [ "$NEED_REGEN" = "1" ]; then
    xcodegen generate
fi
```

### 4. 流式输出不截断

冷编译可能 3-5 分钟，`| tail -5` 期间用户只能看到一片空白。用 `xcbeautify` 可用则用，不可用就 `cat` 原样流出：

```bash
if command -v xcbeautify >/dev/null 2>&1; then
    FORMATTER=(xcbeautify)
else
    FORMATTER=(cat)
fi
xcodebuild ... | "${FORMATTER[@]}"
```

## 完整模板

- `references/build.sh.txt` — 完整可直接改名使用的 build.sh
- `references/project-signing.yml.excerpt.txt` — project.yml 签名片段

## 常见错误

| 错误 | 后果 |
|---|---|
| `CODE_SIGN_IDENTITY` 写到全局 `settings.base` | SPM 包也被强制 Manual，报 conflicting provisioning |
| 只检查 `project.yml` mtime、不检查 SHA | 证书刚轮换、project.yml 未改，构建仍用旧 SHA 失败 |
| 跳过 `set -euo pipefail` | 中间某步失败后续还在跑，错误堆叠难定位 |
| 用 `tail -5` 看输出 | 冷编译期间用户以为卡死，反复中断重来 |

## 适用范围

本脚本专为**个人项目本机构建**设计。CI 环境下应改用 keychain 里预置的专用签名身份 + 环境变量注入，不应该从 `security find-identity` 的"第一条 Apple Development"猜，否则多人协作时选到错误证书。
