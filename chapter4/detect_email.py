"""メール1通を1文ずつに分けて、含まれる個人情報の種類を判定する。"""

import json
import sys
from pathlib import Path

from decider import ask
from pii_questions import QUESTIONS, split_segments

THRESHOLD = 0.5
EMAILS_PATH = Path(__file__).parent.parent / "data" / "seed" / "emails.json"

email_id = sys.argv[1] if len(sys.argv) > 1 else "m14"
emails = json.loads(EMAILS_PATH.read_text(encoding="utf-8"))
email = next(e for e in emails if e["id"] == email_id)

for segment in split_segments(email["body"]):
    answers = ask(segment, QUESTIONS)
    found = [
        f"{name} {answer['noul']:.2f}"
        for name, answer in answers.items()
        if answer["noul"] >= THRESHOLD
    ]
    mark = "*" if found else " "
    print(f"{mark} {segment}")
    if found:
        print(f"    -> {', '.join(found)}")
