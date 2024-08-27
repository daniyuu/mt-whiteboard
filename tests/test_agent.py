import pytest

from agent import ChatGPTAgent, get_related_questions


@pytest.mark.asyncio
async def test_chat():
    messages = [
        {"role": "human", "content": "Hi"},
    ]
    agent = ChatGPTAgent()
    reply = agent.chat(messages)
    assert reply != ""


@pytest.mark.asyncio
async def test_chat_streaming():
    messages = [
        {"role": "human", "content": "Hi"},
    ]
    agent = ChatGPTAgent()
    reply = agent.chat_streaming(messages)
    assert reply != ""


@pytest.mark.asyncio
async def test_get_related_questions():
    chat_history_text = """user: 我想要去旅游
bot: 你想去哪里？
user: 云南"""
    target_language = None
    result = get_related_questions(chat_history_text, target_language)
    assert result != ""
