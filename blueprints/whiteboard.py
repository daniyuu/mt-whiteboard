from sanic.response import json
from sanic import Blueprint, response
from sanic.log import logger

bp = Blueprint("whiteboard", url_prefix="/whiteboard")


# Create a whiteboard
@bp.route("/create", methods=["POST"])
async def create_whiteboard_handler(request):
    name = request.json.get("name")
    if not name:
        logger.error("Name is required")
        return response.json({"error": "Name is required"}, status=400)
    whiteboard_id = 1
    return response.json({"id": whiteboard_id})


# Update a whiteboard
@bp.route("/<whiteboard_id:int>/update", methods=["POST"])
async def update_whiteboard_handler(request, whiteboard_id):
    name = request.json.get("name")
    if not name:
        logger.error("Name is required")
        return response.json({"error": "Name is required"}, status=400)
    return response.json({"id": whiteboard_id})


# Delete a whiteboard
@bp.route("/<whiteboard_id:int>/delete", methods=["POST"])
async def delete_whiteboard_handler(request, whiteboard_id):
    return response.json({"id": whiteboard_id})


# Get a whiteboard
@bp.route("/<whiteboard_id:int>", methods=["GET"])
async def get_whiteboard_handler(request, whiteboard_id):
    return response.json({"id": whiteboard_id})


# Get all whiteboards
@bp.route("/all", methods=["GET"])
async def get_all_whiteboards_handler(request):
    return response.json({"whiteboards": []})
