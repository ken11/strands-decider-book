from strands import Agent
from strands.models import BedrockModel

model = BedrockModel(
    model_id="global.anthropic.claude-sonnet-5-5",
    region_name="ap-northeast-1",
)
agent = Agent(model=model)

agent("こんにちは。あなたにできることを3つ教えてください。")
