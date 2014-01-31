import psycopg2
from flask import Flask, render_template, request, send_from_directory
app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

# @app.route('/static.html')
@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

if __name__ == "__main__":
    app.run()