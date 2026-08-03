# mypy: ignore-errors
import os

from openai import NOT_GIVEN, OpenAI

from models.base import BaseModel, Conversation, Response, record_token_usage


class OpenAIModel(BaseModel):

    context_lengths = {
        "gpt-5": 400000,
        "gpt-5.5": 400000,
        "gpt-5.4": 400000,
        "gpt-5.4-mini": 400000,
    }

    max_completion_tokens = {
        "gpt-5": 128000,
        "gpt-5.5": 128000,
        "gpt-5.4": 128000,
        "gpt-5.4-mini": 128000,
        "huihui_ai/glm-4.7-flash-abliterated:q4_K": 32768,
    }

    def __init__(
        self,
        model_name: str,
        model_provider: str,
        reasoning: bool = False,
        reasoning_effort: int | str | None = None,
    ):
        super().__init__(model_name, model_provider, reasoning, reasoning_effort)
        self.client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.environ.get("OPENAI_BASE_URL"),
            timeout=float(os.environ.get("OPENAI_TIMEOUT", "60")),
            max_retries=int(os.environ.get("OPENAI_MAX_RETRIES", "5")),
        )

    def _generate_chat(
        self, conversation: Conversation, temperature: float, purpose: str
    ) -> Response:
        completion = self.client.chat.completions.create(
            model=self.model_name,
            max_completion_tokens=self.max_completion_tokens.get(self.model_name, 8192),
            n=1,
            temperature=temperature,
            messages=self._conv_to_messages(conversation, system="system"),
        )
        if completion.usage is not None:
            record_token_usage(
                completion.usage.prompt_tokens,
                completion.usage.completion_tokens,
                self.model_name,
                thinking=False,
                purpose=purpose,
            )
        message = completion.choices[0].message
        text = message.content or getattr(message, "reasoning", None)
        if text is None or len(text) == 0:
            raise Exception("Empty response")
        else:
            return Response(role="assistant", text=text)

    def _generate_reason(
        self, conversation: Conversation, temperature: float, purpose: str
    ) -> Response:
        if self.model_name == "o1-mini":
            messages = self._conv_to_messages(conversation, system=None)
        else:
            messages = self._conv_to_messages(conversation, system="developer")
        completion = self.client.chat.completions.create(
            model=self.model_name,
            max_completion_tokens=self.max_completion_tokens.get(self.model_name, 8192),
            n=1,
            messages=messages,
            reasoning_effort=(
                NOT_GIVEN if self.model_name == "o1-mini" else self.reasoning_effort
            ),
        )
        if completion.usage is not None:
            record_token_usage(
                completion.usage.prompt_tokens,
                completion.usage.completion_tokens,
                self.model_name,
                thinking=self.reasoning_effort,
                purpose=purpose,
            )
        message = completion.choices[0].message
        text = message.content or getattr(message, "reasoning", None)
        if len(text) == 0:
            raise Exception("Empty response")
        else:
            return Response(role="assistant", text=text)
