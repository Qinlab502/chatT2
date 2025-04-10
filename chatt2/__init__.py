import json
import os
from pathlib import Path


root = Path(__file__) / ".."
cwd = Path.cwd()

cache_dir = cwd / "cache"
cache_dir.mkdir(exist_ok=True)  # cache dir is used to store the process of the chatt2
os.environ["cache_dir"] = str(cache_dir)


config_path = os.getenv("CONFIG_PATH")

with open(config_path, "r") as f:
    config = json.load(f)

for key, value in config.items():
    os.environ[key] = str(value)

import traceback
from typing import Literal
import time
from .utils import write_json, get_text_completion
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
        elif stop_criterion == "convergence":  
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

        if cot_mode == "disable":
            max_iterations = 1

        initial_response_from_mentor = mentor.daily_chat()
        error_content = None

        yield {"role": "user", "content": initial_question}

        if initial_response_from_mentor:
            yield {
                "role": "mentor",
                "content": initial_response_from_mentor,
                "status": "finised",
            }
        else:
            for i in range(max_iterations):
                try:
                    if self.termination(
                        mentor=mentor,
                        stop_criterion=stop_criterion,
                    ):
                        summary_answer = mentor.summary()
                        yield {
                            "role": "mentor",
                            "content": summary_answer,
                            "status": "finished",
                        }
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
                    yield {"role": "mentor", "content": question, "status": "thinking"}

                    try:
                        executor_response = executor.executing(question)
                    except ExecutorError as e:
                        error_content = str(e)
                        continue
                    except Exception as e:
                        raise

                    if max_iterations == 1:
                        yield {
                            "role": "executor",
                            "content": executor_response,
                            "status": "finished",
                        }
                    else:
                        yield {
                            "role": "executor",
                            "content": executor_response,
                            "status": "thinking",
                        }

                except KeyboardInterrupt:
                    demand = input("Do you have extra demand?\n")
                    mentor.add_user_demand("Do you have extra demand?\n", demand)
                    continue

                except Exception as e:
                    raise
