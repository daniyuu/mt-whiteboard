from sanic import Blueprint, response
from sanic.log import logger
from sqlalchemy import select
from models import Node

bp = Blueprint("node", url_prefix="/node")


# Create a node
@bp.route("/create", methods=["POST"])
async def create_node_handler(request):
    session = request.ctx.session
    whiteboard_id = request.json.get("whiteboard_id")
    content = request.json.get("content")
    status = request.json.get("status")
    created_by = request.json.get("created_by")
    extra_metadata = request.json.get("extra_metadata")
    ui_attributes = request.json.get("ui_attributes")
    if not whiteboard_id:
        logger.error("Whiteboard ID is required")
        return response.json({"error": "Whiteboard ID is required"}, status=400)
    if not content:
        logger.error("Content is required")
        return response.json({"error": "Content is required"}, status=400)
    if not status:
        logger.error("Status is required")
        return response.json({"error": "Status is required"}, status=400)
    if not created_by:
        logger.error("Created by is required")
        return response.json({"error": "Created by is required"}, status=400)

    async with session.begin():
        node = Node(
            whiteboard_id=whiteboard_id,
            content=content,
            status=status,
            created_by=created_by,
            extra_metadata=extra_metadata,
            ui_attributes=ui_attributes,
        )
        session.add(node)

    return response.json({"id": node.id})


# Update a node
@bp.route("/<node_id:int>/update", methods=["POST"])
async def update_node_handler(request, node_id):
    content = request.json.get("content")
    status = request.json.get("status")
    extra_metadata = request.json.get("extra_metadata")
    ui_attributes = request.json.get("ui_attributes")
    if not content:
        logger.error("Content is required")
        return response.json({"error": "Content is required"}, status=400)
    if not status:
        logger.error("Status is required")
        return response.json({"error": "Status is required"}, status=400)

    async with request.ctx.session.begin():
        node = await request.ctx.session.get(Node, node_id)
        node.content = content
        node.status = status
        node.extra_metadata = extra_metadata
        node.ui_attributes = ui_attributes

    return response.json({"id": node.id})


# Delete a node
@bp.route("/<node_id:int>/delete", methods=["POST"])
async def delete_node_handler(request, node_id):
    async with request.ctx.session.begin():
        node = await request.ctx.session.get(Node, node_id)
        await node.delete(request.ctx.session)

    return response.json({"id": node.id})


# Get a node
@bp.route("/<node_id:int>", methods=["GET"])
async def get_node_handler(request, node_id):
    async with request.ctx.session.begin():
        node = await request.ctx.session.get(Node, node_id)
        if not node:
            return response.json({"error": "Node not found"}, status=404)

    return response.json(node.to_dict())


# Get all nodes for a whiteboard
@bp.route("/all/<whiteboard_id:int>", methods=["GET"])
async def get_all_nodes_handler(request, whiteboard_id):
    async with request.ctx.session.begin():
        stmt = select(Node).where(Node.whiteboard_id == whiteboard_id)
        nodes = await request.ctx.session.execute(stmt)
        nodes = nodes.scalars().all()

    return response.json({"nodes": [node.to_dict() for node in nodes]})
