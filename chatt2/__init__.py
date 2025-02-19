import traceback
from typing import Literal
from time import sleep

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
        elif stop_criterion == "convergence":  # 先不管他
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

    def discussion(
        self,
        initial_question,
        max_iterations=20,
        stop_criterion=Literal["auto", "manual", "convergence"],
        evaluator_exist=True,
        cot_mode=Literal["disable", "fixed", "updated", "auto"],
    ):
        """
        Return the agents' responds iteratively.
        """
        mentor, evaluator, executor = self.initial_agents(
            initial_question, evaluator_exist, cot_mode
        )

        if cot_mode == "disable":
            max_iterations = 1

        initial_response_from_mentor = mentor.daily_chat()
        error_content = None

        if initial_response_from_mentor:
            yield initial_response_from_mentor
        else:
            for i in range(max_iterations):
                try:
                    if self.termination(
                        mentor=mentor,
                        stop_criterion=stop_criterion,
                    ):
                        yield {"mentor_summary", mentor.summary()}
                        break

                    question = mentor.generate_next_question(
                        error_content=error_content
                    )
                    yield {"mentor": question}

                    try:
                        executor_response = executor.executing(question)
                    except ExecutorError as e:
                        error_content = str(e)
                        continue
                    except Exception as e:
                        raise

                    # print(executor_response)
                    yield {"executor": executor_response}

                except KeyboardInterrupt:
                    demand = input(
                        "有什么额外的需求吗?\n"
                    )  # 这里是一个延迟处理的接口，是当执行完一次循环时才获得用户输入，考虑如何实现
                    # 这里可能要插入mentor处理一下用户是要发起另一个问题的discussion还是在当前discussion插入一些自己的要求
                    mentor.add_user_demand("有什么额外的需求吗?\n", demand)
                    continue

                except Exception as e:  # 这里用于处理意料之外的异常
                    raise
                    # evaluator.report(error=e)
