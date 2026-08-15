from openai import OpenAI
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase
from deepeval import evaluate
from config import Config


class CustomLLM(DeepEvalBaseLLM):
    def __init__(self, model: str, api_key: str, base_url: str = None):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def load_model(self): return self._client

    def generate(self, prompt: str) -> str:
        return self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
        ).choices[0].message.content

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self) -> str:
        return self._model


# ── Pick your LLM ─────────────────────────────────────────
kimi = CustomLLM(
    model=Config.KIMI_MODEL,
    api_key=Config.KIMI_API_KEY,
    base_url=Config.KIMI_BASE_URL,
)

groq = CustomLLM(
    model="llama-3.3-70b-versatile",
    api_key=Config.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

gpt_oss = CustomLLM(
    model="openai/gpt-oss-120b",
    api_key=Config.GROQ_API_KEY,
    base_url="https://your-base-url/v1",  # or None for standard OpenAI
)

# ── Test Case ──────────────────────────────────────────────
test_case = LLMTestCase(
    input="What if these shoes don't fit?",
    actual_output="We offer a 30-day full refund at no extra cost.",
)

# ── Evaluate (swap model= to switch LLM) ──────────────────
metric = AnswerRelevancyMetric(
    threshold=0.7,
    model=groq,  # 👈 change to kimi / gpt_oss / groq
    include_reason=True,
)

evaluate(test_cases=[test_case], metrics=[metric])