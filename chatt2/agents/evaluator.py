from ..utils import dict_to_markdown_table, get_text_completion, get_text_completion_with_stream, get_text_completion_with_tools, ExecutorError
from .mentor import Mentor
from .executor import Executor
from ..knowledge_source.retrieval import retrieval_for_context
import json
from .base_agent import BaseAgent
from typing import Literal


class Evaluator(BaseAgent):
    def __init__(self):
        self.name = "evaluator"
        self.unanswerable_question_list = []

    def initial_group(self, mentor, executor):
        self.mentor = mentor
        self.executor = executor

    def speak(self, content):
        self.add_global_conversation(self.name, content)
        return content

    def report(self, error=None, executor_status=None, content=None):
        if executor_status is None:  # 这个先不做，处理用户使用时的异常, error用于传入其它异常
            return self.speak("")

        else:
            if executor_status == "preprocess":
                # for mentor
                # 问题无法回答，让mentor换一个或回馈用户重新提问
                return self.speak("")

            elif executor_status == "midprocess":
                # for mentor
                # 问题缺少相关信息，让mentor换一个或回馈用户重新提问
                return self.speak(f"executor can't find relevant information about this question '{content}' in database, please provide another one")

            elif executor_status == "postprocess":
                # for executor
                # 关于引文生成的异常
                return self.speak("")

    def preprocess(self, content):
        # 由用户反馈的提供了错误回答的问题，磁盘化保存
        executor_status = "preprocess"
        error_content = self.report(executor_status=executor_status, content=content)
        raise ExecutorError(error_content, status=executor_status)

    def midprocess(self, content):
        # 筛选context中的不相关信息
        executor_status = "midprocess"
        error_content = self.report(executor_status=executor_status, content=content)
        raise ExecutorError(error_content, status=executor_status)

    def postprocess(self, content):
        # 检查引用是否正确
        executor_status = "postprocess"
        error_content = self.report(executor_status=executor_status, content=content)
        raise ExecutorError(error_content, status=executor_status)
