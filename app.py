from flask import Flask, jsonify

# Initialize the Flask application
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    """
    Root endpoint:
    Displays the welcome message when visitors hit the base URL.
    """
    return "<h1>Welcome to My First DevOps Project!</h1><p>Application is up and serving traffic.</p>"

@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint:
    Used by orchestrators (like Kubernetes, Docker, or Load Balancers)
    to verify that the application is alive and healthy.
    """
    return jsonify(
        status="healthy",
        message="Application is running smoothly"
    ), 200

if __name__ == "__main__":
    # Binding to host '0.0.0.0' allows external connections,
    # which is essential when running inside a Docker container.
    # The application will listen on port 5000.
    app.run(host="0.0.0.0", port=5000, debug=False)
