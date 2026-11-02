"""AIメール秘書。指定したメールを確認して、整理する。

第3章では、モデルへの入力を送信ログ（workspace/sent_log.txt）に書き出し、
メールごとに、AIに渡した内容を記録する。
"""

import json

from strands import Agent
from strands.agent import AgentResult
from strands.hooks import BeforeModelCallEvent
from strands.models import BedrockModel
from strands.tools.executors import SequentialToolExecutor

from tools import TOOLS, WORK_DIR, load, save

SENT_LOG = WORK_DIR / "sent_log.txt"

SYSTEM_PROMPT = """あなたは株式会社見本ソフトの青木 陽介のメール秘書です。
今日は2026年11月2日（月）です。

秘書として、次のことを守ってください。
- メールは送信しない。返信は下書きとして保存する
- 予定を登録するときは、既存の予定と重ならないか確認する
- 不審なメールのURLは開かない"""

REQUEST = """次のメールを確認して、整理してください。
対象のメール: {email_ids}

- 返信が必要なメールには、返信の下書きを保存する
- 日時が決まった予定は、カレンダーに登録する
- 期限のある作業は、タスクとして登録する
- ニュースレター、広告、不審なメールはアーカイブする

最後に、対応した内容を短く報告してください。"""


def render(message: dict) -> str:
    """モデルへの入力を、人が読みやすいテキストにする。

    モデル自身の出力（応答の文章やツール呼び出しの引数）は書き出さない。
    どのツールを呼び出したかだけ、ツール名を残す。
    """
    lines = []
    for block in message["content"]:
        if "text" in block and message["role"] == "user":
            lines.append(f"[user] {block['text']}")
        elif "toolUse" in block:
            lines.append(f"[ツール呼び出し] {block['toolUse']['name']}")
        elif "toolResult" in block:
            for content in block["toolResult"]["content"]:
                lines.append(f"[ツールの結果]\n{content.get('text', '')}")
    return "\n".join(lines)


class SentLog:
    """モデルを呼び出す直前に、モデルへの入力を送信ログに書き出すフック。

    ハンズオンで観察するためのもの。実際のシステムでは、
    個人情報を含みうる内容をログに出してはいけない。
    """

    def __init__(self) -> None:
        self.calls = 0
        self.logged = 0

    def log_model_call(self, event: BeforeModelCallEvent) -> None:
        self.calls += 1
        messages = event.agent.messages
        size = len(json.dumps(messages, ensure_ascii=False))
        with SENT_LOG.open("a", encoding="utf-8") as f:
            f.write(
                f"===== {self.calls}回目の呼び出し: "
                f"メッセージ {len(messages)}件 / {size}文字 =====\n"
            )
            # システムプロンプトは毎回一緒に送られる。最初の1回だけ書き出す
            if self.calls == 1:
                f.write(f"[system] {event.agent.system_prompt}\n")
            # 前回の呼び出しから増えたメッセージだけを書き出す
            for message in messages[self.logged :]:
                f.write(render(message) + "\n")
        self.logged = len(messages)


def create_agent() -> Agent:
    model = BedrockModel(
        model_id="global.anthropic.claude-sonnet-5-5",
        region_name="ap-northeast-1",
        max_tokens=16000,
    )
    return Agent(
        model=model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        tool_executor=SequentialToolExecutor(),
    )


def record(email_ids: list[str], messages: list[dict]) -> None:
    """メールごとに、AIに渡した内容と、秘書がしたことを記録する。"""
    history = load("history.json")
    for email_id in email_ids:
        history[email_id] = {"actions": []}
    calls = {}  # ツール呼び出しのID → 呼び出し
    for message in messages:
        for block in message["content"]:
            if "toolUse" in block:
                tool_use = block["toolUse"]
                calls[tool_use["toolUseId"]] = tool_use
                email_id = tool_use["input"].get("email_id")
                if email_id in history and tool_use["name"] != "read_email":
                    history[email_id]["actions"].append(
                        {"tool": tool_use["name"], "input": tool_use["input"]}
                    )
            if "toolResult" in block:
                result = block["toolResult"]
                tool_use = calls[result["toolUseId"]]
                email_id = tool_use["input"].get("email_id")
                if tool_use["name"] == "read_email" and email_id in history:
                    text = "".join(c.get("text", "") for c in result["content"])
                    history[email_id]["sent"] = text
    save("history.json", history)


def run(email_ids: list[str]) -> AgentResult:
    """指定したメールを、秘書に整理させる。"""
    agent = create_agent()
    agent.add_hook(SentLog().log_model_call)
    result = agent(REQUEST.format(email_ids=", ".join(email_ids)))
    record(email_ids, agent.messages)
    return result
