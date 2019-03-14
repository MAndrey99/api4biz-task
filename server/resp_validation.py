import jsonschema
from aiohttp.web import json_response


def validated_json_response(data, *, status=200, **kwargs):
    if status == 200:
        schema = {
            "type": "object",

            "properties": {
                "content": {
                    "type": "array",
                    "items": {
                        "type": "object"
                    }
                }
            },

            "additionalProperties": False
        }
    elif status//100 == 2:
        schema = {
            "type": "object",

            "properties": {
                "error": {"type": "string"},
                "content": {
                    "type": "array",
                    "items": {
                        "type": "object"
                    }
                }
            },

            "required": ["error"],
            "additionalProperties": False
        }
    else:
        schema = {
            "type": "object",

            "properties": {
                "error": {"type": "string"}
            },

            "required": ["error"],
            "additionalProperties": False
        }

    jsonschema.validate(data, schema)
    return json_response(data, status=status, **kwargs)

