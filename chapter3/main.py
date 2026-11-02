"""受信箱のすべてのメールを、秘書にまとめて整理させる。

画面を使わずに、まとめて実行したいときに使う。
"""

from secretary import SENT_LOG, run
from tools import load, reset_workspace

# 実行のたびに、作業ディレクトリ（workspace/）を初期状態に戻す
reset_workspace()

email_ids = [email["id"] for email in load("emails.json")]
result = run(email_ids)

usage = result.metrics.accumulated_usage
print(f"\n\n入力トークン: {usage['inputTokens']}")
print(f"出力トークン: {usage['outputTokens']}")
print(f"送信した内容: {SENT_LOG.relative_to(SENT_LOG.parent.parent)}")
