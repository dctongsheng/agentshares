# Agent Share API Reference

## Table of Contents

- [Authentication](#authentication)
- [Conversations](#conversations)
- [Upload](#upload)
- [Social](#social)
- [Credits](#credits)
- [Skills](#skills)
- [Error Codes](#error-codes)

## Authentication

Two auth modes:

### API Key (Bearer Token)
For upload endpoint. Header: `Authorization: Bearer <apiKey>`
API key is auto-generated on registration (UUID v4).

### Session (NextAuth Cookie)
For social, credits, unlock endpoints. Login flow:
1. `GET /api/auth/csrf` → `{"csrfToken": "..."}`
2. `POST /api/auth/callback/credentials` with form data: `csrfToken`, `email`, `password`
3. Session cookie set automatically

### POST /api/auth/register
Register a new account.

**Request:** `Content-Type: application/json`
```json
{ "email": "user@example.com", "password": "123456", "nickname": "Alice" }
```

**Response 201:**
```json
{ "user": { "id": "uuid", "email": "...", "nickname": "...", "apiKey": "uuid", "credits": 100, "avatar": null, "bio": null, "createdAt": "..." } }
```
**Errors:** 400 (validation), 409 (email exists), 429 (rate limit: 5/min/IP)

## Conversations

### GET /api/conversations
List public conversations.

**Query params:** `page` (default 1), `limit` (default 12), `sort` (latest|popular|most_viewed), `tag`, `search`

**Response:**
```json
{
  "conversations": [{ "id", "title", "description", "viewCount", "likeCount", "tags", "createdAt", "user": { "id", "nickname", "avatar" } }],
  "pagination": { "page", "limit", "total", "totalPages" }
}
```

### GET /api/conversations/{id}
Get conversation with messages. Public endpoint.

**Query params:** `cursor` (message sequence offset), `limit` (default 50, max 100)

**Response:**
```json
{
  "id", "title", "description", "rawContent", "sourceType", "price", "messageCount", "likeCount", "viewCount", "tags",
  "user": { "id", "nickname", "avatar" },
  "messages": [{ "sequence", "role", "content", "toolCalls", "timestamp" }],
  "skills": [{ "skill": { "id", "name", "description", "content" } }],
  "environment": { "os", "containerInfo", "gpu", "runtimeInfo" },
  "hasFullAccess": true/false,
  "previewLimit": null/number,
  "pagination": { "hasMore", "nextCursor", "totalMessages" }
}
```
Non-owners see only 20% of messages unless unlocked.

### POST /api/conversations/{id}/unlock
Unlock a paid conversation. Requires session.

**Response:**
```json
{ "success": true, "creditsSpent": 50, "newBalance": 50 }
```
5% platform fee (min 1 credit). Cannot unlock own or free conversations.

## Upload

### POST /api/upload/conversation
Upload a conversation file. Requires API key auth.

**Request:** `Content-Type: multipart/form-data`

| Field | Required | Description |
|-------|----------|-------------|
| `file` | Yes | Conversation file |
| `title` | Yes | Title string |
| `source_type` | Yes | One of: `claude-code`, `jsonl`, `openai`, `openclaw`, `trae`, `cursor`, `windsurf`, `aider`, `copilot`, `cline` |
| `description` | No | Description text |
| `price` | No | Credits required to unlock (default: 0) |
| `tags` | No | Comma-separated tags |
| `skills` | No | JSON array: `[{"name":"...", "description":"...", "content":"..."}]` |
| `environment` | No | JSON: `{"os":"...", "containerInfo":"...", "gpu":"...", "runtimeInfo":"..."}` |

**Source type → parser mapping:**
- `claude-code`, `jsonl` → JSONL parser (Claude Code session format)
- All others → OpenAI-compatible parser

#### JSON Conversation Format (for non-Claude Code agents)

Top-level array or `{"messages": [...]}`. Supported roles: `user`, `assistant`, `tool` (`system` is skipped). Supports `tool_calls` on assistant messages.

**Basic example:**
```json
[
  {"role": "user", "content": "帮我写一个快速排序"},
  {"role": "assistant", "content": "好的，这是 Python 实现：\n```python\ndef quicksort(arr): ...\n```"}
]
```

**With tool calls:**
```json
[
  {"role": "user", "content": "写一个文件"},
  {"role": "assistant", "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "write_file", "arguments": "{\"path\":\"test.py\",\"content\":\"print('hello')\"}"}}]},
  {"role": "tool", "tool_call_id": "call_1", "content": "File written successfully"},
  {"role": "assistant", "content": "文件已写入 test.py"}
]
```

**With wrapper:**
```json
{"messages": [
  {"role": "user", "content": "Hello"},
  {"role": "assistant", "content": "Hi!"}
]}
```

**Response 201:**
```json
{ "id": "uuid", "title": "...", "messageCount": 42, "skillCount": 2 }
```
**Errors:** 400 (validation), 401 (no API key), 429 (rate limit: 10/min/IP)

## Social

### POST /api/social/interact
Like/dislike/bookmark. Requires session. Toggle behavior.

**Request:**
```json
{ "targetType": "conversation|skill", "targetId": "uuid", "action": "like|dislike|bookmark" }
```

**Response:**
```json
{ "action": "like|null", "counts": { "likeCount": 10, "dislikeCount": 2, "bookmarkCount": 5 } }
```
Like and dislike are mutually exclusive for conversations.

### POST /api/social/comment
Create a comment. Requires session.

**Request:**
```json
{ "conversationId": "uuid", "content": "text", "parentId": "uuid|null" }
```

**Response 201:**
```json
{ "comment": { "id", "userId", "content", "parentId", "createdAt", "user": { "id", "nickname", "avatar" } } }
```

### GET /api/social/comment
Get comments. Public endpoint.

**Query params:** `conversationId` (required)

**Response:**
```json
{ "comments": [{ "id", "content", "parentId", "createdAt", "user": { "id", "nickname", "avatar" }, "replies": [...] }] }
```
One level of nested replies.

### POST /api/social/follow
Follow/unfollow toggle. Requires session.

**Request:** `{ "userId": "uuid" }`

**Response:** `{ "following": true/false, "followerCount": 42 }`

## Credits

### GET /api/credits/balance
Get balance and recent transactions. Requires session.

**Response:**
```json
{
  "balance": 100,
  "transactions": [{ "id", "fromUserId", "toUserId", "amount", "platformFee", "type": "unlock|reward|gift", "createdAt" }]
}
```

### POST /api/credits/transfer
Transfer credits. Requires session. 5% platform fee (min 1).

**Request:** `{ "toUserId": "uuid", "amount": 10 }`

**Response:** `{ "success": true, "platformFee": 1, "newBalance": 89 }`

## Skills

### GET /api/skills
List skills. Public endpoint.

**Query params:** `page` (default 1), `limit` (default 20), `search`

**Response:**
```json
{
  "skills": [{ "id", "name", "description", "content", "likeCount", "createdAt", "user": { "id", "nickname" } }],
  "pagination": { "page", "limit", "total", "totalPages" }
}
```

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Validation error (see `error` field) |
| 401 | Not authenticated |
| 404 | Resource not found |
| 409 | Conflict (e.g., email already registered) |
| 429 | Rate limited |
| 500 | Server error |
