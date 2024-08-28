from contextvars import ContextVar

from sanic import Sanic, response
from sanic.log import logger
from sanic.request import Request
from sanic_cors import CORS
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from blueprints.whiteboard import bp as whiteboard_bp
from models import Whiteboard

app = Sanic(__name__)
CORS(app)

bind = create_async_engine("sqlite+aiosqlite:///local.db", echo=True)
_sessionmaker = sessionmaker(bind, class_=AsyncSession, expire_on_commit=False)
_base_model_session_ctx = ContextVar("session")


@app.middleware("request")
async def inject_session(request):
    request.ctx.session = _sessionmaker()
    request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.session)


@app.middleware("response")
async def close_session(request, response):
    if hasattr(request.ctx, "session_ctx_token"):
        _base_model_session_ctx.reset(request.ctx.session_ctx_token)
        await request.ctx.session.close()


# Initialize the database
@app.listener("before_server_start")
async def setup_db(app, loop):
    async with bind.begin() as conn:
        await conn.run_sync(Whiteboard.metadata.create_all)


@app.listener("before_server_start")
async def init_whiteboard_data_folder(app, loop):
    import os

    if not os.path.exists("whiteboard_data"):
        os.makedirs("whiteboard_data")


app.blueprint(whiteboard_bp)


@app.route("/health", methods=["GET"])
async def health(request: Request):
    logger.info("Health check")
    return response.json({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
