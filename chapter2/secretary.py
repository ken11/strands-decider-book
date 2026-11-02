"""AIメール秘書。指定したメールを確認して、整理する。"""

from strands import Agent
from strands.agent import AgentResult
from strands.models import BedrockModel
from strands.tools.executors import SequentialToolExecutor

from tools import TOOLS, load, save

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
    """秘書がメールごとにしたことを、会話の履歴から取り出して記録する。"""
    history = load("history.json")
    for email_id in email_ids:
        history[email_id] = {"actions": []}
    for message in messages:
        for block in message["content"]:
            tool_use = block.get("toolUse")
            if tool_use and tool_use["name"] != "read_email":
                email_id = tool_use["input"].get("email_id")
                if email_id in history:
                    history[email_id]["actions"].append(
                        {"tool": tool_use["name"], "input": tool_use["input"]}
                    )
    save("history.json", history)


def run(email_ids: list[str]) -> AgentResult:
    """指定したメールを、秘書に整理させる。"""
    agent = create_agent()
    result = agent(REQUEST.format(email_ids=", ".join(email_ids)))
    record(email_ids, agent.messages)
    return result
