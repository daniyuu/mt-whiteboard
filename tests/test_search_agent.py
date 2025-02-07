import pytest
from agent import SearchAgent

@pytest.mark.asyncio
async def test_search():
    agent = SearchAgent()
    result = await agent.search("Python programming")
    assert "webPages" in result or "videos" in result

@pytest.mark.asyncio
async def test_search_no_results():
    agent = SearchAgent()
    result = await agent.search("asdkjfhaskjdfhaksjdfh")
    assert "webPages" not in result and "videos" not in result
