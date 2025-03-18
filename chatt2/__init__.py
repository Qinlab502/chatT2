import json
import os
from pathlib import Path


root = Path(__file__) / ".."
cwd = Path.cwd()

cache_dir = cwd / "cache"
cache_dir.mkdir(exist_ok=True)  # cache dir is used to store the process of the chatt2
os.environ["cache_dir"] = str(cache_dir)

# config_path = (root / "../config.json").resolve().relative_to(cwd).as_posix()

config_path = os.getenv("CONFIG_PATH")

with open(config_path, "r") as f:
    config = json.load(f)

for key, value in config.items():
    os.environ[key] = str(
        value
    )  # get the value fiedld in the process: os.getenv("OPENAI_API_KEY")

import traceback
from typing import Literal
import time
from .utils import write_json
from .agents import Evaluator, Executor, Mentor, ExecutorError


class ChatT2:
    def __init__(self):
        pass

    def termination(self, mentor: Mentor, stop_criterion):
        if stop_criterion == "auto":
            return mentor.new_question == "No further questions are needed"
        elif stop_criterion == "manual":
            user_input = input("wheather to stop?")
            return user_input == "yes"
        elif stop_criterion == "convergence":  # 这里应该加一个当最后一次迭代时行进总结
            return False

    def initial_agents(self, initial_question, evaluator_exist, cot_mode):
        mentor = Mentor(initial_question, cot_mode)
        executor = Executor()

        if evaluator_exist:
            evaluator = Evaluator()
            evaluator.initial_group(executor, mentor)

        else:
            evaluator = None

        mentor.initial_group(evaluator, executor)
        executor.initial_group(evaluator, mentor)

        return mentor, evaluator, executor

    def discussion(self, initial_question):
        """
        Return the agents' responds iteratively.
        """

        stop_criterion = os.getenv("STOP_CRITERION")
        max_iterations = int(os.getenv("MAX_ITERATION"))
        evaluator_exist = bool(os.getenv("EVALUATOR_EXIST") == "true")
        cot_mode = os.getenv("COT_MODE")

        mentor, evaluator, executor = self.initial_agents(
            initial_question, evaluator_exist, cot_mode
        )
        print(mentor.cot)
        if cot_mode == "disable":
            max_iterations = int(os.getenv("MAX_ITERATION"))

        initial_response_from_mentor = mentor.daily_chat()
        error_content = None

        yield "user query: " + initial_question

        if initial_response_from_mentor:
            yield initial_response_from_mentor
        else:
            for i in range(max_iterations):
                try:
                    if self.termination(
                        mentor=mentor,
                        stop_criterion=stop_criterion,
                    ):
                        summary_answer = mentor.summary()
                        yield ("mentor: ", summary_answer)
                        if bool(os.getenv("cache")):
                            cache_schema = {
                                "user_question": "",
                                "thought": {},
                                "summary_answer": "",
                            }
                            cache_schema["user_question"] = initial_question
                            cache_schema["thought"] = mentor.global_conversation
                            cache_schema["summary_answer"] = summary_answer
                            write_json(
                                cache_schema,
                                os.getenv("cache_dir")
                                + "/"
                                + time.strftime("%Y%m%d_%H%M%S"),
                            )
                        break

                    question = mentor.generate_next_question(
                        error_content=error_content
                    )
                    yield "mentor question: " + question

                    try:
                        executor_response = executor.executing(question)
                    except ExecutorError as e:
                        error_content = str(e)
                        continue
                    except Exception as e:
                        raise

                    yield "executor response: " + executor_response

                except KeyboardInterrupt:
                    demand = input("Do you have extra demand?\n")
                    mentor.add_user_demand("Do you have extra demand?\n", demand)
                    continue

                except Exception as e:
                    raise
