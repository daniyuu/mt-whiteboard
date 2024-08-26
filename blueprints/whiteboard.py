from sanic import Blueprint, response
from sanic.log import logger
from models import Whiteboard

bp = Blueprint("whiteboard", url_prefix="/whiteboard")


# Create a whiteboard
@bp.route("/create", methods=["POST"])
async def create_whiteboard_handler(request):
    session = request.ctx.session
    name = request.json.get("name")
    if not name:
        logger.error("Name is required")
        return response.json({"error": "Name is required"}, status=400)

    async with session.begin():
        whiteboard = Whiteboard(name=name)
        session.add(whiteboard)

    return response.json({"id": whiteboard.id})


# Update a whiteboard
@bp.route("/<whiteboard_id:int>/update", methods=["POST"])
async def update_whiteboard_handler(request, whiteboard_id):
    name = request.json.get("name")
    if not name:
        logger.error("Name is required")
        return response.json({"error": "Name is required"}, status=400)

    async with request.ctx.session.begin():
        whiteboard = await request.ctx.session.get(Whiteboard, whiteboard_id)
        whiteboard.name = name

    return response.json({"id": whiteboard.id})


# Delete a whiteboard
@bp.route("/<whiteboard_id:int>/delete", methods=["POST"])
async def delete_whiteboard_handler(request, whiteboard_id):

    async with request.ctx.session.begin():
        whiteboard = await request.ctx.session.get(Whiteboard, whiteboard_id)
        whiteboard.delete()

    return response.json({"id": whiteboard.id})


# Get a whiteboard
@bp.route("/<whiteboard_id:int>", methods=["GET"])
async def get_whiteboard_handler(request, whiteboard_id):
    async with request.ctx.session.begin():
        whiteboard = await request.ctx.session.get(Whiteboard, whiteboard_id)
        if not whiteboard:
            return response.json({"error": "Whiteboard not found"}, status=404)

    return response.json(whiteboard.to_dict())


# Get all whiteboards
@bp.route("/all", methods=["GET"])
async def get_all_whiteboards_handler(request):
    async with request.ctx.session.begin():
        whiteboards = await request.ctx.session.execute(Whiteboard.select())
        whiteboards = whiteboards.scalars().all()

    return response.json(
        {"whiteboards": [whiteboard.to_dict() for whiteboard in whiteboards]}
    )
