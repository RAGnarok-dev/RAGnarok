import json
import re
from typing import Any, Dict, Optional, Tuple

from openai import AsyncOpenAI
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)


def clean_up_json_from_oai(text: str) -> str:
    # https://community.openai.com/t/gpt-4-1106-preview-messes-up-function-call-parameters-encoding/478500/4
    text = re.sub("```json\n?|```", "", text)
    # # Add missing quotation marks around keys
    return re.sub(r"([{,]\s*)(\w+)(\s*:)", r'\1"\2"\3', text)


def load_json_from_oai(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(clean_up_json_from_oai(text))


class KeywordExtractComponent(RagnarokComponent):
    DESCRIPTION: str = "Extract keywords from user query"
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="query",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="size",
                allowed_types={ComponentIOType.INT},
                required=False,
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
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (
            ComponentOutputTypeOption(
                name="keywords",
                type=ComponentIOType.STRING_LIST,
            ),
        )

    @classmethod
    async def execute(
        cls, api_key: str, base_url: str, model_name: str, query: str, size: Optional[int] = 5
    ) -> Dict[str, Any]:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        messages = [
            {
                "role": "system",
                "content": f"Extract {size} keywords from the following query. "
                f"Return them as a comma-separated string.",
            },
            {"role": "user", "content": query},
        ]
        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "keyword_extract",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "keywords": {
                                "type": "array",
                                "items": {"type": "string", "description": "Keywords to extract."},
                                "minItems": size,
                                "maxItems": size,
                            }
                        },
                        "required": ["keywords"],
                    },
                },
            },
        )
        keywords_str = response.choices[0].message.content
        keywords_json = load_json_from_oai(keywords_str)
        return {"keywords": keywords_json["keywords"]}
