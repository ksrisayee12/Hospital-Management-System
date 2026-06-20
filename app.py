from flask import Flask
from flask_cors import CORS
from config import FLASK_HOST, FLASK_PORT

from routes.doctor_routes import doctor_bp
from routes.nfc_routes import nfc_bp
from routes.module3_routes import module3_bp

try:
    from routes.ai_routes import ai_bp
    HAS_AI = True
except ImportError:
    HAS_AI = False
    print("\n[WARNING] AI dependencies are still installing. The AI Reviewer tab will not work yet, but the rest of the app is running normally!\n")

app = Flask(__name__)

CORS(app, resources={
    r"/api/*": {
        "origins": "*"
    }
})

app.register_blueprint(doctor_bp, url_prefix="/api")
app.register_blueprint(nfc_bp, url_prefix="/api")
app.register_blueprint(module3_bp, url_prefix="/api")
if HAS_AI:
    app.register_blueprint(ai_bp, url_prefix="/api")


@app.route("/", methods=["GET"])
def home():
    return {
        "success": True,
        "message": "Module 3 Flask Backend Running"
    }


if __name__ == "__main__":
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=True
    )