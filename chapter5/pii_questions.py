"""個人情報の種類ごとに1問ずつ用意した、Decider の質問。"""

import re

from decider import noul

QUESTIONS = {
    "PERSON_NAME": noul(
        "Does this text contain the name of a specific individual person?",
        true="A personal name appears, such as a family name, a given "
        "name, or a full name (for example 山田太郎, 山田, 花子, or John "
        "Smith), including names written in katakana or followed by "
        "honorifics such as さん, 様, 氏, or 殿, or by job titles such as "
        "課長 or 部長.",
        false="No personal name appears. Company names, department names, "
        "job titles, product names, and placeholders such as [PERSON_NAME] "
        "are not personal names.",
    ),
    "ADDRESS": noul(
        "Does this text contain a postal address?",
        true="A postal address appears, such as a prefecture, city, ward, "
        "town, street number, or building name and room number that "
        "locates a place.",
        false="No postal address appears. A room name inside an office, a "
        "country name alone, or a placeholder such as [ADDRESS] is not a "
        "postal address.",
    ),
    "POSTAL_CODE": noul(
        "Does this text contain a Japanese postal code?",
        true="A seven-digit Japanese postal code appears, usually written "
        "as 〒123-4567 or 123-4567.",
        false="No postal code appears. Phone numbers, order numbers, "
        "prices, dates, and placeholders such as [POSTAL_CODE] are not "
        "postal codes.",
    ),
    "EMAIL": noul(
        "Does this text contain an email address?",
        true="An email address with an @ sign and a domain appears, such "
        "as taro@example.jp.",
        false="No email address appears. A website URL or a placeholder "
        "such as [EMAIL] is not an email address.",
    ),
    "PHONE": noul(
        "Does this text contain a phone number?",
        true="A phone number appears, such as a mobile number like "
        "090-0123-4567, a landline number like 03-0123-4567, or an "
        "internal extension number like 内線 1201.",
        false="No phone number appears. Order numbers, invoice numbers, "
        "dates, times, prices, and placeholders such as [PHONE] are not "
        "phone numbers.",
    ),
    "BIRTH_DATE": noul(
        "Does this text contain a person's date of birth?",
        true="The date on which a specific person was born appears, such "
        "as 1990年4月12日生まれ or a birthday written next to a person's "
        "name.",
        false="No date of birth appears. Meeting dates, deadlines, "
        "delivery dates, holidays, and placeholders such as [BIRTH_DATE] "
        "are not dates of birth.",
    ),
    "MY_NUMBER": noul(
        "Does this text contain a Japanese Individual Number (My Number)?",
        true="A twelve-digit Japanese Individual Number (マイナンバー) "
        "appears, for example 1234 5678 9012.",
        false="No Individual Number appears. The word マイナンバー alone, "
        "order numbers, and placeholders such as [MY_NUMBER] are not "
        "Individual Numbers.",
    ),
    "BANK_ACCOUNT": noul(
        "Does this text contain a bank account number?",
        true="A bank account number appears, usually with a bank name, a "
        "branch name, an account type such as 普通 or 当座, and a "
        "seven-digit number.",
        false="No bank account number appears. A bank name alone or a "
        "placeholder such as [BANK_ACCOUNT] is not a bank account number.",
    ),
    "CREDIT_CARD": noul(
        "Does this text contain a credit card number?",
        true="A credit card number of about sixteen digits appears, for "
        "example 4111-1111-1111-1111.",
        false="No credit card number appears. Order numbers, phone "
        "numbers, and placeholders such as [CREDIT_CARD] are not credit "
        "card numbers.",
    ),
    "HEALTH": noul(
        "Does this text reveal information about a specific person's "
        "health?",
        true="The text reveals a specific person's illness, injury, "
        "medical examination result, hospital visit, a doctor's "
        "instructions such as resting at home, pregnancy or the stage of a "
        "pregnancy, or other health condition.",
        false="The text does not reveal any specific person's health "
        "condition. General announcements such as a company-wide health "
        "checkup schedule do not count.",
    ),
    "SALARY": noul(
        "Does this text reveal information about a specific person's "
        "salary or pay?",
        true="The text reveals a specific person's salary, bonus, raise, "
        "pay cut, or other compensation.",
        false="The text does not reveal any specific person's "
        "compensation. Company revenue, product prices, and invoice "
        "amounts do not count.",
    ),
    "EVALUATION": noul(
        "Does this text reveal a specific person's performance evaluation?",
        true="The text reveals a specific person's performance rating, "
        "appraisal result, promotion decision, or disciplinary action.",
        false="The text does not reveal any specific person's performance "
        "evaluation. A schedule for evaluation meetings alone does not "
        "count.",
    ),
}


def split_segments(text: str) -> list[str]:
    """文章を、改行と「。」で1文ずつに分割する。"""
    segments = []
    for line in text.splitlines():
        for segment in re.split(r"(?<=。)", line):
            if segment.strip():
                segments.append(segment.strip())
    return segments
