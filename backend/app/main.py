from flask import Flask, jsonify
from flask_cors import CORS

from api.routes import router
from app.config import settings


app = Flask(__name__)
CORS(
    app,
    origins=["http://127.0.0.1:5173", "http://localhost:5173", "file://"],
)

app.register_blueprint(router)


@app.get("/")
def root():
    return jsonify(name="JX JARVIS", status="online")


if __name__ == "__main__":
    from waitress import serve

    serve(app, host="127.0.0.1", port=settings.backend_port)
