import asyncio
import json
from typing import Any, Dict, List, Tuple

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
        """
        Executes the async retrieval function based on current question, history, and content.

        Parameters:
        - question: str, the user query.
        - content_list: List[str], background knowledge.
        - history: dict, previous dialogue history.
        - model_name, api_key, etc...

        Example format of `history`:
        history = {
            "messages": [
                {"role": "user", "content": "Hi, can you help me with X?"},
                {"role": "assistant", "content": "Sure, I can help you with X by doing Y."},
                {"role": "user", "content": "That sounds good. What about Z?"},
                {"role": "assistant", "content": "Regarding Z, here's what I found..."}
            ]
        }
        """

        return (
            ComponentInputTypeOption(
                name="user_question",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="content_list",
                allowed_types={ComponentIOType.STRING_LIST},
                required=True,
            ),
            ComponentInputTypeOption(
                name="user_history",
                allowed_types={ComponentIOType.DICT},
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
        """the options of all the output value"""
        return (ComponentOutputTypeOption(name="out", type=ComponentIOType.STRING),)

    @classmethod
    async def execute(
        cls,
        user_question: str,
        content_list: List[str],
        user_history: dict,
        model_name: str,
        api_key: str,
        base_url: str,
        temperature: float,
        top_p: float, 
    ) -> Dict[str, Any]:
        """
        execute the async component function
        """
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        messages = [
            {
                "role": "system",
                "content": "you are a helpful AI assistant",
            },
        ]
        # add history
        for entry in user_history.get("messages", []):
            messages.append({
                "role": entry["role"],
                "content": entry["content"]
            })
        
        # add retrieved information
        if content_list:
            knowledge_text = "\n\n".join(content_list)
            messages.append({
                "role": "user",
                "content": f"Here is some background information for your reference:\n{knowledge_text}"
            })

        # add question
        messages.append({
            "role": "user",
            "content": f"Based on the history and retrieved information above, strictly use the same language to answer the question: {user_question}",
        },)

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
        temperature: float,
        top_p: float,
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
