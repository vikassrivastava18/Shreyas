from dotenv import load_dotenv

from typing import Literal
from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from langgraph.graph import StateGraph, END, MessagesState
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt

from config import llm2 as llm, llm_nano
from utils.agent.schemas import DialogueState, QuizSchema

load_dotenv(override=True)
checkpointer = InMemorySaver()


class IntentSchema(BaseModel):
    intent: Literal["hint", "clear"]


class Graph:
    @staticmethod
    def set_topic_index(state: DialogueState) -> DialogueState:
        state["index"] += 1
        return state

    @staticmethod
    def remaining(state: DialogueState) -> Literal["remaining", "complete"]:
        next_index = state["index"]

        if next_index >= len(state["dialogues"]):
            return "complete"
        return "remaining"

    @staticmethod
    def concept_summary(state: DialogueState) -> DialogueState:
        """LLM should prepare a friendly summary on the topic."""

        context = "\n".join([topic["notes"] for topic in state["dialogues"]])
        concept_prompt = f"""
        Prepare a summary on the topic. Use notes for preparing summary and
        context information as overall context while preparing the conceptual summary.
        Wrap the output in HTML tags like <p>, <i>, but do not introduce unnecessary header tags like
        <header>, <html>, <body>.
    
        Topic: {state["dialogues"][state["index"]]["topic"]}
        Notes: {state["dialogues"][state["index"]]["notes"]}
        Context: {context}
    
        End the output with something like "<p><b>Do you have any doubts?</b></p>".
        Output Sample (Follow format strictly!!): 
            <b>Topic</b>  <p>How to get rich in 100 days?</p> <p>There are many ways, best
            path is to work hard....</p>
        """
        summary = llm.invoke(concept_prompt).content

        state["dialogues"][state["index"]]["messages"].append(
            AIMessage(content=summary)
        )
        return state

    @staticmethod
    def get_user_reply(state: DialogueState) -> DialogueState:
        summary = state["dialogues"][state["index"]]["messages"][-1].content
        user_reply = interrupt(f"{summary}")
        state["dialogues"][state["index"]]["messages"].append(
            HumanMessage(content=user_reply)
        )
        return state

    @staticmethod
    def reply_intent(state: DialogueState) -> Literal["hint", "clear"]:

        user_reply = state["dialogues"][state["index"]]["messages"][-1].content

        intent_prompt = f"""
        Look at the user's latest reply and determine the intent.
    
        Return:
        - "hint" -> if the user is confused or wants more clarity
        - "clear" -> if the user understands the concept. For a reply like "No", "Nopes" or similar, takes it that 
        the user is clear on the topic
    
        User Reply:
        {user_reply}
        """
        structured_llm = llm_nano.with_structured_output(IntentSchema)
        response = structured_llm.invoke(intent_prompt)
        state["dialogues"][state["index"]]["state"] = response.intent
        return response.intent

    @staticmethod
    def clarify_doubt(state: DialogueState) -> DialogueState:
        clarify_prompt = f"""Look at the past converstaion on a topic and latest user's reply to clarify user's doubts.
        Output format:  <p>There are many ways, best
        path is to work hard....</p>
        """
        system_message = AIMessage(content=clarify_prompt)
        messages = [system_message] + state["dialogues"][state["index"]]["messages"]

        response = llm.invoke(messages).content
        state["dialogues"][state["index"]]["messages"].append(
            AIMessage(content=response)
        )

        return state

    @staticmethod
    def prepare_quiz(state: DialogueState) -> DialogueState:

        content = state["dialogues"][state["index"]]["notes"]
        prompt = f"""
        You are a quiz master. Use the content of a topic to create questions (MCQ's and True/False) and expected answers 
        that help students in their study.
        Return the response in the format specified.    
        
        Content: {content}
        """

        structured_llm = llm.with_structured_output(QuizSchema)
        messages = [SystemMessage(content=prompt)]

        quizzes = structured_llm.invoke(messages)
        state["dialogues"][state["index"]]["quizzes"] = quizzes

        return state

    @staticmethod
    def quiz_response(state: DialogueState) -> DialogueState:
        quizzes = state["dialogues"][state["index"]]["quizzes"]
        user_reply = interrupt(f"{quizzes}")
        return state

    @staticmethod
    def build_graph():
        builder = StateGraph(DialogueState)

        builder.add_node("set_topic_index", Graph.set_topic_index)
        builder.add_node("concept_summary", Graph.concept_summary)
        builder.add_node("get_user_reply", Graph.get_user_reply)
        builder.add_node("clarify_doubt", Graph.clarify_doubt)
        builder.add_node("prepare_quiz", Graph.prepare_quiz)
        builder.add_node("quiz_response", Graph.quiz_response)

        builder.set_entry_point("set_topic_index")
        builder.add_conditional_edges(
            "set_topic_index",
            Graph.remaining,
            {"remaining": "concept_summary", "complete": END},
        )
        builder.add_edge("concept_summary", "get_user_reply")
        builder.add_conditional_edges(
            "get_user_reply",
            Graph.reply_intent,
            {"hint": "clarify_doubt", "clear": "prepare_quiz"},
        )
        builder.add_edge("clarify_doubt", "get_user_reply")
        builder.add_edge("prepare_quiz", "quiz_response")
        builder.add_edge("quiz_response", "set_topic_index")

        return builder.compile(checkpointer)


class TopicState(MessagesState):
    topic: str
    notes: str
    question: str
    reply: str
    hint_taken: bool


class AnswerState(MessagesState):
    index: int
    max_ind: int
    topic: dict
    topics: list


