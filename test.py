from flask import Flask, jsonify
from routes.user import user_bp  # Make sure this is your user blueprint file

app = Flask(__name__)

@app.route('/')
def home():
    return "Flask is running!"


app.register_blueprint(user_bp, url_prefix="/user")

if __name__ == "__main__":
    app.run(debug=True)