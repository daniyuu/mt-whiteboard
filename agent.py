import asyncio
import json
import os
from pprint import pprint
from typing import List, Dict

import aiohttp
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


class SearchAgent:
    def __init__(self):
        # DOC: https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
        # https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/overview
        # https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/reference/response-objects
        # WebAnser: https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/reference/response-objects#webanswer
        # Entity: https://learn.microsoft.com/en-us/bing/search-apis/bing-entity-search/reference/response-objects#entityanswer
        # Image: https://learn.microsoft.com/en-us/bing/search-apis/bing-entity-search/reference/response-objects#localentityanswer
        # Video: https://learn.microsoft.com/en-us/bing/search-apis/bing-video-search/reference/response-objects#videosanswer

        self.subscription_key = os.environ["BING_SEARCH_V7_SUBSCRIPTION_KEY"]
        self.endpoint = os.environ["BING_SEARCH_V7_ENDPOINT"] + "v7.0/search"

    async def search(self, query: str):
        # Construct a request
        mkt = "en-US"
        params = {"q": query, "mkt": mkt}
        headers = {"Ocp-Apim-Subscription-Key": self.subscription_key}

        # Call the API
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    self.endpoint, headers=headers, params=params
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
            except Exception as ex:
                raise ex

        return result


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


# 和Summary的内容上看是会撞车的
def get_ai_response(chat_history: List) -> str:
    chatgpt_agent = ChatGPTAgent()
    answer = chatgpt_agent.chat(chat_history)
    return answer


def get_search_results_summary(search_results: List[Dict], top_n=5) -> str:
    summary = ""
    for i, result in enumerate(search_results):
        if i >= top_n:
            break
        if result["type"] == "search-webPage":
            summary += f"Title: {result['name']}\n"
            summary += f"URL: {result['url']}\n"
            summary += f"Snippet: {result['snippet']}\n"
        elif result["type"] == "search-video":
            summary += f"Title: {result['name']}\n"
            summary += f"URL: {result['url']}\n"
            summary += f"Description: {result['description']}\n"

    prompt = """Based on the search results provided, generate a suitable response that addresses the user's query. The response should be relevant, concise, and informative, incorporating key points from the retrieved information. Aim to present the most important insights in a clear and accessible manner, and consider the user's potential needs or interests when crafting your reply. The language of the output should match the language of the search results.\n\nSearch Results:\n{0}""".format(
        summary
    )

    chatgpt_agent = ChatGPTAgent()
    summary = chatgpt_agent.chat([{"sender": "user", "content": prompt}])

    return summary


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


def get_search_keywords(chat_history_text: str) -> str:
    prompt = """Based on the provided chat history, infer the user's intent and purpose behind the conversation. While you are unable to access real-time or specific internet information directly, you can assist the user by generating relevant search keywords that can be used to find the necessary information via a search engine. Please output the queies in a JSON format, where each item is a separate entry in the list. The response should only include the JSON output, and the language of the queries should be the same as the chat history

Chat History:
{history}

Output Format (JSON):
[
"query1",
"query2",
"query3"
]

""".format(
        history=chat_history_text
    )

    chatgpt_agent = ChatGPTAgent()
    answers_text = chatgpt_agent.chat([{"sender": "user", "content": prompt}])
    answers_text = answers_text.replace("```json\n", "").replace("```", "")
    answers = json.loads(answers_text)

    return answers


async def get_search_results(chat_history_text: str, limit: int = 5) -> List[Dict]:
    queries = get_search_keywords(chat_history_text)
    search_agent = SearchAgent()
    results = []
    for query in queries:
        r = await search_agent.search(query)
        if "webPages" in r:
            webPages = r["webPages"]["value"]
            for webPage in webPages:
                results.append(
                    {
                        "type": "search-webPage",
                        "name": webPage["name"],
                        "url": webPage["url"],
                        "snippet": webPage["snippet"],
                    }
                )

        if "videos" in r:
            videos = r["videos"]["value"]
            for video in videos:
                results.append(
                    {
                        "type": "search-video",
                        "name": video["name"],
                        "url": video["contentUrl"],
                        "description": video["description"],
                    }
                )

        if len(results) >= limit:
            break

    return results


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


async def try_get_search_keywords():
    from data_helper import WhiteboardData

    whiteboard_id = WhiteboardData("aeSo4yq9ERU9pKGdX3cGEb")
    chat_history_text = await whiteboard_id.load_as_chat_history_text()

    result = get_search_keywords(chat_history_text)
    print(result)


async def try_search_engine():
    search_agent = SearchAgent()
    result = await search_agent.search("苏州未来十天的天气")
    return result


async def try_get_search_results():
    from data_helper import WhiteboardData

    whiteboard_id = WhiteboardData("aeSo4yq9ERU9pKGdX3cGEb")
    chat_history_text = await whiteboard_id.load_as_chat_history_text()

    result = await get_search_results(chat_history_text, limit=5)

    print(result)


async def try_get_search_with_ai_summary():
    from data_helper import WhiteboardData

    whiteboard_id = WhiteboardData("aeSo4yq9ERU9pKGdX3cGEb")
    chat_history_text = await whiteboard_id.load_as_chat_history_text()

    result = await get_search_results(chat_history_text, limit=5)

    summary = get_search_results_summary(result)

    print(summary)


async def try_ai_response():
    from data_helper import WhiteboardData

    whiteboard_id = WhiteboardData("aeSo4yq9ERU9pKGdX3cGEb")
    chat_history = await whiteboard_id.load_as_chat_history()

    result = get_ai_response(chat_history)
    print(result)


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
    loop.run_until_complete(try_get_search_with_ai_summary())
    loop.close()
