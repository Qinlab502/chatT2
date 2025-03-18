from typing import Literal

# try:
#     from langfuse.openai import OpenAI
# except ImportError:
#     from openai import OpenAI
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)
model = "gpt-4o-mini"


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


def get_text_completion_with_stream(
    messages, temperature=0.7, response_format: Literal["text", "json_object"] = "text"
):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        response_format={"type": response_format},
        stream=True,
    )
    return response


def get_embedding(text, model="text-embedding-3-small"):
    return client.embeddings.create(input=[text], model=model).data[0].embedding


def get_embeddings(texts: list, model="text-embedding-3-small"):
    response = client.embeddings.create(input=texts, model=model)
    embeddings = [item.embedding for item in response.data]
    return embeddings
