#!/usr/bin/env python3
"""Agent Share CLI - Interact with the Agent Share platform API."""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import uuid
from pathlib import Path

CONFIG_PATH = Path.home() / ".agent-share-config.json"
COOKIE_PATH = Path.home() / ".agent-share-cookies.txt"
PROJECT_DIR = Path(__file__).resolve().parents[3]  # agent-share project root

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}


def load_env():
    """Read NEXTAUTH_URL from project .env file."""
    env_path = PROJECT_DIR / ".env"
    env_vars = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                env_vars[key.strip()] = val.strip().strip('"').strip("'")
    return env_vars


def get_base_url(args):
    """Get base URL from CLI arg > env var > .env > config."""
    if args.url:
        return args.url.rstrip("/")
    env_url = os.environ.get("AGENT_SHARE_URL")
    if env_url:
        return env_url.rstrip("/")
    env_vars = load_env()
    if "NEXTAUTH_URL" in env_vars:
        return env_vars["NEXTAUTH_URL"].rstrip("/")
    config = load_config()
    if config.get("url"):
        return config["url"].rstrip("/")
    print(json.dumps({"error": "No base URL configured. Use --url or set AGENT_SHARE_URL env var."}), file=sys.stderr)
    sys.exit(1)


def get_api_key(args):
    """Get API key from CLI arg > env var > config."""
    if hasattr(args, "api_key") and args.api_key:
        return args.api_key
    key = os.environ.get("AGENT_SHARE_API_KEY")
    if key:
        return key
    config = load_config()
    return config.get("apiKey")


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {}


def save_config(data):
    existing = load_config()
    existing.update(data)
    CONFIG_PATH.write_text(json.dumps(existing, indent=2))


def get_cookie_jar():
    cj = http.cookiejar.MozillaCookieJar(str(COOKIE_PATH))
    if COOKIE_PATH.exists():
        try:
            cj.load(ignore_discard=True, ignore_expires=True)
        except Exception:
            pass
    return cj


def save_cookie_jar(cj):
    cj.save(str(COOKIE_PATH), ignore_discard=True, ignore_expires=True)


