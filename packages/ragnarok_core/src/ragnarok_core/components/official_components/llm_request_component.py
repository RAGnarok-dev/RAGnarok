import ast
import asyncio
import json
from typing import Any, Dict, List, Optional, Tuple

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
                name="creator_id",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="llm_session_id",
                allowed_types={ComponentIOType.INT},
                required=False,
            ),
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
        """the options of all the output value"""
        return (
            ComponentOutputTypeOption(name="out", type=ComponentIOType.STRING),
            ComponentOutputTypeOption(name="llm_session_id", type=ComponentIOType.INT),
        )

    @classmethod
    def register_sessions_repo(cls, repo):
        cls.llm_sessions_repo = repo

    @classmethod
    def register_session_cls(cls, session_class):
        cls.LLMSession = session_class

    @classmethod
    async def execute(
        cls,
        creator_id: str,
        llm_session_id: Optional[int],
        user_question: str,
        content_list: List[str],
        model_name: str,
        api_key: str,
        base_url: str,
        max_retries: Optional[int],
        temperature: float,
        top_p: float,
    ) -> Dict[str, Any]:
        """
        execute the async component function
        """
        llm_session_id = int(llm_session_id)
        if isinstance(content_list, str):
            content_list = ast.literal_eval(content_list)
        max_retries = int(max_retries)
        temperature = float(temperature)
        top_p = float(top_p)
        if llm_session_id is None:
            llm_session = cls.LLMSession(
                title="untitled session",
                created_by=creator_id,
                history={"messages": []},
            )
            llm_session = await cls.llm_sessions_repo.create_session(llm_session)
            llm_session_id = llm_session.id
        else:
            llm_session = await cls.llm_sessions_repo.get_session_by_id(llm_session_id)

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        old_messages = llm_session.history["messages"]
        new_messages = []

        if len(old_messages) == 0:
            new_messages.append(
                {
                    "role": "system",
                    "content": "you are a helpful AI assistant",
                }
            )
        # add retrieved information
        if content_list:
            knowledge_text = "\n\n".join(content_list)
            new_messages.append(
                {
                    "role": "user",
                    "content": f"Here is some background information for your reference:\n{knowledge_text}",
                }
            )
        # add question
        new_messages.append(
            {
                "role": "user",
                "content": f"Based on the history and retrieved information above, \
                strictly use the same language to answer the question: {user_question}",
            },
        )

        messages = old_messages
        messages.extend(new_messages)

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
                retries += 1
                if retries == max_retries:
                    response_json = {"answer": f"Error: {e}. Max retries exceeded!"}
                    break
                await asyncio.sleep(1)

        answer = response_json.get("answer")
        new_messages.append(
            {
                "role": "system",
                "content": answer,
            }
        )
        await cls.llm_sessions_repo.update_dialog_history(llm_session_id, {"messages": new_messages})
        return {"out": answer, "llm_session_id": llm_session_id}
