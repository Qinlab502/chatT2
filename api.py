import os

os.environ["CONFIG_PATH"] = "config.json"

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from chatt2 import ChatT2, get_text_completion
import json
import time


app = FastAPI()
chatt2 = ChatT2()


chat_history = []  # 存储了对话记录，不包含不同agents的反思过程


@app.post("/ask-stream")
async def ask_question_stream(request: Request):
    body = await request.body()
    data = json.loads(body)
    question = data.get("question")  # 获得用户输出

    # 把问题添加到历史
    chat_history.append({"role": "user", "input": question})

    # 构造上下文作为完整输入
    user_question = build_question_from_history(chat_history)

    def generate_response():
        for response in chatt2.discussion(user_question):
            if response["status"] == "finished":
                chat_history.append({"role": "chatt2", "output": response["content"]})
            yield response["content"] + "\n"
        # 这里做成每个chunk是一个agent输出，但是返回到前端是流式的效果
        # 在下载github仓库使用时候就直接输出

    return StreamingResponse(generate_response(), media_type="text/plain")


def build_question_from_history(history):
    messages = [
        {
            "role": "user",
            "content": f"chatt2 is an intelligent AI assistant. Based on the user's conversation history, please transform the user's latest input into a standalone question. chat_history: {str(history)}",
        },
    ]
    user_question = get_text_completion(messages)  # 检查一下这里会输出什么
    return user_question
