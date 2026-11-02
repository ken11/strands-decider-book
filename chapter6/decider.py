"""ローカルで動いている Strands Decider のサーバに質問するクライアント。"""

import json
import urllib.request

URL = "http://127.0.0.1:8099/v1/systemone"


def ask(state: str, questions: dict) -> dict:
    """state（判定する文章）について、questions の質問に答えてもらう。"""
    body = json.dumps({"state": state, "questions": questions}).encode()
    request = urllib.request.Request(
        URL, data=body, headers={"content-type": "application/json"}
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read())["answers"]


def noul(instructions: str, true: str, false: str) -> dict:
    """Yes / No で答える質問（noul）を作る。"""
    return {
        "type": "noul",
        "instructions": instructions,
        "criteria": {"true": true, "false": false},
    }


def choice(instructions: str, options: dict[str, str]) -> dict:
    """選択肢から1つを選ぶ質問（choice）を作る。"""
    return {
        "type": "choice",
        "instructions": instructions,
        "criteria": options,
    }


def score(instructions: str, levels: list[str]) -> dict:
    """段階で評価する質問（score）を作る。levels は低い順に並べる。"""
    return {
        "type": "score",
        "instructions": instructions,
        "criteria": levels,
    }
