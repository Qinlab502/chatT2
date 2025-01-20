from ..utils import (
    dict_to_markdown_table,
    get_text_completion,
    get_text_completion_with_stream,
    get_text_completion_with_tools,
)
from typing import Literal
import time


class BaseAgent:
    global_message_count = 0
    global_conversation = []
    """
        {"message_speaker":"user", "message_content": "...", "message_order":"..."}
    """

    def add_global_conversation(self, role, content):
        self.global_conversation.append({"message_speaker": role, "message_content": content, "message_order": self.global_message_count})
        self.global_message_count += 1

    def output_from_llm(
        self,
        messages,
        temperature=0.7,
        response_format: Literal["text", "json_object"] = "text",
    ):
        return get_text_completion(messages=messages, temperature=temperature, response_format=response_format)

    def input_from_user(self, prompt_for_user):
        user_input = input(prompt_for_user)
        self.add_global_conversation(role="user", content=user_input)
        return user_input