def make_request(url, data=None, headers=None, method=None, cj=None, is_json=True):
    """Make HTTP request. Returns parsed JSON or raw response."""
    if headers is None:
        headers = {}
    merged = {**DEFAULT_HEADERS, **headers}
    if data is not None and is_json:
        data = json.dumps(data).encode("utf-8")
        merged["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=merged, method=method)
    opener = urllib.request.build_opener()
    if cj:
        opener.add_handler(urllib.request.HTTPCookieProcessor(cj))
    try:
        resp = opener.open(req)
        body = resp.read().decode("utf-8")
        if is_json:
            return json.loads(body), resp.status
        return body, resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            err = json.loads(body)
        except Exception:
            err = {"error": body}
        return err, e.code


def login_session(base_url, email, password):
    """Perform NextAuth credentials login, returns cookie jar."""
    cj = get_cookie_jar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # Get CSRF token
    csrf_req = urllib.request.Request(f"{base_url}/api/auth/csrf", headers=DEFAULT_HEADERS)
    csrf_resp = opener.open(csrf_req)
    csrf_data = json.loads(csrf_resp.read().decode("utf-8"))
    csrf_token = csrf_data.get("csrfToken", "")

    # Login
    login_data = urllib.parse.urlencode({
        "csrfToken": csrf_token,
        "email": email,
        "password": password,
        "callbackUrl": f"{base_url}/",
        "json": "true",
    }).encode("utf-8")
    login_req = urllib.request.Request(
        f"{base_url}/api/auth/callback/credentials",
        data=login_data,
        headers={**DEFAULT_HEADERS, "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        login_resp = opener.open(login_req)
        save_cookie_jar(cj)
        return cj
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(json.dumps({"error": f"Login failed: {body}"}), file=sys.stderr)
        sys.exit(1)


def get_session_auth(args):
    """Get authenticated cookie jar, re-login if needed."""
    base_url = get_base_url(args)
    config = load_config()
    email = getattr(args, "email", None) or config.get("email") or os.environ.get("AGENT_SHARE_EMAIL")
    password = getattr(args, "password", None) or config.get("password") or os.environ.get("AGENT_SHARE_PASSWORD")
    if not email or not password:
        print(json.dumps({"error": "No credentials. Run 'agent_share.py login' first."}), file=sys.stderr)
        sys.exit(1)
    return login_session(base_url, email, password), base_url


def output(data, status=200):
    """Print JSON to stdout."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ── Subcommands ──

def cmd_register(args):
    base_url = get_base_url(args)
    payload = {
        "email": args.email,
        "password": args.password,
        "nickname": args.nickname,
    }
    result, status = make_request(f"{base_url}/api/auth/register", data=payload)
    if status == 201:
        user = result.get("user", {})
        save_config({
            "url": base_url,
            "apiKey": user.get("apiKey", ""),
            "email": args.email,
            "password": args.password,
        })
        # Also login to get session cookie
        login_session(base_url, args.email, args.password)
    output(result, status)


def cmd_login(args):
    base_url = get_base_url(args)
    email = args.email
    password = args.password
    login_session(base_url, email, password)
    save_config({"url": base_url, "email": email, "password": password})
    output({"success": True, "message": "Logged in"})


def cmd_whoami(args):
    cj, base_url = get_session_auth(args)
    result, status = make_request(f"{base_url}/api/auth/session", cj=cj)
    output(result, status)


def cmd_upload(args):
    base_url = get_base_url(args)
    api_key = get_api_key(args)
    if not api_key:
        print(json.dumps({"error": "No API key. Register first or use --api-key."}), file=sys.stderr)
        sys.exit(1)

    file_path = Path(args.file)
    if not file_path.exists():
        print(json.dumps({"error": f"File not found: {args.file}"}), file=sys.stderr)
        sys.exit(1)

    # Build multipart form data
    boundary = uuid.uuid4().hex
    body = b""

    def add_field(name, value):
        nonlocal body
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        body += f"{value}\r\n".encode()

    def add_file(name, filename, content):
        nonlocal body
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        body += b"Content-Type: application/octet-stream\r\n\r\n"
        body += content
        body += b"\r\n"

    add_field("title", args.title)
    add_field("source_type", args.source_type)

    if args.description:
        add_field("description", args.description)
    if args.price is not None:
        add_field("price", str(args.price))
    if args.tags:
        add_field("tags", args.tags)
    if args.skills:
        add_field("skills", args.skills)
    if args.environment:
        add_field("environment", args.environment)

    file_content = file_path.read_bytes()
    add_file("file", file_path.name, file_content)

    body += f"--{boundary}--\r\n".encode()

    headers = {
        **DEFAULT_HEADERS,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    req = urllib.request.Request(
        f"{base_url}/api/upload/conversation",
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read().decode("utf-8"))
        output(result, resp.status)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            output(json.loads(err_body), e.code)
        except Exception:
            print(json.dumps({"error": err_body}), file=sys.stderr)
        sys.exit(1)


def cmd_browse(args):
    base_url = get_base_url(args)
    params = {}
    if args.page:
        params["page"] = args.page
    if args.limit:
        params["limit"] = args.limit
    if args.sort:
        params["sort"] = args.sort
    if args.tag:
        params["tag"] = args.tag
    if args.search:
        params["search"] = args.search
    qs = urllib.parse.urlencode(params)
    url = f"{base_url}/api/conversations"
    if qs:
        url += f"?{qs}"
    result, status = make_request(url)
    output(result, status)


def cmd_get(args):
    base_url = get_base_url(args)
    params = {}
    if args.cursor:
        params["cursor"] = args.cursor
    if args.limit:
        params["limit"] = args.limit
    qs = urllib.parse.urlencode(params)
    url = f"{base_url}/api/conversations/{args.id}"
    if qs:
        url += f"?{qs}"
    result, status = make_request(url)
    output(result, status)


def cmd_unlock(args):
    cj, base_url = get_session_auth(args)
    result, status = make_request(
        f"{base_url}/api/conversations/{args.id}/unlock",
        data={},
        cj=cj,
        method="POST",
    )
    output(result, status)


def cmd_interact(args):
    cj, base_url = get_session_auth(args)
    payload = {
        "targetType": args.target_type,
        "targetId": args.target_id,
        "action": args.action,
    }
    result, status = make_request(
        f"{base_url}/api/social/interact",
        data=payload,
        cj=cj,
    )
    output(result, status)


def cmd_comment(args):
    cj, base_url = get_session_auth(args)
    payload = {
        "conversationId": args.conversation_id,
        "content": args.content,
    }
    if args.parent_id:
        payload["parentId"] = args.parent_id
    result, status = make_request(
        f"{base_url}/api/social/comment",
        data=payload,
        cj=cj,
    )
    output(result, status)


def cmd_comments(args):
    base_url = get_base_url(args)
    result, status = make_request(
        f"{base_url}/api/social/comment?conversationId={args.conversation_id}"
    )
    output(result, status)


def cmd_follow(args):
    cj, base_url = get_session_auth(args)
    result, status = make_request(
        f"{base_url}/api/social/follow",
        data={"userId": args.user_id},
        cj=cj,
    )
    output(result, status)


def cmd_credits_balance(args):
    cj, base_url = get_session_auth(args)
    result, status = make_request(f"{base_url}/api/credits/balance", cj=cj)
    output(result, status)


def cmd_credits_transfer(args):
    cj, base_url = get_session_auth(args)
    payload = {"toUserId": args.to_user_id, "amount": args.amount}
    result, status = make_request(
        f"{base_url}/api/credits/transfer",
        data=payload,
        cj=cj,
    )
    output(result, status)


def cmd_skills(args):
    base_url = get_base_url(args)
    params = {}
    if args.page:
        params["page"] = args.page
    if args.limit:
        params["limit"] = args.limit
    if args.search:
        params["search"] = args.search
    qs = urllib.parse.urlencode(params)
    url = f"{base_url}/api/skills"
    if qs:
        url += f"?{qs}"
    result, status = make_request(url)
    output(result, status)


# ── CLI Parser ──

def build_parser():
    parser = argparse.ArgumentParser(
        prog="agent_share",
        description="Agent Share CLI - interact with the Agent Share platform",
    )
    parser.add_argument("--url", help="Base URL of the Agent Share instance")
    parser.add_argument("--api-key", help="API key for upload auth")

    sub = parser.add_subparsers(dest="command")

    # register
    p = sub.add_parser("register", help="Register a new account")
    p.add_argument("--email", required=True)
    p.add_argument("--password", required=True)
    p.add_argument("--nickname", required=True)
    p.set_defaults(func=cmd_register)

    # login
    p = sub.add_parser("login", help="Login and save session")
    p.add_argument("--email", required=True)
    p.add_argument("--password", required=True)
    p.set_defaults(func=cmd_login)

    # whoami
    p = sub.add_parser("whoami", help="Check current auth status")
    p.set_defaults(func=cmd_whoami)

    # upload
    p = sub.add_parser("upload", help="Upload a conversation file")
    p.add_argument("--file", required=True, help="Path to conversation file")
    p.add_argument("--title", required=True, help="Conversation title")
    p.add_argument("--source-type", required=True,
                   choices=["claude-code", "jsonl", "openai", "openclaw", "trae",
                            "cursor", "windsurf", "aider", "copilot", "cline"],
                   help="Source format")
    p.add_argument("--description", help="Description")
    p.add_argument("--price", type=int, help="Price in credits (default: 0)")
    p.add_argument("--tags", help="Comma-separated tags")
    p.add_argument("--skills", help="JSON array of skills: [{name, description, content}]")
    p.add_argument("--environment", help="JSON object: {os, containerInfo, gpu, runtimeInfo}")
    p.set_defaults(func=cmd_upload)

    # browse
    p = sub.add_parser("browse", help="Browse conversations")
    p.add_argument("--page", type=int)
    p.add_argument("--limit", type=int)
    p.add_argument("--sort", choices=["latest", "popular", "most_viewed"])
    p.add_argument("--tag", help="Filter by tag")
    p.add_argument("--search", help="Search title/description")
    p.set_defaults(func=cmd_browse)

    # get
    p = sub.add_parser("get", help="Get conversation details")
    p.add_argument("id", help="Conversation ID")
    p.add_argument("--cursor", type=int, help="Message cursor for pagination")
    p.add_argument("--limit", type=int, help="Messages per page (default: 50, max: 100)")
    p.set_defaults(func=cmd_get)

    # unlock
    p = sub.add_parser("unlock", help="Unlock a paid conversation")
    p.add_argument("id", help="Conversation ID")
    p.set_defaults(func=cmd_unlock)

    # interact
    p = sub.add_parser("interact", help="Like/dislike/bookmark")
    p.add_argument("--target-type", required=True, choices=["conversation", "skill"])
    p.add_argument("--target-id", required=True)
    p.add_argument("--action", required=True, choices=["like", "dislike", "bookmark"])
    p.set_defaults(func=cmd_interact)

    # comment
    p = sub.add_parser("comment", help="Create a comment")
    p.add_argument("--conversation-id", required=True)
    p.add_argument("--content", required=True)
    p.add_argument("--parent-id", help="Parent comment ID for replies")
    p.set_defaults(func=cmd_comment)

    # comments
    p = sub.add_parser("comments", help="Get comments for a conversation")
    p.add_argument("--conversation-id", required=True)
    p.set_defaults(func=cmd_comments)

    # follow
    p = sub.add_parser("follow", help="Follow/unfollow a user")
    p.add_argument("user_id", help="User ID to follow/unfollow")
    p.set_defaults(func=cmd_follow)

    # credits
    p_credits = sub.add_parser("credits", help="Credits operations")
    credits_sub = p_credits.add_subparsers(dest="credits_command")

    cb = credits_sub.add_parser("balance", help="Check credit balance")
    cb.set_defaults(func=cmd_credits_balance)

    ct = credits_sub.add_parser("transfer", help="Transfer credits")
    ct.add_argument("--to-user-id", required=True)
    ct.add_argument("--amount", type=int, required=True)
    ct.set_defaults(func=cmd_credits_transfer)

    # skills
    p = sub.add_parser("skills", help="Browse skills")
    p.add_argument("--page", type=int)
    p.add_argument("--limit", type=int)
    p.add_argument("--search", help="Search skills")
    p.set_defaults(func=cmd_skills)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
