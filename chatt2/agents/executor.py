from ..utils import (
    dict_to_markdown_table,
    get_text_completion,
    get_text_completion_with_stream,
    get_text_completion_with_tools,
    ExecutorError,
)
from .mentor import Mentor
from ..knowledge_source.retrieval import retrieval_for_context
import json
from .base_agent import BaseAgent


class Executor(BaseAgent):
    def __init__(self):
        self.name = "executor"
        self.question = ""

    def speak(self, content):
        self.add_global_conversation(self.name, content)

    def initial_group(self, evaluator, mentor: Mentor):
        self.mentor = mentor
        self.evaluator = evaluator

    def executing(self, question):
        self.question = question

        if self.evaluator:
            try:
                self.evaluator.preprocess(question)
            except ExecutorError as e:
                raise

        self.mentor.add_message_to_executor("user", question)

        context = self.retrieval(question)
        self.speak(context)

        if self.evaluator:
            try:
                self.evaluator.midprocess(question)
            except ExecutorError as e:
                raise

        response = self.generation_with_context_no_stream(context, question)
        try:
            text_answer = json.loads(response)["text_answer"]
            reference = json.loads(response)["reference"]
            answer = text_answer + "\n\n" + "References:" + "\n\n" + reference
        except KeyError:
            answer = response
        except json.JSONDecodeError:
            answer = response

        if self.evaluator:
            try:
                self.speak(answer)
                self.evaluator.postprocess(content=(question, answer, context))
            except ExecutorError as e:
                response = self.generation_with_context_no_stream(
                    context, question, guidance=str(e)
                )
                try:
                    text_answer = json.loads(response)["text_answer"]
                    reference = json.loads(response)["reference"]
                    answer = text_answer + "\n\n" + "References:" + "\n\n" + reference
                except KeyError:
                    answer = response
                except json.JSONDecodeError:
                    answer = response

        self.speak(answer)
        self.mentor.add_message_to_executor("assistant", answer)
        return answer

    def retrieval(self, question):
        return retrieval_for_context(question)

    def generation_with_context_no_stream(self, context, question, guidance=""):
        qa_prompt1 = "You play a role as a biological natural product agent that respond to users. If the user's query is related to natural products such as Type II polyketides, you should provide the answer in as much detail and with as much professional depth as possible, based on the knowledge provided below."

        qa_prompt2 = (
            "The knowledge you record is: "
            + context
            + "Please list the reference source of the question's relevant information at the end of the answer, including articles' citation.  Add reference numbers with IEEE format, like '[1]', to each sentence according to reference list"
            'for example: \n"This model utilizes multiple classifiers to translate protein sequences into T2PK product classes, allowing for the identification of potential new compounds beyond established groups[1]. \nReference:\n1.A deep learning model for type II polyketide natural product prediction without sequence alignment" \n'
            'Please output in json format, include fields "text_answer" and "reference", for example "{"text_answer":"...","reference":"1.reference1\n2.reference2..." (markdown format)}'
            f"This is the guidance from evaluator: {guidance}"
        )

        messages = [
            {"role": "system", "content": qa_prompt1},
            {"role": "system", "content": qa_prompt2},
            {"role": "user", "content": question},
        ]

        response = get_text_completion(messages, response_format="json_object")
        return response
