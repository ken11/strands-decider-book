"""AIメール秘書。指定したメールを確認して、整理する。

モデルへの入力を送信ログ（workspace/sent_log.txt）に書き出し、
メールごとに、AIに渡した内容を記録する。
第5章からは、個人情報を守る仕組み（PrivacyGuard）を使うかどうかを選べる。
"""

import json

from strands import Agent
from strands.agent import AgentResult
from strands.hooks import BeforeModelCallEvent
from strands.models import BedrockModel
from strands.tools.executors import SequentialToolExecutor

from privacy_guard import WITHHELD, PrivacyGuard
from tools import TOOLS, WORK_DIR, load, save

SENT_LOG = WORK_DIR / "sent_log.txt"

SYSTEM_PROMPT = """あなたは株式会社見本ソフトの青木 陽介のメール秘書です。
今日は2026年11月2日（月）です。

秘書として、次のことを守ってください。
- メールは送信しない。返信は下書きとして保存する
- 予定を登録するときは、既存の予定と重ならないか確認する
- 不審なメールのURLは開かない"""

# 個人情報を守る仕組みを使うときに、システムプロンプトに足すルール
GUARD_RULES = """
- [PERSON_NAME] のような表記は、個人情報を伏せた部分。下書きでもそのまま使う
- 内容が伏せられたメールは、推測せず、確認が必要なメールとして報告する"""

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


def create_agent(guard: PrivacyGuard | None = None) -> Agent:
    model = BedrockModel(
        model_id="global.anthropic.claude-sonnet-5-5",
        region_name="ap-northeast-1",
        max_tokens=16000,
    )
    return Agent(
        model=model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT + (GUARD_RULES if guard else ""),
        tool_executor=SequentialToolExecutor(),
        interventions=[guard] if guard else [],
    )


def status_of(original: str, sent: str) -> str:
    """読んだメールを、どうAIに渡したかを返す。"""
    if sent == WITHHELD:
        return "withheld"  # 丸ごと伏せた
    if sent != original:
        return "masked"  # 伏せ字にして渡した
    return "as_is"  # そのまま渡した


def record(email_ids: list[str], messages: list[dict], guard: bool,
           guarded: dict) -> None:
    """メールごとに、AIに渡した内容と、秘書がしたことを記録する。

    guarded は、PrivacyGuard が保護する前の内容と、判定の記録
    （ツール呼び出しのID → (元の内容, 判定の記録)）。
    """
    history = load("history.json")
    for email_id in email_ids:
        history[email_id] = {"actions": [], "guard": guard}
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
                    original, trace = guarded.get(result["toolUseId"], (text, []))
                    history[email_id]["status"] = status_of(original, text)
                    history[email_id]["trace"] = trace
    save("history.json", history)


def run(email_ids: list[str], guard: bool = False) -> AgentResult:
    """指定したメールを、秘書に整理させる。guard が True なら、個人情報を守る。"""
    guarded = {}

    def on_result(tool_use, original, sent, trace):
        guarded[tool_use["toolUseId"]] = (original, trace)

    agent = create_agent(PrivacyGuard(on_result) if guard else None)
    agent.add_hook(SentLog().log_model_call)
    result = agent(REQUEST.format(email_ids=", ".join(email_ids)))
    record(email_ids, agent.messages, guard, guarded)
    return result
