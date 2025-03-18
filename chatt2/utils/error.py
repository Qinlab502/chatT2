from typing import Literal


class ExecutorError(Exception):
    def __init__(
        self, error_content, status=Literal["preprocess", "midprocess", "postprocess"]
    ):
        super().__init__(error_content)
        self.error_content = error_content
        self.status = status

    def __str__(self):
        return f"A problem occurred during the {self.status} stage of the executor. The error message is: {self.error_content}."
