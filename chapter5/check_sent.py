"""モデルへの入力に、正解ラベルの個人情報がいくつ含まれていたかを数える。

送信ログには、システムプロンプト、依頼文、ツールの結果が書き出されている。
モデル自身の出力（返信の下書きなど）は書き出していないので、数えない。
同じ値（たとえば同じ人名）が複数のメールに出てくることがあるので、
種類と値の組み合わせの重複を除いて数える。
"""

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent
LABELS_PATH = ROOT / "data" / "labels" / "emails.json"
SENT_LOG = ROOT / "workspace" / "sent_log.txt"

labels = json.loads(LABELS_PATH.read_text(encoding="utf-8"))
log = SENT_LOG.read_text(encoding="utf-8")

values = set()
for label in labels:
    for pii in label["pii"]:
        values.add((pii["type"], pii["text"]))
total = Counter(pii_type for pii_type, _ in values)
sent_values = sorted((t, text) for t, text in values if text in log)
sent = Counter(pii_type for pii_type, _ in sent_values)

print(f"{'種類':14} 送信された値 / 値の数")
for pii_type in sorted(total):
    print(f"{pii_type:16} {sent[pii_type]:>3} / {total[pii_type]:>3}")
print(f"{'合計':14} {sum(sent.values()):>5} / {sum(total.values()):>3}")

print("\n送信された値:")
for pii_type, text in sent_values:
    print(f"  {pii_type:16} {text}")
