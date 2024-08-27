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
            Message(content=msg["content"], sender=Sender.HUMAN) for msg in messages
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

    prompt = """Based on the provided chat history, generate a list of the most relevant questions to gather necessary information from the user. The questions should be formatted as a JSON object suitable for front-end rendering, and the language of the questions should be specified. Only output the JSON object with the questions.

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
    questions_text = chatgpt_agent.chat([{"role": "user", "content": prompt}])
    questions_text = questions_text.replace("```json\n", "").replace("```", "")
    questions = json.loads(questions_text)

    return questions


if __name__ == "__main__":
    chat_history_text = """user: 我想要去旅游
bot: 你想去哪里？
user: 云南"""
    target_language = None
    result = get_related_questions(chat_history_text, target_language)
    assert result != ""
