import aiohttp
import jsonschema

from typing import Callable


error_schema = {
    "type": "object",

    "properties": {
        "error": {"type": "string"}
    },

    "required": ["error"],
    "additionalProperties": False
}

empty_schema = {
    "type": "object",
    "maxProperties": 0
}

content_schema = {
    "type": "object",

    "properties": {
        "content": {
            "type": "array",
            "items": {
                "type": "object"
            }
        }
    },

    "required": ["content"],
    "additionalProperties": False
}


async def delete_all(session: aiohttp.ClientSession):
    async with session.delete('http://0.0.0.0:8080/') as resp:
        assert resp.status == 200


async def check(method: Callable, src: str, params: dict, expect_status: int, expect_json_schema: dict) -> dict:
    async with method(f'http://0.0.0.0:8080/{src}', params=params) as resp:
        assert resp.status == expect_status

        json: dict = await resp.json()
        jsonschema.validate(json, expect_json_schema)

    return json
