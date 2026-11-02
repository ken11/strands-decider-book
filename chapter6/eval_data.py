"""第6章の100通のメールと、正解ラベルを読み込む。"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
EVAL_DIR = ROOT / "data" / "eval"
RESULTS_DIR = ROOT / "results"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


# 100通のメールと、正解ラベル
EMAILS = read_json(EVAL_DIR / "emails.json")
LABELS = read_json(EVAL_DIR / "labels.json")
PII_BY_ID = {label["id"]: label["pii"] for label in LABELS}

# 個人情報の種類と値の組み合わせ（重複を除く）
VALUES = {(p["type"], p["text"]) for label in LABELS for p in label["pii"]}
