import asyncio
import json
from typing import Any, Dict, Tuple

from openai import OpenAI
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
    async def execute(cls, api_key: str, base_url: str, model_name: str, messages: str) -> Dict[str, Any]:
        """
        execute the component function, could be either sync or async
        """
        client = OpenAI(api_key=api_key, base_url=base_url)
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
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    timeout=30,
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
