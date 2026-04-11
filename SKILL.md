---
name: agent-share
description: Interact with the Agent Share platform — a community for sharing AI agent conversations. Use when the user wants to (1) upload or share a conversation/session to Agent Share, (2) browse or search shared conversations and skills, (3) like, bookmark, comment on, or follow users on Agent Share, (4) check credit balance or transfer credits, (5) register an account on Agent Share, or (6) get details of a specific conversation. Triggers on phrases like "share this conversation", "upload to agent-share", "find conversations about X", "browse agent share", "check my credits", "search skills".
---

# Agent Share

Interact with the Agent Share platform via the CLI script at `scripts/agent_share.py`.

## Prerequisites

One-time setup — register an account:

```bash
python scripts/agent_share.py register --email you@example.com --password yourpass --nickname YourName
```

This saves credentials to `~/.agent-share-config.json` and a session cookie to `~/.agent-share-cookies.txt`. The base URL defaults to `https://agentshare.hebox.one/` and can be auto-read from the project's `.env` file (`NEXTAUTH_URL`).

Override base URL via `--url`, `AGENT_SHARE_URL` env var, or config file.

## First-Time Setup

**Every time this skill is triggered, FIRST check if the user is registered:**

Check if `~/.agent-share-config.json` exists and contains valid credentials:
```bash
cat ~/.agent-share-config.json
```

If the file does NOT exist or is missing `email`/`apiKey` fields, this is a first-time user. Follow this onboarding flow:

1. **Welcome**: "Welcome to Agent Share! Let me help you set up."
2. **Ask** via AskUserQuestion: "Register a new account" or "Login with existing account"
3. **Register** — ask for email, password, nickname, then run:
   ```bash
   python scripts/agent_share.py register --email <email> --password <password> --nickname <nickname>
   ```
4. **Login** — ask for email, password, then run:
   ```bash
   python scripts/agent_share.py login --email <email> --password <password>
   ```
5. **After success**, introduce the platform:

> "Agent Share is ready! Here's what you can do:
> - **Upload** conversations to share with the community
> - **Browse** and search conversations from others
> - **Like, bookmark, comment** on interesting conversations
> - **Follow** other users
> - **Credits** — earn and spend credits for premium content
> - **Skills** — discover useful skills
>
> Try saying: 'browse latest conversations' or 'upload this session'"

## Decision Tree

```
First: check ~/.agent-share-config.json → if missing, go to First-Time Setup

```
What does the user want?
├─ Upload/share a conversation  → cmd_upload
├─ Browse conversations          → cmd_browse
├─ Get conversation details      → cmd_get
├─ Unlock paid conversation      → cmd_unlock
├─ Like/dislike/bookmark         → cmd_interact
├─ Create comment                → cmd_comment
├─ Read comments                 → cmd_comments
├─ Follow/unfollow user          → cmd_follow
├─ Check credit balance          → cmd_credits_balance
├─ Transfer credits              → cmd_credits_transfer
├─ Search skills                 → cmd_skills
├─ Register account              → cmd_register
├─ Login                         → cmd_login
└─ Check auth status             → cmd_whoami
```

## Commands

All commands output JSON to stdout. Run from the skill directory:

```bash
SCRIPT="scripts/agent_share.py"
```

### Browse & Search

```bash
# List latest conversations
python $SCRIPT browse

# Search conversations
python $SCRIPT browse --search "react hooks" --sort popular --limit 5

# Filter by tag
python $SCRIPT browse --tag "coding"

# Get conversation details
python $SCRIPT get <conversation-id>

# Paginate messages
python $SCRIPT get <id> --cursor 50 --limit 50
```

### Upload

> **MANDATORY RULE: 上传对话前必须先执行敏感信息过滤，这是强规则，不可跳过。**
>
> **NEVER upload raw session files. ALWAYS redact sensitive information first. No exceptions.**

**Before uploading, ALWAYS confirm with the user using AskUserQuestion. Do NOT upload directly.**

Follow this workflow:

1. **Find session file** — Locate the current conversation file
   - Claude Code: `~/.claude/projects/<project-hash>/` — pick the most recently modified `.jsonl` file
   - Other agents: the conversation JSON file
2. **REDACT SENSITIVE INFO (MANDATORY — MUST DO THIS BEFORE ANYTHING ELSE)** — Create a redacted copy of the session file. This step is NON-NEGOTIABLE and MUST happen before generating titles, detecting skills, or any other upload preparation:
   - Do NOT modify the original file
   - Read the session file and scan for sensitive patterns:
     - Database connection strings (`postgresql://...`, `mongodb://...`, `mysql://...`)
     - API keys and tokens (`Bearer ...`, `sk-...`, `npg_...`, `ghp_...`, `gho_...`)
     - Auth secrets (`AUTH_SECRET=...`, `SECRET_KEY=...`)
     - File paths with usernames (`/Users/username/`, `/home/username/`)
     - Passwords (`password=...`, `"password": "..."`)
     - Email addresses, phone numbers, IP addresses
     - Any environment variables containing secrets
   - Replace all matches with `***REDACTED***` in a temp copy
   - Upload the temp file, not the original
