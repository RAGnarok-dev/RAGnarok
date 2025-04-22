import asyncio
import json
from typing import Any, Dict, Tuple

from openai import AsyncOpenAI
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)


class LLMRequestComponent(RagnarokComponent):
    """
    Component class for send requests to LLM
    """

    # the description of the component's functionality
    DESCRIPTION: str

    # whether to enable type annotation check for identification
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        """the options of all the input value"""
        return (
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
                name="temperature",
                allowed_types={ComponentIOType.FLOAT},
                required=True,
            ),
            ComponentInputTypeOption(
                name="top_p",
                allowed_types={ComponentIOType.FLOAT},
                required=True,
            ),
            ComponentInputTypeOption(
                name="model_name",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="model_name",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="messages",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        """the options of all the output value"""
        return (ComponentOutputTypeOption(name="out", type=ComponentIOType.STRING),)

    @classmethod
    async def execute(
        cls, api_key: str, base_url: str, temperature: float, top_p: float, model_name: str, messages: str
    ) -> Dict[str, Any]:
        """
        execute the component function, could be either sync or async
        """
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        messages = [
            {
                "role": "system",
                "content": "you are a helpful AI assistant for information retrieving",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": messages},
                ],
            },
        ]
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
                            "name": "information_retrieving",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "answer": {
                                        "type": "string",
                                    },
                                },
                                "required": [
                                    "answer",
                                ],
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
                await asyncio.sleep(1)

        return {"out": response_json.get("answer")}

    def __new__(cls, *args, **kwargs):
        raise TypeError(f"Class {cls.__name__} and its subclasses cannot be instantiated.")


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
                name="temperature",
                allowed_types={ComponentIOType.FLOAT},
                required=True,
            ),
            ComponentInputTypeOption(
                name="top_p",
                allowed_types={ComponentIOType.FLOAT},
                required=True,
            ),
            ComponentInputTypeOption(
                name="model_name",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="intent_dict",
                allowed_types={ComponentIOType.DICT},  # expects JSON string
                required=True,
            ),
            ComponentInputTypeOption(
                name="user_question",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (ComponentOutputTypeOption(name="out", type=ComponentIOType.STRING),)

    @classmethod
    async def execute(
        cls,
        api_key: str,
        base_url: str,
        temperature: float,
        top_p: float,
        model_name: str,
        intent_dict: dict,
        user_question: str,
    ) -> Dict[str, Any]:
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
                await asyncio.sleep(1)

        return {"out": response_json.get("intent")}

    def __new__(cls, *args, **kwargs):
        raise TypeError(f"Class {cls.__name__} and its subclasses cannot be instantiated.")
