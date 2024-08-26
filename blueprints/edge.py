from sanic import Blueprint, response
from sanic.log import logger

from models import Edge

bp = Blueprint("edge", url_prefix="/edge")


@bp.route("/create", methods=["POST"])
async def create_edge_handler(request):
    session = request.ctx.session
    whiteboard_id = request.json.get("whiteboard_id")
    source_id = request.json.get("source_id")
    target_id = request.json.get("target_id")
    extra_metadata = request.json.get("extra_metadata")
    ui_attributes = request.json.get("ui_attributes")
    if not whiteboard_id:
        logger.error("Whiteboard ID is required")
        return response.json({"error": "Whiteboard ID is required"}, status=400)
    if not source_id:
        logger.error("Source ID is required")
        return response.json({"error": "Source ID is required"}, status=400)
    if not target_id:
        logger.error("Target ID is required")
        return response.json({"error": "Target ID is required"}, status=400)

    async with session.begin():
        edge = Edge(
            whiteboard_id=whiteboard_id,
            source_id=source_id,
            target_id=target_id,
            extra_metadata=extra_metadata,
            ui_attributes=ui_attributes,
        )
        session.add(edge)

    return response.json({"id": edge.id})


@bp.route("/<edge_id:int>/update", methods=["POST"])
async def update_edge_handler(request, edge_id):
    extra_metadata = request.json.get("extra_metadata")
    ui_attributes = request.json.get("ui_attributes")

    async with request.ctx.session.begin():
        edge = await request.ctx.session.get(Edge, edge_id)
        edge.extra_metadata = extra_metadata
        edge.ui_attributes = ui_attributes

    return response.json({"id": edge.id})


@bp.route("/<edge_id:int>/delete", methods=["POST"])
async def delete_edge_handler(request, edge_id):
    async with request.ctx.session.begin():
        edge = await request.ctx.session.get(Edge, edge_id)
        edge.delete()

    return response.json({"id": edge.id})


@bp.route("/<edge_id:int>", methods=["GET"])
async def get_edge_handler(request, edge_id):
    async with request.ctx.session.begin():
        edge = await request.ctx.session.get(Edge, edge_id)
        if not edge:
            return response.json({"error": "Edge not found"}, status=404)

    return response.json(edge.to_dict())


# Get all relationships for a whiteboard
@bp.route("/all/<whiteboard_id:int>", methods=["GET"])
async def get_all_edges_handler(request, whiteboard_id):
    async with request.ctx.session.begin():
        edges = await request.ctx.session.execute(
            Edge.select().where(Edge.whiteboard_id == whiteboard_id)
        )
        edges = edges.scalars().all()

    return response.json({"edges": [edge.to_dict() for edge in edges]})