3. **Generate a suggested title** — Based on conversation content, create a concise descriptive title
4. **Auto-detect source type** — Determine from current agent:
   - Claude Code → `claude-code`
   - Other agents → corresponding type (`openai`, `cursor`, `windsurf`, `trae`, `aider`, `copilot`, `cline`, `openclaw`)
5. **Detect skills used in this conversation** —
   - Read the session JSONL file, search for skill names in `system-reminder` messages or `<command-name>/skill-name</command-name>` patterns
   - For each detected skill, read its SKILL.md to get name, description, and content
   - Build the `--skills` JSON array: `[{"name":"skill-name","description":"...","content":"..."}]`
   - If no skills detected, leave skills empty
6. **Ask user to confirm** — Use AskUserQuestion with these fields pre-filled:
   - Title (editable)
   - Source type (selectable)
   - Skills detected (show list, allow removal)
   - Tags (optional, editable)
   - Description (optional, editable)
   - Show a summary of what was redacted (e.g., "已过滤: 2个API密钥, 1个数据库连接串, 3个文件路径")
7. **Upload** — Only after redaction and user confirmation, run the upload command

**IMPORTANT: Determine the current agent before uploading.**

1. **Claude Code agent** → upload JSONL session file with `--source-type claude-code`
   - Session JSONL files are at `~/.claude/projects/<project-hash>/`
   - Pick the most recently modified `.jsonl` file
2. **All other agents** (OpenAI, Cursor, Windsurf, Trae, Aider, Copilot, Cline, OpenClaw, etc.) → upload the conversation as a JSON file with `--source-type <agent-name>`
   - JSON format: `[{"role":"user","content":"..."}, {"role":"assistant","content":"..."}, ...]`
   - Supports `tool_calls` and `tool` roles

```bash
# Claude Code: upload JSONL session
python $SCRIPT upload \
  --file path/to/session.jsonl \
  --title "My Session Title" \
  --source-type claude-code \
  --tags "coding,react"

# Other agents: upload conversation JSON
python $SCRIPT upload \
  --file path/to/conversation.json \
  --title "My Conversation" \
  --source-type openai \
  --tags "coding"

# Upload with price (credits to unlock)
python $SCRIPT upload \
  --file session.jsonl \
  --title "Premium Session" \
  --source-type claude-code \
  --price 10

# Upload with skills metadata
python $SCRIPT upload \
  --file session.jsonl \
  --title "Session with Skills" \
  --source-type claude-code \
  --skills '[{"name":"my-skill","description":"Does X","content":"..."}]'

# Source types for other agents: openai, openclaw, trae, cursor, windsurf, aider, copilot, cline
```

#### JSON Conversation Format (non-Claude Code agents)

Top-level array or `{"messages": [...]}`. Supported roles: `user`, `assistant`, `tool` (system is skipped). Supports `tool_calls` on assistant messages.

```json
[
  {"role": "user", "content": "帮我写一个快速排序"},
  {"role": "assistant", "content": "好的，这是快速排序的 Python 实现：\n```python\ndef quicksort(arr): ...\n```"},
  {"role": "user", "content": "加上注释"},
  {"role": "assistant", "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "write_file", "arguments": "{\"path\":\"sort.py\",\"content\":\"def quicksort(arr):\\n    ...\"}"}}]},
  {"role": "tool", "tool_call_id": "call_1", "content": "File written successfully"},
  {"role": "assistant", "content": "已加上注释并保存到 sort.py"}
]
```

### Social

```bash
# Like a conversation
python $SCRIPT interact --target-type conversation --target-id <id> --action like

# Bookmark
python $SCRIPT interact --target-type conversation --target-id <id> --action bookmark

# Comment
python $SCRIPT comment --conversation-id <id> --content "Great session!"

# Reply to a comment
python $SCRIPT comment --conversation-id <id> --content "Thanks!" --parent-id <comment-id>

# Read comments
python $SCRIPT comments --conversation-id <id>

# Follow a user
python $SCRIPT follow <user-id>

# Unlock paid conversation
python $SCRIPT unlock <conversation-id>
```

### Credits

```bash
# Check balance
python $SCRIPT credits balance

# Transfer credits (5% platform fee)
python $SCRIPT credits transfer --to-user-id <id> --amount 10
```

### Skills

```bash
# List skills
python $SCRIPT skills

# Search skills
python $SCRIPT skills --search "debugging"
```

## Upload: Finding Session Files

**Claude Code:** Session JSONL files at `~/.claude/projects/<project-hash>/`. Pick the most recently modified `.jsonl` file.

**Other agents:** Export or construct a JSON file with the conversation messages array `[{"role":"user","content":"..."}, ...]`.

## Full API Reference

For detailed request/response formats, see [references/api-reference.md](references/api-reference.md).
