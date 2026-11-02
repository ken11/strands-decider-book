"""受信箱のすべてのメールを、秘書にまとめて整理させる。

画面を使わずに、まとめて実行したいときに使う。

使い方:
  uv run --group mask python chapter5/main.py          # AI秘書
  uv run --group mask python chapter5/main.py --guard  # 個人情報をケアしたAI秘書
"""

import argparse

from secretary import SENT_LOG, run
from tools import load, reset_workspace

parser = argparse.ArgumentParser()
parser.add_argument("--guard", action="store_true")
args = parser.parse_args()

# 実行のたびに、作業ディレクトリ（workspace/）を初期状態に戻す
reset_workspace()

email_ids = [email["id"] for email in load("emails.json")]
result = run(email_ids, guard=args.guard)

usage = result.metrics.accumulated_usage
print(f"\n\n入力トークン: {usage['inputTokens']}")
print(f"出力トークン: {usage['outputTokens']}")
print(f"送信した内容: {SENT_LOG.relative_to(SENT_LOG.parent.parent)}")
