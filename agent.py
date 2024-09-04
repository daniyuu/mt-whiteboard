import asyncio
import json
import os
from typing import List, Dict

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


def get_related_questions(chat_history_text: str) -> List[Dict]:
    prompt = """Based on the provided chat history, generate a list of the most relevant questions to gather necessary information from the user that will directly enhance the quality of the agent’s future responses and services, avoiding questions that repeat information already known from the chat history. Focus on identifying gaps in understanding, clarifying user preferences, or obtaining specific details that will enable the agent to provide more personalized and effective assistance. The questions should be formatted as a JSON object suitable for front-end rendering, and the language of the questions should match the main language used in the chat history. Only output the JSON object with the questions.
        
Chat History:
{0}

""".format(
        chat_history_text
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


def get_related_insights(chat_history_text: str) -> List[Dict]:
    prompt = """Based on the provided chat history, generate a mix of high-quality insights and actionable suggestions that reflect different perspectives and directions. The insights should be thought-provoking, concise, and unique, while the suggestions should be practical, specific, and directly applicable. Avoid redundancy, irrelevant information, and focus on providing value. The language of the insights and suggestions should match the language of the chat history. Please output the insights and suggestions in a JSON format, where each item is a separate entry in the list. The response should only include the JSON output, and the language of the insights and suggestions should be the same as the chat history.
    
Chat History:
{0}

""".format(
        chat_history_text
    )

    prompt = (
        prompt
        + """
Output Format (JSON):
[
"insight1",
"suggestion1",
"insight2",
"suggestion2",
...
]

"""
    )

    chatgpt_agent = ChatGPTAgent()
    answers_text = chatgpt_agent.chat([{"sender": "user", "content": prompt}])
    answers_text = answers_text.replace("```json\n", "").replace("```", "")
    answers = json.loads(answers_text)

    return answers


def get_answer(chat_history_text: str) -> str:
    prompt = """Based on the provided chat history, infer the user's intent and purpose behind the conversation. Determine the most likely desired output or result that the user is seeking, such as a travel plan for travel-related discussions or an analysis report for product analysis conversations. Use the inferred intent to produce the specific high-quality output that best meets the user's needs and goals. The language of the output should match the language of the chat history. The response should directly address the inferred user intent with a complete and relevant output.

Chat History:
{history}

Output:
[Insert the inferred output here based on the user's intent]
""".format(
        history=chat_history_text
    )

    chatgpt_agent = ChatGPTAgent()
    answer = chatgpt_agent.chat([{"sender": "user", "content": prompt}])
    return answer


async def get_answer_steaming(chat_history_text: str, response) -> str:
    prompt = """Based on the provided chat history, infer the user's intent and purpose behind the conversation. Determine the most likely desired output or result that the user is seeking, such as a travel plan for travel-related discussions or an analysis report for product analysis conversations. Use the inferred intent to produce the specific high-quality output that best meets the user's needs and goals. The language of the output should match the language of the chat history. The response should directly address the inferred user intent with a complete and relevant output.

Chat History:
{history}

Output:
[Insert the inferred output here based on the user's intent]
""".format(
        history=chat_history_text
    )

    chatgpt_agent = ChatGPTAgent()

    async for chunk in chatgpt_agent.chat_streaming(
        [{"sender": "user", "content": prompt}]
    ):
        await response.send(chunk)

    await response.eof()


async def try_related_insights():
    from data_helper import WhiteboardData

    whiteboard_id = WhiteboardData("aeSo4yq9ERU9pKGdX3cGEb")
    chat_history_text = await whiteboard_id.load_as_chat_history_text()

    result = get_related_insights(chat_history_text)
    print(result)


async def try_related_questions():
    from data_helper import WhiteboardData

    whiteboard_id = WhiteboardData("aeSo4yq9ERU9pKGdX3cGEb")
    chat_history_text = await whiteboard_id.load_as_chat_history_text()

    result = get_related_questions(chat_history_text)
    print(result)


async def try_get_answer():
    from data_helper import WhiteboardData

    whiteboard_id = WhiteboardData("aeSo4yq9ERU9pKGdX3cGEb")
    chat_history_text = await whiteboard_id.load_as_chat_history_text()

    result = get_answer(chat_history_text)
    print(result)


def try_search():
    # DOC: https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
    import os
    from pprint import pprint
    import requests

    # Add your Bing Search V7 subscription key and endpoint to your environment variables.
    subscription_key = os.environ["BING_SEARCH_V7_SUBSCRIPTION_KEY"]
    endpoint = os.environ["BING_SEARCH_V7_ENDPOINT"] + "v7.0/search"

    # Query term(s) to search for.
    query = "最近十天的天气"

    # Construct a request
    mkt = "en-US"
    params = {"q": query, "mkt": mkt}
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}

    # Call the API
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()

        print("Headers:")
        print(response.headers)

        print("JSON Response:")
        pprint(response.json())
    except Exception as ex:
        raise ex


if __name__ == "__main__":
    #     chat_history_text = """user: 我想要去旅游
    # bot: 你想去哪里？
    # user: 云南"""
    #     target_language = None
    #     result = get_related_insights(chat_history_text, target_language)
    #     print(result)
    #     assert result != ""

    #     chat_history_text = """user: 我想要去旅游
    # bot: 你想去哪里？
    # user: 云南"""
    #     target_language = None
    #     result = get_related_questions(chat_history_text, target_language)
    #     print(result)
    #     assert result != ""

    #     chat_history = [
    #         {"content": "我想要去旅游", "sender": "user", "timestamp": "2022-01-01"},
    #         {"content": "你想去哪里？", "sender": "bot", "timestamp": "2022-01-01"},
    #         {"content": "云南", "sender": "user", "timestamp": "2022-01-01"},
    #     ]
    #     target_language = None
    #     result = get_answer(chat_history, target_language)
    #     print(result)
    #     assert result != ""

    # try_search()
    # run async test_related_insights

    loop = asyncio.get_event_loop()
    loop.run_until_complete(try_get_answer())
    loop.close()
