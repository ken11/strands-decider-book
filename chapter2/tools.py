import json
import shutil
from pathlib import Path

from strands import tool

ROOT = Path(__file__).parent.parent
SEED_DIR = ROOT / "data" / "seed"
WORK_DIR = ROOT / "workspace"


def reset_workspace() -> None:
    """作業ディレクトリを初期状態（data/seed）に戻す。"""
    shutil.rmtree(WORK_DIR, ignore_errors=True)
    shutil.copytree(SEED_DIR, WORK_DIR)
    save("drafts.json", [])
    save("archived.json", [])
    save("read.json", [])
    # 秘書がメールごとにしたことの記録（画面の「処理確認」で表示する）
    save("history.json", {})


def load(name: str):
    return json.loads((WORK_DIR / name).read_text(encoding="utf-8"))


def save(name: str, data) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    (WORK_DIR / name).write_text(text, encoding="utf-8")


def mark_as_read(email_id: str) -> None:
    """メールを既読にする。"""
    read = load("read.json")
    if email_id not in read:
        save("read.json", read + [email_id])


@tool
def list_emails() -> str:
    """受信箱のメールの一覧を、受信日時の新しい順に返す。

    アーカイブ済みのメールは含まない。
    各行は「ID | 受信日時 | 差出人 | 件名」の形式。
    """
    archived = load("archived.json")
    emails = [e for e in load("emails.json") if e["id"] not in archived]
    emails.sort(key=lambda e: e["date"], reverse=True)
    lines = []
    for email in emails:
        lines.append(
            f"{email['id']} | {email['date']} | "
            f"{email['from']} | {email['subject']}"
        )
    return "\n".join(lines)


@tool
def read_email(email_id: str) -> str:
    """指定したIDのメールを、ヘッダと本文を含めて返す。読んだメールは既読になる。

    Args:
        email_id: メールのID（例: m01）
    """
    for email in load("emails.json"):
        if email["id"] == email_id:
            mark_as_read(email_id)
            return (
                f"差出人: {email['from']}\n"
                f"宛先: {email['to']}\n"
                f"日時: {email['date']}\n"
                f"件名: {email['subject']}\n\n"
                f"{email['body']}"
            )
    return f"ID が {email_id} のメールは見つかりません。"


@tool
def save_reply_draft(email_id: str, body: str) -> str:
    """メールへの返信の下書きを保存する。メールは送信しない。

    Args:
        email_id: 返信するメールのID（例: m02）
        body: 返信の本文
    """
    drafts = load("drafts.json")
    drafts.append({"email_id": email_id, "body": body})
    save("drafts.json", drafts)
    return f"{email_id} への返信の下書きを保存しました。"


@tool
def list_events() -> str:
    """カレンダーに登録されている予定の一覧を返す。

    各行は「開始 〜 終了 | タイトル」の形式。
    """
    lines = []
    for event in sorted(load("calendar.json"), key=lambda e: e["start"]):
        lines.append(
            f"{event['start']} 〜 {event['end']} | {event['title']}"
        )
    return "\n".join(lines)


@tool
def add_event(email_id: str, title: str, start: str, end: str) -> str:
    """カレンダーに予定を登録する。

    Args:
        email_id: 予定のもとになったメールのID
        title: 予定のタイトル
        start: 開始日時（例: 2026-11-04T10:00:00+09:00）
        end: 終了日時（例: 2026-11-04T11:00:00+09:00）
    """
    events = load("calendar.json")
    events.append({"title": title, "start": start, "end": end,
                   "email_id": email_id})
    save("calendar.json", events)
    return f"予定を登録しました: {start} 〜 {end} {title}"


@tool
def add_task(email_id: str, title: str, due: str) -> str:
    """タスクを登録する。

    Args:
        email_id: タスクのもとになったメールのID
        title: タスクの内容
        due: 期限の日付（例: 2026-11-06）
    """
    tasks = load("tasks.json")
    tasks.append({"title": title, "due": due, "email_id": email_id})
    save("tasks.json", tasks)
    return f"タスクを登録しました: {due} {title}"


@tool
def archive_email(email_id: str) -> str:
    """メールをアーカイブして、受信箱から外す。

    Args:
        email_id: アーカイブするメールのID
    """
    archived = load("archived.json")
    archived.append(email_id)
    save("archived.json", archived)
    return f"{email_id} をアーカイブしました。"


TOOLS = [
    list_emails,
    read_email,
    save_reply_draft,
    list_events,
    add_event,
    add_task,
    archive_email,
]
