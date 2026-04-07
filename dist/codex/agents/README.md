# agents

## 用途

`agents` 用于存放全局代理定义。这里的文件不是单个 skill 私有的代理，而是面向某个工具分发时需要整体带上的公共代理。

## 当前状态

当前目录为空，说明这个仓库现在主要依赖 skill 自带的 `agents/`，暂时没有全局代理需要统一下发。

## 用法

1. 当多个 skill 或多个工具都需要同一份代理定义时，可以把文件放到这里。
2. 运行同步命令后，这些文件会按适配器规则复制到 `dist/<tool>/<agent_dir_name>/`：

```bash
/Users/wangjie/ai-hub/bin/publish-skills/publish-skills
```

3. 安装到目标工具目录后，会以软链接或复制的方式暴露给目标工具：

```bash
/Users/wangjie/ai-hub/bin/install-target/install-target --tool codex --target ~/.codex
```

## 注意事项

- 如果只是某个 skill 独有的代理，优先放在对应 skill 目录下的 `agents/` 中，不要上升到全局目录。
- 目录为空是正常状态，不需要为了“完整”强行放示例文件。
