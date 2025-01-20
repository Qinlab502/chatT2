from ..utils import (
    dict_to_markdown_table,
    get_text_completion,
    get_text_completion_with_stream,
    get_text_completion_with_tools,
)
from typing import Literal
import json
from .base_agent import BaseAgent


class Mentor(BaseAgent):
    def __init__(self, initial_question, cot_mode=Literal["disable", "fixed", "updated", "auto"]):
        self.name = "mentor"
        self.initial_question = initial_question
        self.messages_to_executor = []  # to form the summary

        self.user_demand = []
        self.new_question = initial_question
        self.cot_mode = cot_mode
        if self.cot_mode != "disable":
            self.cot = self.create_cot()  # 这个用于

    def add_message_to_executor(self, role, content):
        self.messages_to_executor.append({"role": role, "content": content})

    def add_user_demand(self, user_prompt, demand):
        self.user_demand.append((user_prompt, demand))
        self.create_cot()

    def daily_chat(self):
        chat_messages = [
            {
                "role": "system",
                "content": "You play a role as a biological natural product agent that respond to users. If user asks a question, you should output 'I am thinking..'.",
            },
            {"role": "user", "content": f"{self.initial_question}"},
        ]
        _output = get_text_completion(chat_messages)
        if _output == "I am thinking.." or _output == "我在思考..":
            return False
        else:
            return _output

    def messages_to_dialog(self, messages):
        # dialog = f"""{{"initial question": "Which bioinformatics tools would you recommend for predicting type II polyketide biosynthetic pathways?","response":"{response}"}}"""
        dialog = {}
        for index, i in enumerate(messages):
            if i["role"] == "user":
                if index == 0:
                    dialog[f"initial question #{index // 2}"] = i["content"]
                else:
                    dialog[f"follow-up question #{index // 2}"] = i["content"]
            if i["role"] == "assistant":
                dialog[f"response #{index // 2}"] = i["content"]
        return json.dumps(dialog)

    def initial_group(self, evaluator, executor):
        self.evaluator = evaluator
        self.executor = executor

    def speak(self, content):
        self.add_global_conversation(self.name, content)

    def summary(self):
        messages = self.messages_to_executor
        dialog = self.messages_to_dialog(messages)
        summary_messages = [
            {
                "role": "system",
                "content": "Please merge the dialogs to create an scientific search report related to the user's initial question. 每个问题的response中的内容以<sup>标签加数字结尾，意味者这句话参考了'References'中文献，因此你在合并信息时，应该保留相同的文献引用格式. You should incorporate all information from each dialog in the answer",
            },
            {
                "role": "user",
                "content": f"initial_question: {self.initial_question}, dialogs:{dialog}",
            },
        ]
        summary = get_text_completion(summary_messages)
        self.speak(summary)
        return summary

    def create_cot(self):
        messages = self.messages_to_executor
        if len(messages) != 0:
            dialog = self.messages_to_dialog(messages)
            create_cot_messages = [
                {
                    "role": "user",
                    "content": f'对于用户的问题 "{self.initial_question}"已经产生了一些讨论 "{dialog}". 你可以参考这个讨论写一段回答该问题的解决步骤并且 satisfy user demand:{self.user_demand}.',
                },
            ]
        else:
            create_cot_messages = [
                {
                    "role": "user",
                    "content": f'对于用户的问题 "{self.initial_question}". 你需要写一段回答该问题的解决步骤',
                },
            ]
        # print(create_cot_messages)
        response = get_text_completion(create_cot_messages)
        # print(response)
        cot_prompt = response
        # print(cot_prompt)
        self.cot = cot_prompt

    def generate_next_question(self, error_content=None):
        # latest_response_from_executor = self.messages_to_executor[-1]["content"]

        messages = self.messages_to_executor
        dialog = self.messages_to_dialog(messages)
        for i in range(100):
            if error_content:
                # 处理当由evaluator反馈的错误信息时，需要重新提问
                generation_new_question_messages_with_error = [
                    {
                        "role": "user",
                        "content": f'You are now trying to solve the user initial question \'{self.initial_question}.\' \
                            These are the past dialog records between you and assistant agents you can refer: \'{dialog}\'. However, evaluator report the error content:\'{error_content}\', \
                            you can either show what have been done in the dialog and ask user to ask another question (output in JSON format:\'{{"demand_to_user":".."}}\' )\
                            or generate another question (output in JSON format:"{{"follow_question_for_agents":".."}}")',
                    },
                ]
                response = self.output_from_llm(generation_new_question_messages_with_error, response_format="json_object")
                try:
                    demand_to_user = response["demand_to_user"]
                    self.speak(demand_to_user)
                    new_question = self.input_from_user(demand_to_user)
                    return new_question

                except json.JSONDecodeError:
                    follow_question_for_agents = response["follow_question_for_agents"]
                    self.speak(follow_question_for_agents)
                    self.new_question = follow_question_for_agents
                    return follow_question_for_agents

                except Exception as e:
                    raise

            if self.cot_mode == "auto":
                achieve_user_demand_messages = [
                    {
                        "role": "user",
                        "content": f'You are now trying to solve the user initial question {self.initial_question}. \
                            Here are the past dialog records between you and assistant agents you can refer: {dialog}. If you need more background about the initial question, \
                            you can show what have beed done in the dialog and ask user what he want to do in next step or what is the final purpose, output in JSON format:"{{"demand_to_user":".."}}". Otherwise, output "I don\'t need anything" in json value field, like "{{"demand_to_user":"I don\'t need anything"}}" ',
                    },
                ]
                demand_to_user = get_text_completion(
                    achieve_user_demand_messages,
                    temperature=1,
                    response_format="json_object",
                )
                demand = json.loads(demand_to_user)["demand_to_user"]
                if demand == "I don't need anything":
                    pass
                else:
                    self.speak(demand)
                    new_demand = self.input_from_user(demand)
                    self.add_user_demand(demand, new_demand)

            elif self.cot_mode == "updated":
                achieve_user_demand_messages = [
                    {
                        "role": "user",
                        "content": f'You are now trying to solve the user initial question {self.initial_question}. \
                            Here are the past dialog records between you and assistant agents you can refer: {dialog}. \
                            you need to show what have beed done in the dialog and ask user what he want to do in next step or what is the final purpose. Output in JSON format:"{{"demand_to_user":".."}}" ',
                    },
                ]
                demand_to_user = get_text_completion(
                    achieve_user_demand_messages,
                    temperature=1,
                    response_format="json_object",
                )
                demand = json.loads(demand_to_user)["demand_to_user"]
                self.speak(demand)
                new_demand = self.input_from_user(demand)
                self.add_user_demand(demand, new_demand)

            elif self.cot_mode == "disable":
                return self.initial_question

            else:
                # 这里是fix模式, cot不需要进行修改
                pass

            generation_new_question_messages = [
                {
                    "role": "system",
                    "content": f'You need to generate a new question for database assisstant as part of a series of questions to step-by-step \
                        address the users initial_question: "{self.initial_question}". If information in dialog is enough to solve the initial question,\
                        you can output "No further questions are needed". Output in JSON format:"{{"follow_question_for_database":".."}}"',
                },
                {
                    "role": "user",
                    "content": f"You are now acting as an intermediary between a user and a knowledge database. The knowledge database has\
                          already provided a series of answers to the initial question and follow questions. However, you need to raise another questions based on strategy '{self.cot}', \
                            to submit to the knowledge database in order to more comprehensively and exploratively address initial question step-by-step. Here are the past diolog records between you and database assistant: {dialog}. ",
                },
            ]
            new_question = get_text_completion(
                generation_new_question_messages,
                temperature=1,
                response_format="json_object",
            )
            new_question = json.loads(new_question)["follow_question_for_database"]
            self.speak(new_question)
            self.new_question = new_question
            return new_question
