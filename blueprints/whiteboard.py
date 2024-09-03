import json
from datetime import datetime

import aiofiles
from sanic import Blueprint, response
from sanic.log import logger
from shortuuid import uuid
from sqlalchemy.future import select

from agent import get_related_questions, get_related_insights, get_answer
from models import Whiteboard

bp = Blueprint("whiteboard", url_prefix="/whiteboard")


# sample whiteboard data
# data = {
#     "name": "whiteboard",
#     "ui_attributes": {"avatar": "x0fdsafadsrewreafdsfda"},
#     "data": {
#         "graph": {
#             "nodes": [
#                 {
#                     "id": "uuid_1",
#                     "type": "text",
#                     "content": "Updated Content",
#                     "status": "inactive",
#                     "created_by": "user",
#                     "extra_metadata": {},
#                     "ui_attributes": {
#                         "position": {"x": 100, "y": 100},
#                     },
#                 }
#             ],
#             "edges": [{"extra_metadata": {}, "ui_attributes": {}}],
#         }
#     },
# }


# Create a whiteboard
@bp.route("/create", methods=["POST"])
async def create_whiteboard_handler(request):
    session = request.ctx.session
    wid = request.json.get("id", uuid())
    name = request.json.get("name")
    ui_attributes = request.json.get("ui_attributes", {})
    if not name:
        logger.error("Name is required")
        return response.json({"error": "Name is required"}, status=400)

    async with session.begin():
        whiteboard = Whiteboard(id=wid, name=name, ui_attributes=ui_attributes)
        session.add(whiteboard)

    # create a file to store whiteboard data
    async with aiofiles.open(f"whiteboard_data/{wid}.json", "w") as f:
        await f.write(json.dumps({}))

    return response.json({"id": whiteboard.id})


# Update a whiteboard
@bp.route("/<whiteboard_id:str>/update", methods=["POST"])
async def update_whiteboard_handler(request, whiteboard_id):
    name = request.json.get("name")
    if name is not None:
        async with request.ctx.session.begin():
            whiteboard = await request.ctx.session.get(Whiteboard, whiteboard_id)
            whiteboard.name = name
    ui_attributes = request.json.get("ui_attributes")

    if ui_attributes is not None:
        async with request.ctx.session.begin():
            whiteboard = await request.ctx.session.get(Whiteboard, whiteboard_id)
            whiteboard.ui_attributes = ui_attributes

    data = request.json.get("data")
    if data is not None:
        async with aiofiles.open(f"whiteboard_data/{whiteboard_id}.json", "w") as f:
            await f.write(json.dumps(data, indent=4))

        async with request.ctx.session.begin():
            whiteboard = await request.ctx.session.get(Whiteboard, whiteboard_id)
            whiteboard.updated_at = datetime.now()

    return response.json({"id": whiteboard.id})


# Delete a whiteboard
@bp.route("/<whiteboard_id:str>/delete", methods=["POST"])
async def delete_whiteboard_handler(request, whiteboard_id):
    async with request.ctx.session.begin():
        whiteboard = await request.ctx.session.get(Whiteboard, whiteboard_id)
        await whiteboard.delete(request.ctx.session)

    return response.json({"id": whiteboard.id})


# Get a whiteboard
@bp.route("/<whiteboard_id:str>", methods=["GET"])
async def get_whiteboard_handler(request, whiteboard_id):
    async with request.ctx.session.begin():
        stmt = (
            select(Whiteboard)
            .where(Whiteboard.id == whiteboard_id)
            .where(Whiteboard.deleted_at == None)
        )
        whiteboard = await request.ctx.session.execute(stmt)
        whiteboard = whiteboard.scalar()

        if not whiteboard:
            return response.json({"error": "Whiteboard not found"}, status=404)

        whiteboard_dict = whiteboard.to_dict()
        async with aiofiles.open(f"whiteboard_data/{whiteboard_id}.json", "r") as f:
            data = await f.read()
            whiteboard_dict["data"] = json.loads(data)

    return response.json(whiteboard_dict)


# Get all whiteboards
@bp.route("/all", methods=["GET"])
async def get_all_whiteboards_handler(request):
    async with request.ctx.session.begin():
        stmt = select(Whiteboard).where(Whiteboard.deleted_at == None)
        whiteboards = await request.ctx.session.execute(stmt)
        whiteboards = whiteboards.scalars().all()

    return response.json(
        {"whiteboards": [whiteboard.to_dict() for whiteboard in whiteboards]}
    )


async def get_chat_history(whiteboard_id: str):
    async with aiofiles.open(f"whiteboard_data/{whiteboard_id}.json", "r") as f:
        data = await f.read()

    data = json.loads(data)
    nodes = data["graph"]["nodes"]

    chat_history = []
    for node in nodes:
        if node["type"] != "text":
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


# Get related questions about current whiteboard
@bp.route("/<whiteboard_id:str>/questions", methods=["POST"])
async def get_related_questions_handler(request, whiteboard_id):

    chat_history = await get_chat_history(whiteboard_id)

    chat_history_text = "\n".join(
        [f"{msg['sender']}: {msg['content']}" for msg in chat_history]
    )

    related_questions = get_related_questions(chat_history_text)

    return response.json({"related_questions": related_questions})


@bp.route("/<whiteboard_id:str>/insights", methods=["POST"])
async def get_related_insights_handler(request, whiteboard_id):
    chat_history = await get_chat_history(whiteboard_id)

    chat_history_text = "\n".join(
        [f"{msg['sender']}: {msg['content']}" for msg in chat_history]
    )

    related_insights = get_related_insights(chat_history_text)

    return response.json({"related_insights": related_insights})


@bp.route("/<whiteboard_id:str>/answer", methods=["POST"])
async def answer_question_handler(request, whiteboard_id):
    chat_history = await get_chat_history(whiteboard_id)

    answer = get_answer(chat_history)

    return response.json({"answer": answer})
