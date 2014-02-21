import psycopg2
import psycopg2.extras
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, jsonify
app = Flask(__name__)

# Load configuration
app.config.from_pyfile('config.cfg')

# Normal (non-query) SQL
list_sql = """
           SELECT * FROM links ORDER BY id DESC
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
            ORDER BY 
                l1.id DESC
            """


@app.route("/")
@app.route("/<int:page>")
def index(page=1):
    # Paging variables
    pagesize = app.config['PAGE_SIZE']
    offset = (page - 1) * pagesize
    # Other variables
    link = None
    results = None
    paging = None
    # Optional query parameters
    query = request.args.get("q")
    link_id = request.args.get("id")
    query_terms = []

    # Set up default SQL/parameters
    sql = list_sql
    params = [pagesize, offset]
    
    # If any tags were passed in as a query
    if query is not None:
        # Try and tidy up the tag query terms a bit
        query_terms = [s.lower().strip() for s in query.split('|') if s.strip() is not '']
        # Use the query SQL
        sql = query_sql
        params = [tuple(query_terms), len(query_terms), pagesize, offset]

    # Set up the connection
    db = psycopg2.connect(app.config['CONNECTION_STRING'])
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # If a link is being edited, no need to load all the results
    if link_id is not None:
        cur.execute("SELECT id, title, url, abstract, tags FROM links WHERE id = %s", [link_id])
        link = cur.fetchone()
    else:
        # Get the total number of results *before* limit/offset
        cur.execute("SELECT COUNT(*) FROM (" + sql + ") AS total", params[:2])
        total = int(cur.fetchone()['count'])
        # Set up paging data for convenience
        pages = total / pagesize if total % pagesize == 0 else total / pagesize + 1
        paging = { "page": page, "pagesize": pagesize, "total": total, "pages": pages }
        # Get the result data
        cur.execute("SELECT * FROM (" + sql + ") AS results LIMIT %s OFFSET %s", params)
        results = cur.fetchall()

    cur.close()
    db.close()

    return render_template('index.html', results=results, query_terms=query_terms, paging=paging, link=link, link_id=link_id)


@app.route("/update-link", methods=['POST'])
def update_link():
    link_id = request.form['link_id']
    title = request.form['title']
    url = request.form['url']
    abstract = request.form['abstract']
    xhr = int(request.form['xhr']) is 1

    tags = [tag.strip() for tag in request.form["tags"].split("|")]

    db = psycopg2.connect(app.config['CONNECTION_STRING'])
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Insert or update the basic details
    if link_id == "0":
        cur.execute("INSERT INTO links (title, url, abstract, tags) VALUES (%s, %s, %s, %s) RETURNING id", [title, url, abstract, '|'.join(tags)])
        link_id = cur.fetchone()['id']
    else:
        cur.execute("UPDATE links SET title = %s, url = %s, abstract = %s, tags = %s WHERE id = %s", [title, url, abstract, '|'.join(tags), link_id])
    db.commit()

    # Get all of this user's tags from the database
    cur.execute("SELECT id, tag FROM tags")
    # Create a dictionary of the existing tags, with tag as key and id as value
    dbtags = { t["tag"] : t["id"] for t in cur.fetchall() }

    # Delete all the tag joins for this link
    cur.execute("DELETE FROM tags_links WHERE link_id = %s", [link_id])
    db.commit()

    # Loop through all the posted tags
    for tag in tags:
        # If a tag isn't already in the db
        if tag not in dbtags:
            cur.execute("INSERT INTO tags (tag) VALUES (%s) RETURNING id", [tag])
            # Add the new tag and id to the dbtags dict so we don't have to query for it again
            dbtags[tag] = cur.fetchone()['id']
        # Insert a join record for this tag/link
        cur.execute("INSERT INTO tags_links (tag_id, link_id) VALUES (%s, %s)", [dbtags[tag], link_id])
    db.commit()

    cur.close()
    db.close()

    if not xhr:
        return redirect(url_for('index'))
    else:
        return jsonify(success=True)


@app.route('/tags')
def tags():
    db = psycopg2.connect(app.config['CONNECTION_STRING'])
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get all of this user's tags from the database
    cur.execute("SELECT id, tag FROM tags")
    tags = cur.fetchall()

    cur.close()
    db.close()

    return jsonify(tags=tags)

# @app.route('/static.html')
@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

if __name__ == "__main__":
    app.run(debug=True, threaded=True)