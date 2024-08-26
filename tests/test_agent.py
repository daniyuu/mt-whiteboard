import pytest

from agent import ChatGPTAgent


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
