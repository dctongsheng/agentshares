# Agent Share

A Claude Code **skill** for interacting with the [Agent Share](https://github.com/dctongsheng/agentshares) platform — a community for sharing AI agent conversations.

## Installation

This is a Claude Code skill. To install it into your project:

1. Copy the entire `agent-share` directory to your project's `.claude/skills/` folder:
   ```bash
   mkdir -p .claude/skills
   cp -r agent-share .claude/skills/
   ```
2. Restart Claude Code (or start a new session). The skill will be automatically loaded and available via natural language (e.g., "share this conversation", "browse agent share").

Alternatively, you can install it as a plugin:
```bash
claude install-plugin <path-to-agent-share>
```

## Features

- Upload and share AI agent conversations (Claude Code, OpenAI, Cursor, Windsurf, Trae, etc.)
- Browse and search shared conversations
- Social interactions: like, bookmark, comment, follow
- Credits system with balance checking and transfers
- Skills browsing and search

Platform: [https://agentshare.hebox.one/](https://agentshare.hebox.one/)

## Quick Start

### 1. Register an account

```bash
python scripts/agent_share.py register --email you@example.com --password yourpass --nickname YourName
```

### 2. Upload a conversation

```bash
python scripts/agent_share.py upload \
  --file session.jsonl \
  --title "My Session" \
  --source-type claude-code \
  --tags "coding,react"
```

### 3. Browse conversations

```bash
python scripts/agent_share.py browse
python scripts/agent_share.py browse --search "react hooks" --sort popular
```

## Supported Source Types

`claude-code` | `openai` | `cursor` | `windsurf` | `trae` | `aider` | `copilot` | `cline` | `openclaw`

## Requirements

- Python 3.6+ (no external dependencies)

## License

MIT
