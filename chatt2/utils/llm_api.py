from typing import Literal

# try:
#     from langfuse.openai import OpenAI
# except ImportError:
#     from openai import OpenAI
from openai import OpenAI


client = OpenAI(
    api_key="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"
)
# model = "gpt-4-0125-preview"
model = "gpt-4o-mini"
# model = "gpt-3.5-turbo-0125"


def get_text_completion_with_tools(
    messages,
    temperature=0.7,
    response_format: Literal["text", "json_object"] = "text",
    tools=None,
    tool_choice="auto",
):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        response_format={"type": response_format},
        tools=tools,
        tool_choice=tool_choice,
    )
    return response.choices[0]


def get_text_completion(
    messages,
    temperature=0.7,
    response_format: Literal["text", "json_object"] = "text",
):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        response_format={"type": response_format},
    )
    return response.choices[0].message.content


def get_text_completion_with_stream(messages, temperature=0.7, response_format: Literal["text", "json_object"] = "text"):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        response_format={"type": response_format},
        stream=True,
    )

    # for chunk in response:
    #     if chunk.choices[0].delta.content is not None:
    #         print(chunk.choices[0].delta.content, end="1")

    return response


def get_embedding(text, model="text-embedding-3-small"):
    return client.embeddings.create(input=[text], model=model).data[0].embedding
