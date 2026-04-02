import os

from openai import OpenAI

MODEL = "openai/gpt-oss-120b"

ACTIONS_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "kanban_response",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Text response to the user",
                },
                "actions": {
                    "type": "array",
                    "description": "List of board operations to perform",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["create_card", "update_card", "delete_card", "move_card"],
                            },
                            "column_id": {
                                "type": ["integer", "null"],
                                "description": "Column DB id (for create_card, move_card target)",
                            },
                            "card_id": {
                                "type": ["integer", "null"],
                                "description": "Card DB id (for update/delete/move)",
                            },
                            "title": {
                                "type": ["string", "null"],
                                "description": "Card title (for create/update)",
                            },
                            "details": {
                                "type": ["string", "null"],
                                "description": "Card details (for create/update)",
                            },
                            "position": {
                                "type": ["integer", "null"],
                                "description": "Target position in column (for move_card)",
                            },
                        },
                        "required": ["type", "column_id", "card_id", "title", "details", "position"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["message", "actions"],
            "additionalProperties": False,
        },
    },
}


def get_ai_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
