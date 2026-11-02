import json
from pathlib import Path

from strands import Agent, tool
from strands.models import BedrockModel

EMAILS_PATH = Path(__file__).parent.parent / "data" / "seed" / "emails.json"


def load_emails() -> list[dict]:
    return json.loads(EMAILS_PATH.read_text(encoding="utf-8"))


@tool
def list_emails() -> str:
    """受信メールの一覧を、受信日時の新しい順に返す。

    各行は「ID | 受信日時 | 差出人 | 件名」の形式。
    """
    emails = sorted(load_emails(), key=lambda e: e["date"], reverse=True)
    lines = []
    for email in emails:
        lines.append(
            f"{email['id']} | {email['date']} | "
            f"{email['from']} | {email['subject']}"
        )
    return "\n".join(lines)


@tool
def read_email(email_id: str) -> str:
    """指定したIDのメールを、ヘッダと本文を含めて返す。

    Args:
        email_id: メールのID（例: m01）
    """
    for email in load_emails():
        if email["id"] == email_id:
            return (
                f"差出人: {email['from']}\n"
                f"宛先: {email['to']}\n"
                f"日時: {email['date']}\n"
                f"件名: {email['subject']}\n\n"
                f"{email['body']}"
            )
    return f"ID が {email_id} のメールは見つかりません。"


model = BedrockModel(
    model_id="global.anthropic.claude-sonnet-5-5",
    region_name="ap-northeast-1",
)
agent = Agent(
    model=model,
    tools=[list_emails, read_email],
    system_prompt=(
        "あなたは株式会社見本ソフトの青木 陽介のメール秘書です。"
        "今日は2026年11月2日（月）です。"
    ),
)

agent("今朝届いたメールを確認して、内容を短く要約してください。")
