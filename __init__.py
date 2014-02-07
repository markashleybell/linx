import psycopg2
import psycopg2.extras
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
app = Flask(__name__)

# Load configuration
app.config.from_pyfile('config.cfg')

# Normal (non-query) SQL
list_sql = """
           SELECT * FROM links ORDER BY id LIMIT %s OFFSET %s;
           """

# Tag query SQL
query_sql = """
            SELECT
                l1.*
            FROM
                links l1, tags_links m1, tags t1
            WHERE
                m1.tag_id = t1.id
            AND
                t1.tag IN %s
            AND
                l1.id = m1.link_id
            GROUP BY
                l1.id
            HAVING
                COUNT(l1.id) = %s
            LIMIT %s
            OFFSET %s
            """

@app.route("/")
@app.route("/<int:page>")
def index(page=1):
    # Paging variables
    pagesize = app.config['PAGE_SIZE']
    offset = (page - 1) * pagesize
    # Optional tag query parameters
    query = request.args.get("q")
    query_terms = []
    # Set up default SQL/parameters
    sql = list_sql
    params = [pagesize, offset]
    # If any tags were passed in as a query
    if query is not None:
        # Try and tidy up the tag query terms a bit
        query_terms = [s.lower().strip() for s in query.split(' ') if s.strip() is not '']
        # Use the query SQL
        sql = query_sql
        params = [tuple(query_terms), len(query_terms), pagesize, offset]
    # Get the data
    conn = psycopg2.connect(app.config['CONNECTION_STRING'])
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results, query_terms=query_terms)

@app.route("/update-link", methods=['POST'])
def update_link():
    link_id = request.form['link_id']
    title = request.form['title']
    url = request.form['url']
    abstract = request.form['abstract']
    tags = request.form['tags']
    conn = psycopg2.connect(app.config['CONNECTION_STRING'])
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("INSERT INTO links (title, url, abstract) VALUES (%s, %s, %s)", [title, url, abstract])
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

# @app.route('/static.html')
@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

if __name__ == "__main__":
    app.run(debug=True)