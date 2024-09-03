import os
from typing import List, Dict
import json
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser

from message import Message, Sender


class ChatGPTAgent:
    def __init__(self):
        self.model = AzureChatOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
            openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        )

    def invoke(self, messages: List[Message] = None) -> Message:
        if messages is None:
            messages = []
        _messages = [
            (
                HumanMessage(content=msg.content)
                if msg.sender == Sender.HUMAN
                else AIMessage(content=msg.content)
            )
            for msg in messages
        ]
        parser = StrOutputParser()
        result = parser.invoke(self.model.invoke(_messages))
        result_message = Message(content=result, sender=Sender.CHATGPT)

        return result_message

    def chat(self, messages: List[Dict]):
        messages = [
            Message(content=msg["content"], sender=msg["sender"]) for msg in messages
        ]
        reply = self.invoke(messages)
        return reply.content

    async def chat_streaming(self, messages: List[Dict]):
        if messages is None:
            messages = []
        else:
            messages = [
                Message(content=msg["content"], sender=Sender.HUMAN) for msg in messages
            ]

        _messages = [
            (
                HumanMessage(content=msg.content)
                if msg.sender == Sender.HUMAN
                else AIMessage(content=msg.content)
            )
            for msg in messages
        ]
        async for chunk in self.model.astream(_messages):
            yield chunk.content


def get_related_questions(
    chat_history_text: str, target_language: str = None
) -> List[Dict]:
    if target_language is None:
        target_language = "chat history main language"

    prompt = """Based on the provided chat history, generate a list of the most relevant questions to gather necessary information from the user, don't ask repeat questions. The questions should be formatted as a JSON object suitable for front-end rendering, and the language of the questions should be specified. Only output the JSON object with the questions.

Chat History:
{0}

Language: {1}
""".format(
        chat_history_text, target_language
    )

    prompt = (
        prompt
        + """
Output Format (JSON):
[
    {
        "question": "Question 1",
        "type": "text/multiple-choice/etc.",
        "options": ["Option 1", "Option 2"] // if applicable
    },
    {
        "question": "Question 2",
        "type": "text/multiple-choice/etc.",
        "options": ["Option 1", "Option 2"] // if applicable
    }

]

"""
    )

    chatgpt_agent = ChatGPTAgent()
    questions_text = chatgpt_agent.chat([{"sender": "user", "content": prompt}])
    questions_text = questions_text.replace("```json\n", "").replace("```", "")
    questions = json.loads(questions_text)

    return questions


def get_related_insights(
    chat_history_text: str, target_language: str = None
) -> List[Dict]:
    # if target_language is None:
    #     target_language = "chat history main language"

    target_language = "chat history main language"
    prompt = """Based on the provided chat history, generate several insights that reflect different perspectives and directions. The insights should be thought-provoking and aim to inspire the user's thinking. Please output the insights in a JSON format, where each insight is a separate item in the list. The response should only include the JSON output, and the language of the questions should be specified.

Chat History:
{0}

Language: {1}
""".format(
        chat_history_text, target_language
    )

    prompt = (
        prompt
        + """
Output Format (JSON):
[
"insight1",
"insight2",
"insight3"
]

"""
    )

    chatgpt_agent = ChatGPTAgent()
    answers_text = chatgpt_agent.chat([{"sender": "user", "content": prompt}])
    answers_text = answers_text.replace("```json\n", "").replace("```", "")
    answers = json.loads(answers_text)

    return answers


def get_answer(chat_history: List[Dict], target_language: str = None) -> str:
    if target_language is None:
        target_language = "chat history main language"

    chatgpt_agent = ChatGPTAgent()
    answer = chatgpt_agent.chat(chat_history)
    return answer


if __name__ == "__main__":
    chat_history_text = """user: 我想要去旅游
bot: 你想去哪里？
user: 云南"""
    target_language = None
    result = get_related_insights(chat_history_text, target_language)
    print(result)
    assert result != ""

    chat_history_text = """user: 我想要去旅游
bot: 你想去哪里？
user: 云南"""
    target_language = None
    result = get_related_questions(chat_history_text, target_language)
    print(result)
    assert result != ""

    chat_history = [
        {"content": "我想要去旅游", "sender": "user", "timestamp": "2022-01-01"},
        {"content": "你想去哪里？", "sender": "bot", "timestamp": "2022-01-01"},
        {"content": "云南", "sender": "user", "timestamp": "2022-01-01"},
    ]
    target_language = None
    result = get_answer(chat_history, target_language)
    print(result)
    assert result != ""
