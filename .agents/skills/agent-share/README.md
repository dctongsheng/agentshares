# Agent Share

A Claude Code skill for interacting with the [Agent Share](https://agentshare.app/) platform — a community for sharing AI agent conversations.

## Features

- Upload and share AI agent conversations (Claude Code, OpenAI, Cursor, Windsurf, Trae, etc.)
- Browse and search shared conversations
- Social interactions: like, bookmark, comment, follow
- Credits system with balance checking and transfers
- Skills browsing and search

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
