import json

import aiofiles


class WhiteboardData:
    def __init__(self, whiteboard_id: str):
        self.whiteboard_id = whiteboard_id
        self.path = f"whiteboard_data/{whiteboard_id}.json"

    @classmethod
    async def create(cls, whiteboard_id: str):
        data = {"graph": {"nodes": [], "edges": []}}
        whiteboard_data = cls(whiteboard_id)
        await whiteboard_data.update(data)
        return whiteboard_data

    async def load(self) -> dict:
        async with aiofiles.open(self.path, "r", encoding="utf-8") as f:
            return json.loads(await f.read())

    async def update(self, data):
        async with aiofiles.open(self.path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, indent=4, ensure_ascii=False))

    async def delete(self):
        import os

        os.remove(self.path)

    async def load_as_chat_history(self):
        data = await self.load()
        nodes = data["graph"]["nodes"]

        chat_history = []
        for node in nodes:
            if node["type"] == "text":
                content = node["content"]
                if isinstance(content, dict):
                    question = content.get("question")
                    if question:
                        chat_history.append(
                            {
                                "content": question,
                                "sender": "bot",
                                "timestamp": node["updated_at"],
                            }
                        )
                    answer = content.get("answer")
                    if answer:
                        chat_history.append(
                            {
                                "content": answer,
                                "sender": "user",
                                "timestamp": node["updated_at"],
                            }
                        )
                else:
                    chat_history.append(
                        {
                            "content": node["content"],
                            "sender": node["created_by"],
                            "timestamp": node["updated_at"],
                        }
                    )

        return chat_history
