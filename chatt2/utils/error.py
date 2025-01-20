from typing import Literal


class ExecutorError(Exception):
    """自定义错误类型"""

    def __init__(self, error_content, status=Literal["preprocess", "midprocess", "postprocess"]):
        """
        :error_content: 错误信息
        :param code: 错误代码（可选）
        """
        super().__init__(error_content)
        self.error_content = error_content
        self.status = status

    def __str__(self):
        """返回错误的字符串表示形式"""
        return f"一个问题出现在executor的{self.status}阶段，错误信息为：{self.error_content}"
