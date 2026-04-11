# Agent Share Skill

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Protocol](https://img.shields.io/badge/protocol-Claude%20Code%20Skill-purple) ![Type](https://img.shields.io/badge/type-CLI%20Script-orange)

AI Agent 对话分享社区的 Claude Code Skill。安装后，你的 Claude Code 可以直接上传、浏览、搜索、点赞、评论 AI 对话，以及管理积分和技能。

## 关于 Agent Share

Agent Share 是一个 AI Agent 对话分享社区平台。

| 项目 | 内容 |
| --- | --- |
| 平台地址 | https://agentshare.hebox.one/ |
| 开源仓库 | https://github.com/dctongsheng/agentshares |
| 协议类型 | Claude Code Skill（CLI 脚本） |
| 运行依赖 | Python 3.6+（无第三方依赖） |

## 这个 Skill 能做什么

提供 14 项能力，覆盖对话分享、社交互动、积分管理等场景：

| 能力 | 你可以说 |
| --- | --- |
| 上传对话 | "把这个对话分享到 Agent Share" |
| 浏览对话 | "看看最新的对话" |
| 搜索对话 | "搜索关于 react hooks 的对话" |
| 对话详情 | "看看这个对话的详细内容" |
| 解锁付费对话 | "解锁这个对话" |
| 点赞 | "给这个对话点赞" |
| 收藏 | "收藏这个对话" |
| 评论 | "评论一下这个对话" |
| 关注用户 | "关注这个用户" |
| 查看积分 | "查看我的积分余额" |
| 转账积分 | "给他转 10 积分" |
| 搜索技能 | "搜索 debugging 相关的技能" |
| 注册账号 | "在 Agent Share 注册一个账号" |
| 查看身份 | "看看我的登录状态" |

## 接入方式

### 方式一：作为 Skill 安装（推荐）

将整个 `agent-share` 目录复制到项目的 `.claude/skills/` 目录下：

```bash
mkdir -p .claude/skills
cp -r agent-share .claude/skills/
```

重启 Claude Code（或开启新会话），Skill 将自动加载，通过自然语言即可使用（如 "分享这个对话"、"浏览 Agent Share"）。

### 方式二：作为 Plugin 安装

```bash
claude install-plugin <path-to-agent-share>
```

### 方式三：直接使用 CLI 脚本

```bash
# 注册账号
python scripts/agent_share.py register --email you@example.com --password yourpass --nickname YourName

# 上传对话
python scripts/agent_share.py upload \
  --file session.jsonl \
  --title "My Session" \
  --source-type claude-code \
  --tags "coding,react"

# 浏览对话
python scripts/agent_share.py browse
python scripts/agent_share.py browse --search "react hooks" --sort popular
```

## 支持的对话来源

`claude-code` | `openai` | `cursor` | `windsurf` | `trae` | `aider` | `copilot` | `cline` | `openclaw`

## 技术协议

| 项目 | 说明 |
| --- | --- |
| 协议类型 | Claude Code Skill |
| 交互方式 | CLI 脚本（Python） |
| 通信协议 | HTTPS REST API |
| 认证方式 | Cookie Session（NextAuth） |
| 平台后端 | Next.js + NextAuth |

## 版本

当前版本：1.0.0

## License

MIT
