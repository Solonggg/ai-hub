---
name: jenkins-flow
description: 用户说"构建 dev"或"构建 master"时，通过 Jenkins REST API 触发对应项目的参数化构建。
---

# Jenkins Flow

## 概览

根据当前工作目录自动匹配 Jenkins job，通过 REST API 触发参数化构建。

## Job 映射

| 工作目录名 | Jenkins Job URL |
|---|---|
| `iho-nursing` | `http://192.168.1.120:9990/jenkins/job/iho-nursing/` |
| `iho-mrms` | `http://192.168.1.120:9990/jenkins/job/iho-mrms/` |

项目名取当前工作目录最后一级目录名。若不在上表中，提示用户当前项目无对应 Jenkins job。

## 认证

- 用户名：`likai`
- Token：从环境变量 `JENKINS_TOKEN` 读取

## 场景一：构建 dev

**触发词**：`构建 dev`

**执行命令**：

```bash
curl -s -o /dev/null -w "%{http_code}" -X POST \
  "http://192.168.1.120:9990/jenkins/job/{项目名}/buildWithParameters" \
  --user "likai:${JENKINS_TOKEN}" \
  --data-urlencode "branch=develop" \
  --data-urlencode "custom_branch=" \
  --data-urlencode "dockerImage=false" \
  --data-urlencode "imageVersion=" \
  --data-urlencode "restart211=true"
```

**结果判断**：
- HTTP 201：构建已触发，告知用户
- 其他状态码：告知用户触发失败及状态码

## 场景二：构建 master

**触发词**：`构建 master {版本号}`，例如 `构建 master 4.4.3`

**前置校验**：版本号必填，未提供时提示用户补充版本号，不触发构建。

**执行命令**：

```bash
curl -s -o /dev/null -w "%{http_code}" -X POST \
  "http://192.168.1.120:9990/jenkins/job/{项目名}/buildWithParameters" \
  --user "likai:${JENKINS_TOKEN}" \
  --data-urlencode "branch=master" \
  --data-urlencode "custom_branch=" \
  --data-urlencode "dockerImage=true" \
  --data-urlencode "imageVersion={版本号}" \
  --data-urlencode "restart211=true"
```

**结果判断**：
- HTTP 201：构建已触发，告知用户分支和镜像版本号
- 其他状态码：告知用户触发失败及状态码

## 通用规则

- 触发后不轮询构建结果，直接返回
- 若 `JENKINS_TOKEN` 环境变量未设置，提示用户配置
