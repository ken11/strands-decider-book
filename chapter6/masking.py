"""GiNZA と Presidio を使って、日本語の文章の個人情報を伏せ字にする。"""

from presidio_analyzer import (
    AnalyzerEngine,
    Pattern,
    PatternRecognizer,
    RecognizerRegistry,
)
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.predefined_recognizers import (
    CreditCardRecognizer,
    EmailRecognizer,
)
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# 1. GiNZA の固有表現抽出で見つけるもの
#    GiNZA の種類と、伏せ字にするときの種類名の対応
ENTITY_MAPPING = {
    "Person": "PERSON_NAME",
    "Phone_Number": "PHONE",
    "Postal_Address": "ADDRESS",
    "ID_Number": "ID_NUMBER",
}

# 2. 形式が決まっているものは、正規表現で見つける
PATTERNS = {
    "MY_NUMBER": r"(?<!\d)\d{4} ?\d{4} ?\d{4}(?!\d)",
    "BANK_ACCOUNT": r"(普通|当座)\s*\d{7}(?!\d)",
    "POSTAL_CODE": r"〒\s?\d{3}-\d{4}",
    "BIRTH_DATE": r"(?<=生年月日[:：])\s*\d{4}年\d{1,2}月\d{1,2}日"
    r"|\d{4}年\d{1,2}月\d{1,2}日(?=生まれ)",
}

ENTITIES = [*ENTITY_MAPPING.values(), *PATTERNS, "EMAIL", "CREDIT_CARD"]

provider = NlpEngineProvider(
    nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [
            {"lang_code": "ja", "model_name": "ja_ginza_bert_large"},
        ],
        "ner_model_configuration": {
            "model_to_presidio_entity_mapping": ENTITY_MAPPING,
        },
    }
)
nlp_engine = provider.create_engine()

registry = RecognizerRegistry(supported_languages=["ja"])
# GiNZA の結果を読み取る検出器
registry.load_predefined_recognizers(
    nlp_engine=nlp_engine, languages=["ja"]
)
# メールアドレスとカード番号は、Presidio に用意されている検出器を使う
# （GiNZA が見つけるメールアドレスは、前後の記号で範囲がずれることがある）
registry.add_recognizer(
    EmailRecognizer(supported_language="ja", supported_entity="EMAIL")
)
registry.add_recognizer(CreditCardRecognizer(supported_language="ja"))
# 正規表現の検出器。GiNZA の結果より優先されるよう、スコアを高くする
for entity, regex in PATTERNS.items():
    registry.add_recognizer(
        PatternRecognizer(
            supported_entity=entity,
            supported_language="ja",
            patterns=[Pattern(name=entity, regex=regex, score=0.95)],
        )
    )

analyzer = AnalyzerEngine(
    nlp_engine=nlp_engine, registry=registry, supported_languages=["ja"]
)
anonymizer = AnonymizerEngine()

# 見つけた個人情報を、[PERSON_NAME] のような種類名に置き換える
OPERATORS = {
    entity: OperatorConfig("replace", {"new_value": f"[{entity}]"})
    for entity in ENTITIES
}


def mask(text: str) -> str:
    """文章に含まれる個人情報を、種類名に置き換える。"""
    results = analyzer.analyze(text=text, language="ja", entities=ENTITIES)
    return anonymizer.anonymize(
        text=text, analyzer_results=results, operators=OPERATORS
    ).text
