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
        """这里是一个函数注释的示例Return the agent who sent the last message to group chat manager.

        In a group chat, an agent will always send a message to the group chat manager, and the group chat manager will
        send the message to all other agents in the group chat. So, when an agent receives a message, it will always be
        from the group chat manager. With this property, the agent receiving the message can know who actually sent the
        message.

        Example:
        ```python
        from autogen import ConversableAgent
        from autogen import GroupChat, GroupChatManager


        def print_messages(recipient, messages, sender, config):
            # Print the message immediately
            print(
                f"Sender: {sender.name} | Recipient: {recipient.name} | Message: {messages[-1].get('content')}"
            )
            print(f"Real Sender: {sender.last_speaker.name}")
            assert sender.last_speaker.name in messages[-1].get("content")
            return False, None  # Required to ensure the agent communication flow continues


        agent_a = ConversableAgent("agent A", default_auto_reply="I'm agent A.")
        agent_b = ConversableAgent("agent B", default_auto_reply="I'm agent B.")
        agent_c = ConversableAgent("agent C", default_auto_reply="I'm agent C.")
        for agent in [agent_a, agent_b, agent_c]:
            agent.register_reply(
                [ConversableAgent, None], reply_func=print_messages, config=None
            )
        group_chat = GroupChat(
            [agent_a, agent_b, agent_c],
            messages=[],
            max_round=6,
            speaker_selection_method="random",
            allow_repeat_speaker=True,
        )
        chat_manager = GroupChatManager(group_chat)
        groupchat_result = agent_a.initiate_chat(
            chat_manager, message="Hi, there, I'm agent A."
        )
        ```
        """
        mentor, evaluator, executor = self.initial_agents(initial_question, evaluator_exist, cot_mode)

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
                        yield ("mentor: ", mentor.summary())
                        break

                    question = mentor.generate_next_question(error_content=error_content)
                    print(f"{i} turn question: ", question)

                    try:
                        executor_response = executor.executing(question)
                    except ExecutorError as e:
                        error_content = str(e)
                        continue
                    except Exception as e:
                        raise

                    # print(executor_response)
                    yield ("executor: ", executor_response)

                except KeyboardInterrupt:
                    demand = input("有什么额外的需求吗?\n")  # 这里是一个延迟处理的接口，是当执行完一次循环时才获得用户输入，考虑如何实现
                    # 这里可能要插入mentor处理一下用户是要发起另一个问题的discussion还是在当前discussion插入一些自己的要求
                    mentor.add_user_demand("有什么额外的需求吗?\n", demand)
                    continue

                except Exception as e:  # 这里用于处理意料之外的异常
                    raise
                    # evaluator.report(error=e)
