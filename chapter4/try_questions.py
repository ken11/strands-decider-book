from decider import ask, choice, noul, score

STATE = """件名: 本日お休みをいただきます

昨晩から熱が続いていたため、今朝病院を受診したところ、
インフルエンザと診断されました。
本日予定していた訪問は、先方に延期の連絡を入れました。"""

QUESTIONS = {
    "category": choice(
        "Which category best describes this email?",
        {
            "absence": "the sender will be absent from work",
            "meeting": "the sender wants to schedule a meeting",
            "sales": "the sender is selling a product or service",
        },
    ),
    "needs_reply": noul(
        "Should the recipient reply to this email?",
        true="the recipient is expected to reply or acknowledge",
        false="no reply is needed",
    ),
    "urgency": score(
        "How urgent is this email for the recipient?",
        ["not urgent", "somewhat urgent", "very urgent"],
    ),
}

answers = ask(STATE, QUESTIONS)

category = answers["category"]
confidence = category["confidence"]
print(f"category: {category['choice']}（確信度 {confidence:.2f}）")
for option, probability in category["probabilities"].items():
    print(f"    {option:16} {probability:.2f}")

print(f"needs_reply: {answers['needs_reply']['noul']:.2f}")

urgency = answers["urgency"]
confidence = urgency["confidence"]
print(f"urgency: {urgency['score']:.2f}（確信度 {confidence:.2f}）")
for level, probability in urgency["probabilities"].items():
    print(f"    {urgency['legend'][level]:16} {probability:.2f}")
