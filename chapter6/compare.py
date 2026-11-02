"""伏せ方としきい値を変えて、送られる個人情報と丸ごと伏せるメールを比べる。

Bedrock は使わない。対象は100通のメール（read_email の結果）だけ。
元の単位の判定は、score.py で保存した結果（results/scores/）を使う。
伏せ字にした単位は Decider で判定し、results/masked/ に保存する。

  A. 第5章の仕組み: Decider で検出した単位だけを伏せ字にし、再判定する
  B. Presidio だけ: すべての単位を Presidio で伏せ字にする
  C. 全部を伏せ字にして再判定: すべての単位を伏せ字にしてから、再判定する

使い方: uv run --group mask python chapter6/compare.py
（伏せ字にした文の判定には、Decider のサーバで動いているモデルを使う）
"""

import json

from decider import ask
from eval_data import EMAILS, RESULTS_DIR, VALUES, read_json
from masking import mask
from pii_questions import QUESTIONS
from score import SCORES_DIR, model_name, units

THRESHOLDS = [0.3, 0.5]
model = model_name()
rows = read_json(SCORES_DIR / f"{model}.json")
scores = {row["segment"]: row["scores"] for row in rows}
masked_path = RESULTS_DIR / "masked" / f"{model}.json"
masked_scores = read_json(masked_path) if masked_path.exists() else {}
masked_texts = {}
# 丸ごと伏せたメールと、伏せきれなかった単位（伏せ字にしたあと）
stopped = {}


def score(unit: str) -> dict:
    """判定の結果。伏せ字にした単位は、初回だけ Decider に問い合わせる。"""
    if unit in scores:
        return scores[unit]
    if unit not in masked_scores:
        answers = ask(unit, QUESTIONS)
        masked_scores[unit] = {n: a["noul"] for n, a in answers.items()}
    return masked_scores[unit]


def masked(unit: str) -> str:
    if unit not in masked_texts:
        masked_texts[unit] = mask(unit)
    return masked_texts[unit]


def protect(email: dict, strategy: str, threshold: float) -> str | None:
    """1通を保護して、送る内容を返す。丸ごと伏せるときは None を返す。"""
    sent = []
    for unit in units(email):
        detected = max(score(unit).values()) >= threshold
        if strategy in ("B", "C") or detected:
            unit = masked(unit)
            if strategy != "B" and max(score(unit).values()) >= threshold:
                stopped[email["id"]] = unit
                return None
        sent.append(unit)
    return "\n".join(sent)


print(f"モデル: {model}\n")
print("やり方 しきい値 丸ごと伏せたメール 送られた値")
details = {}
for strategy in ["A", "B", "C"]:
    for threshold in THRESHOLDS if strategy != "B" else [None]:
        stopped.clear()
        results = [protect(e, strategy, threshold or 0.5) for e in EMAILS]
        sent = "\n".join(r for r in results if r is not None)
        leaked = sorted((t, x) for t, x in VALUES if x in sent)
        withheld = results.count(None)
        label = f"{strategy} {threshold or '-'}"
        print(f"{label} {withheld}通 {len(leaked)} / {len(VALUES)}")
        details[strategy, threshold] = (dict(stopped), leaked)

stopped_a, leaked_a = details["A", 0.5]
print("\nA（しきい値0.5）で丸ごと伏せたメールと、伏せきれなかった単位:")
for email_id, unit in stopped_a.items():
    found = [n for n, p in score(unit).items() if p >= 0.5]
    print(f"  {email_id} {unit}  {', '.join(found)}")
for strategy, threshold in [("A", 0.5), ("B", None)]:
    print(f"\n{strategy}（しきい値{threshold or '-'}）で送られた値:")
    for pii_type, text in details[strategy, threshold][1]:
        print(f"  {pii_type:16} {text}")

masked_path.parent.mkdir(exist_ok=True)
text = json.dumps(masked_scores, ensure_ascii=False, indent=1)
masked_path.write_text(text, encoding="utf-8")
