"""広い質問1つで聞く場合と、種類ごとに1問ずつ聞く場合を比べる。"""

from decider import ask, noul
from pii_questions import QUESTIONS

BROAD = {
    "broad": noul(
        "Does this text contain personal information?",
        true="The text contains personal information about a person.",
        false="The text contains no personal information.",
    )
}

SENTENCES = [
    "住所：〒166-0000 東京都杉並区見本町3-4-5 見本ハイツ202",
    "マイナンバー：1234 5678 9010",
    "カード番号：4111-1111-1111-1111",
    "実は妊娠がわかり、来年の3月ごろから産休をいただきたいと考えています。",
    "11月の営業部定例を次の日程で行います。",
]

for sentence in SENTENCES:
    broad = ask(sentence, BROAD)["broad"]["noul"]
    answers = ask(sentence, QUESTIONS)
    name, best = max(answers.items(), key=lambda item: item[1]["noul"])
    print(sentence)
    print(f"  広い質問: {broad:.2f}")
    print(f"  種類ごと: {best['noul']:.2f}（{name}）")
