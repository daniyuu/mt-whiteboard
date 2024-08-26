from sanic import Sanic, response
from sanic.log import logger
from sanic.request import Request
from sanic_cors import CORS
from blueprints.whiteboard import bp as whiteboard_bp


app = Sanic(__name__)
CORS(app)
app.blueprint(whiteboard_bp)


@app.route("/health", methods=["GET"])
async def health(request: Request):
    logger.info("Health check")
    return response.json({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
