"""ツールの結果をクラウドの LLM に送る前に、個人情報を判定して伏せる。"""

import re

from strands.hooks import AfterToolCallEvent
from strands.interventions import InterventionHandler, Proceed, Transform

from decider import ask
from masking import mask
from pii_questions import QUESTIONS

THRESHOLD = 0.5
WITHHELD = "（個人情報が含まれるため、内容を伏せました）"
# 手元のデータを読み出すツール。書き込み系のツールの結果は、
# モデルが渡した内容を繰り返すだけなので、保護しない
READ_TOOLS = {"list_emails", "read_email", "list_events"}

# 画面に表示するための、判定と伏せ字の記録。ツールの結果ごとに作り直す
trace: list[dict] = []


def detect(segment: str) -> list[str]:
    """1文について、しきい値以上だった個人情報の種類を返す。"""
    answers = ask(segment, QUESTIONS)
    scores = {name: answer["noul"] for name, answer in answers.items()}
    trace.append({"step": "detect", "text": segment, "scores": scores})
    return [name for name, p in scores.items() if p >= THRESHOLD]


def protect(text: str) -> str | None:
    """個人情報を伏せた文章を返す。伏せきれないときは None を返す。

    改行と「。」で1文ずつに分けて判定し、検出された文だけをマスクする。
    マスクした文をもう一度判定して、まだ残っていれば None を返す。
    """
    protected_lines = []
    for line in text.splitlines():
        segments = []
        for segment in re.split(r"(?<=。)", line):
            if segment.strip() and detect(segment):
                segment = mask(segment)
                trace.append({"step": "mask", "text": segment})
                if detect(segment):
                    return None
            segments.append(segment)
        protected_lines.append("".join(segments))
    return "\n".join(protected_lines)


def protect_email(text: str) -> str | None:
    """read_email の結果を保護する。伏せきれないときは None を返す。

    ヘッダはフィールドごとに保護する。日時は個人情報ではないので、そのまま残す。
    本文は、protect で1文ずつ保護する。
    """
    header, body = text.split("\n\n", 1)
    lines = []
    for line in header.splitlines():
        name, value = line.split(": ", 1)
        if name != "日時":
            value = protect(value)
            if value is None:
                return None
        lines.append(f"{name}: {value}")
    body = protect(body)
    if body is None:
        return None
    return "\n".join(lines) + "\n\n" + body


def protect_tool_result(tool_name: str, text: str) -> str:
    """ツールの結果を保護する。伏せきれない部分は、まとめて伏せる。"""
    if tool_name == "list_emails":
        # メール一覧は1行が1通。IDと日時は残し、差出人と件名を保護する
        lines = []
        for line in text.splitlines():
            email_id, date, sender, subject = line.split(" | ", 3)
            sender, subject = protect(sender), protect(subject)
            if sender is None or subject is None:
                lines.append(f"{email_id} | {date} | {WITHHELD}")
            else:
                lines.append(f"{email_id} | {date} | {sender} | {subject}")
        return "\n".join(lines)
    if tool_name == "read_email" and "\n\n" in text:
        return protect_email(text) or WITHHELD
    return protect(text) or WITHHELD


class PrivacyGuard(InterventionHandler):
    """個人情報をクラウドの LLM に送らないためのハンドラ。"""

    name = "privacy-guard"

    def __init__(self, on_result=None) -> None:
        # ツールの結果を保護するたびに呼ぶ関数（画面への表示用）
        self.on_result = on_result

    def after_tool_call(self, event: AfterToolCallEvent, **kwargs):
        """ツールの結果に含まれる個人情報を伏せる。"""
        tool_name = event.tool_use["name"]
        if tool_name not in READ_TOOLS:
            return Proceed()
        replacements = []
        for content in event.result["content"]:
            if "text" in content:
                trace.clear()
                try:
                    text = protect_tool_result(tool_name, content["text"])
                except Exception:
                    # 判定できないときは、送らない側に倒す
                    text = WITHHELD
                replacements.append(text)
                if self.on_result:
                    original = content["text"]
                    self.on_result(event.tool_use, original, text, list(trace))

        def apply(e: AfterToolCallEvent) -> None:
            texts = iter(replacements)
            for content in e.result["content"]:
                if "text" in content:
                    content["text"] = next(texts)

        return Transform(apply=apply)
