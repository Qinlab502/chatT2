from ..utils import dict_to_markdown_table, get_text_completion, get_text_completion_with_stream, get_text_completion_with_tools, ExecutorError
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
                # 再引发一次给mentor
                raise

        self.mentor.add_message_to_executor("user", question)

        if self.evaluator:
            try:
                self.evaluator.midprocess(question)
            except ExecutorError as e:
                # 再引发一次给mentor
                raise

        context = self.retrieval(question)
        print("retrieval_success")
        response = self.generation_with_context_no_stream(context, question)
        try:
            text_answer = json.loads(response)["text_answer"]
            reference = json.loads(response)["reference"]  # 这里要设计下，用于统计参考文献
            answer = text_answer + "\n\n" + "References:" + "\n\n" + reference
        except json.JSONDecodeError:
            answer = response

        if self.evaluator:
            try:
                self.speak(answer)
                self.evaluator.postprocess(content=(question, answer, context))
            except ExecutorError as e:
                response = self.generation_with_context_no_stream(context, question, guidance=str(e))
                try:
                    text_answer = json.loads(response)["text_answer"]
                    reference = json.loads(response)["reference"]  # 这里要设计下，用于统计参考文献
                    answer = text_answer + "\n\n" + "References:" + "\n\n" + reference
                except json.JSONDecodeError:
                    answer = response

        self.speak(answer)
        self.mentor.add_message_to_executor("assistant", answer)
        return answer

    def retrieval(self, question):
        return retrieval_for_context(question)

    def generation_with_context_no_stream(self, context, question, guidance=""):
        qa_prompt1 = "You play a role as a biological natural product agent that respond to users. If use query is related to natural prodcut like Type II Polyketides, you should professionally tell the answer based on the knowledge provided as follows. Otherwise, you should communicate with user normally."
        # qa_prompt2 = (
        #     "The knowledge you record is: "
        #     + context
        #     + "Please list the reference source of the question's relevant information at the end of the answer. Including articles' citation and mibig_url.  add citation numbers with HTML formatted superscript '<sup>number</sup>' to each sentence according to reference list"
        #     "for example: 'This model utilizes multiple classifiers to translate protein sequences into T2PK product classes, allowing for the identification of potential new compounds beyond established groups<sup>1</sup>. Reference:\n1.A deep learning model for type II polyketide natural product prediction without sequence alignment'"
        #     """Please note that if there is not enough information in the provided knowledge to answer the question, simply output:"{"text_answer":"Sorry, I don't know. You can try to ask me another question.","reference":"no reference"}" to ensure scientific rigor."""
        #     """Please output in json format:"{"text_answer":"..."(markdown format),"reference":"1.reference1\n2.reference2..." (markdown format)}"""
        # )
        qa_prompt2 = (
            "The knowledge you record is: "
            + context
            + "Please list the reference source of the question's relevant information at the end of the answer. Including articles' citation and mibig_url.  add citation numbers with HTML formatted superscript '<sup>number</sup>' to each sentence according to reference list"
            'for example: \n"This model utilizes multiple classifiers to translate protein sequences into T2PK product classes, allowing for the identification of potential new compounds beyond established groups<sup>1</sup>. \nReference:\n1.A deep learning model for type II polyketide natural product prediction without sequence alignment" \n'
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
