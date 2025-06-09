import ast
import asyncio
import json
from typing import Any, Dict, Optional, Tuple

from openai import AsyncOpenAI
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)


class LLMIntentRecognitionComponent(RagnarokComponent):
    """
    Component class for LLM-based intent recognition.
    """

    DESCRIPTION: str = "Classify user intent using LLM based on provided intents and user input"

    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="user_question",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="intent_dict",
                allowed_types={ComponentIOType.DICT},  # expects JSON string
                required=True,
            ),
            ComponentInputTypeOption(
                name="model_name",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="api_key",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="base_url",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="max_retries",
                allowed_types={ComponentIOType.INT},
                required=False,
            ),
            ComponentInputTypeOption(
                name="temperature",
                allowed_types={ComponentIOType.FLOAT},
                required=True,
            ),
            ComponentInputTypeOption(
                name="top_p",
                allowed_types={ComponentIOType.FLOAT},
                required=True,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (ComponentOutputTypeOption(name="out", type=ComponentIOType.STRING),)

    @classmethod
    async def execute(
        cls,
        user_question: str,
        intent_dict: dict,
        model_name: str,
        api_key: str,
        base_url: str,
        max_retries: Optional[int],
        temperature: float,
        top_p: float,
    ) -> Dict[str, Any]:
        user_question = str(user_question)
        intent_dict = ast.literal_eval(intent_dict)
        max_retries = int(max_retries)
        temperature = float(temperature)
        top_p = float(top_p)

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        # Format the intent list for the prompt
        intent_text = "\n".join([f"{k}: {v}" for k, v in intent_dict.items()])

        messages = [
            {
                "role": "system",
                "content": "You are an AI assistant that classifies the user's intent"
                "based on a list of predefined categories.",
            },
            {
                "role": "user",
                "content": f"""
                    Here are the possible intent categories:
                    {intent_text}

                    Classify the following question into one of the intent
                    categories by returning only the intent number (e.g., "0", "1", "2", etc.).

                    Question: {user_question}
                    """,
            },
        ]

        retries = 0
        while True:
            try:
                completion = await client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    timeout=30,
                    temperature=temperature,
                    top_p=top_p,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "intent_classification",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "intent": {
                                        "type": "number",
                                    },
                                },
                                "required": ["intent"],
                                "additionalProperties": False,
                            },
                            "strict": True,
                        },
                    },
                )
                response = completion.choices[0].message.content
                response_json = json.loads(response)
                break

            except Exception as e:
                print(f"Retrying call {model_name}", e)
                retries += 1
                if retries == max_retries:
                    response_json = {"intent": f"Error: {e}. Max retries exceeded!"}
                    break
                await asyncio.sleep(1)

        return {"out": response_json.get("intent")}
