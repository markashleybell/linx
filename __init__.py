import psycopg2
from flask import Flask, render_template, request, send_from_directory
app = Flask(__name__)

app.config.from_pyfile('config.cfg')

@app.route("/")
def index():
    conn = psycopg2.connect(app.config['CONNECTION_STRING'])
    cur = conn.cursor()
    cur.execute("SELECT * FROM links;")
    result = cur.fetchone()
    cur.close()
    conn.close()

    return render_template('index.html', result=result[1])

# @app.route('/static.html')
@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

if __name__ == "__main__":
    app.run(debug=True)