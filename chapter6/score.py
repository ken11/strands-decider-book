"""100通のメールを Decider で判定し、results/scores/ に保存する。

Bedrock は使わない。結果は、サーバで動いているモデルの名前で保存する。
判定する単位は、privacy_guard.py の protect_email と同じにする。
差出人・宛先・件名はフィールドごと、本文は改行と「。」で1文ずつ。
日時は判定しない。
"""

import json
import re
import time
import urllib.request

from decider import URL, ask
from eval_data import EMAILS, PII_BY_ID, RESULTS_DIR
from pii_questions import QUESTIONS

SCORES_DIR = RESULTS_DIR / "scores"


def model_name() -> str:
    """Decider のサーバで動いているモデルの名前を返す。"""
    health = URL.replace("/v1/systemone", "/health")
    with urllib.request.urlopen(health) as response:
        return json.loads(response.read())["model"]


def segments(text: str) -> list[str]:
    """文章を、改行と「。」で1文ずつに分ける。"""
    return [
        segment
        for line in text.splitlines()
        for segment in re.split(r"(?<=。)", line)
        if segment.strip()
    ]


def units(email: dict) -> list[str]:
    """メールを、判定する単位に分ける。"""
    header = [email["from"], email["to"], email["subject"]]
    return header + segments(email["body"])


def truth(email_id: str, unit: str) -> list[str]:
    """正解: この単位に含まれる個人情報の種類。"""
    pii = PII_BY_ID[email_id]
    return sorted({p["type"] for p in pii if p["text"] in unit})


if __name__ == "__main__":
    SCORES_DIR.mkdir(parents=True, exist_ok=True)
    path = SCORES_DIR / f"{model_name()}.json"
    # 途中で止まったときは、判定済みの単位を使い回して続きから判定する
    done = {}
    if path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        done = {row["segment"]: row["scores"] for row in saved}
    rows = []
    start = time.perf_counter()
    for email in EMAILS:
        for unit in units(email):
            if unit not in done:
                answers = ask(unit, QUESTIONS)
                done[unit] = {n: a["noul"] for n, a in answers.items()}
            rows.append({
                "email_id": email["id"],
                "segment": unit,
                "truth": truth(email["id"], unit),
                "scores": done[unit],
            })
        text = json.dumps(rows, ensure_ascii=False, indent=1)
        path.write_text(text, encoding="utf-8")
        seconds = time.perf_counter() - start
        print(f"{email['id']}: {len(rows)}件 {seconds:.0f}秒", flush=True)