class EvalSchema(BaseModel):
    evaluation: Literal["satisfactory", "unsatisfactory", "hint"]
    comment: str


class AnswerGraph:

    @staticmethod
    def initialize_graph(state: AnswerState) -> AnswerState:
        print("state", state)
        return state

    @staticmethod
    def set_index(state: AnswerState) -> AnswerState:
        state["index"] += 1
        return state

    @staticmethod
    def check_termination(state: AnswerState) -> Literal["continue", "terminate"]:
        return "terminate" if state["index"] >= state["max_ind"] else "continue"

    @staticmethod
    def set_question(state: AnswerState) -> AnswerState:
        question_topic = state["topics"][state["index"]]
        topic, notes, hint_taken = (
            question_topic["topic"],
            question_topic["notes"],
            False,
        )

        question_prompt = f"""
        You are an examiner whose job is to prepare a conceptual question (subjective) on a topic using the notes provided to you.
        Topic: {topic}
        Notes: {notes}
        Keep the question simple, just to test a basic understanding. Do not provide the answer.
        Output format (Follow format strictly!!): Place the text within markup tags like <p>, highlight keywords with <b> tag, etc.
        """
        question = llm.invoke(question_prompt).content

        state["topic"] = {
            "topic": topic,
            "notes": notes,
            "question": question,
            "hint_taken": hint_taken,
            "reply": "",
            "assessment": "",
            "messages": [],
        }
        return state

    @staticmethod
    def get_student_answer(state: AnswerState) -> AnswerState:
        if state["topic"]["hint_taken"]:
            user_reply = interrupt(f"{state["topic"]["messages"][-1].content}")
        else:
            user_reply = interrupt(f"{state["topic"]["question"]}")
        state["topic"]["reply"] = user_reply
        return state

    @staticmethod
    def evaluate(state: AnswerState,) -> Literal["hint", "satisfactory", "unsatisfactory"]:
        """
        Evaluate the user reply, using LLM.
        Returns correct, retry or limits reached outputs
        """
        if not state["topic"]["hint_taken"]:
            ai_prompt = f"""
                You have to analyze the user's reply to a question to check the understanding of a concept and tell whether
                it is acceptable using notes provided to you. 
                Return: satisfactory or unsatisfactory, along with some comment on the users answer. 
                If not satisfactory, give hint in the comment
                without giving complete answer.
                Keep user as the first person and address the answer to user only.
                Question: {state["topic"]["question"]}
                Notes: {state["topic"]["notes"]}
                User's reply: {state["topic"]["reply"]}
                Output format (Follow format strictly!!): Place the text within markup tags like <p>, highlight keywords with <b> tag, etc.                
            """
        else:
            ai_prompt = f"""
                You have to analyze the user's reply to a question to check the understanding of a concept and tell whether
                it is acceptable using notes provided to you. 
                Return: satisfactory or unsatisfactory, along with some comment on the users answer. 
                If not satisfactory, give answer using notes.
                Keep user as the first person and address the answer to user only.
                Also end the comment with: "<p><b>Continue?<b></p>"
                
                Question: {state["topic"]["question"]}
                Notes: {state["topic"]["notes"]}
                User's reply: {state["topic"]["reply"]}
                Output format (Follow format strictly!!): Place the text within markup tags like <p>, highlight keywords with <b> tag, etc.
            """

        llm_s = llm.with_structured_output(EvalSchema)
        evaluation = llm_s.invoke(ai_prompt)
        state["topic"]["messages"].append(AIMessage(content=evaluation.comment))

        if evaluation.evaluation == "satisfactory":
            return "satisfactory"
        else:
            if not state["topic"]["hint_taken"]:
                return "hint"
            else:
                return "unsatisfactory"

    @staticmethod
    def satisfactory(state: AnswerState) -> AnswerState:
        state["topic"]["assessment"] = "satisfactory"
        user_reply = interrupt(f"{state["topic"]["messages"][-1].content}")
        return state

    @staticmethod
    def hint(state: AnswerState) -> AnswerState:        
        state["topic"]["hint_taken"] = True
        state["topic"]["assessment"] = "hint"
        return state

    @staticmethod
    def unsatisfactory(state: AnswerState) -> AnswerState:
        state["topic"]["assessment"] = "unsatisfactory"
        user_reply = interrupt(f"{state["topic"]["messages"][-1].content}")
        return state

    @staticmethod
    def build_graph():

        builder = StateGraph(AnswerState)

        builder.add_node("initialize_graph", AnswerGraph.initialize_graph)
        builder.add_node("set_index", AnswerGraph.set_index)
        builder.add_node("set_question", AnswerGraph.set_question)
        builder.add_node("get_student_answer", AnswerGraph.get_student_answer)
        builder.add_node("satisfactory", AnswerGraph.satisfactory)
        builder.add_node("hint", AnswerGraph.hint)
        builder.add_node("unsatisfactory", AnswerGraph.unsatisfactory)

        builder.set_entry_point("initialize_graph")

        builder.add_conditional_edges(
            "set_index",
            AnswerGraph.check_termination,
            {
                "terminate": END,
                "continue": "set_question",
            },
        )
        builder.add_conditional_edges(
            "get_student_answer",
            AnswerGraph.evaluate,
            {
                "satisfactory": "satisfactory",
                "unsatisfactory": "unsatisfactory",
                "hint": "hint",
            },
        )
        builder.add_edge("initialize_graph", "set_index")
        builder.add_edge("set_question", "get_student_answer")
        builder.add_edge("satisfactory", "set_index")
        builder.add_edge("unsatisfactory", "set_index")
        builder.add_edge("hint", "get_student_answer")

        return builder.compile(checkpointer)
