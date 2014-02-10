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
           SELECT * FROM links ORDER BY id LIMIT %s OFFSET %s
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
    # Optional query parameters
    query = request.args.get("q")
    link_id = request.args.get("id")
    query_terms = []
    link = None
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
    if link_id is not None:
        cur.execute("SELECT id, title, url, abstract FROM links WHERE id = %s", [link_id])
        link = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('index.html', results=results, query_terms=query_terms, link=link)


@app.route("/update-link", methods=['POST'])
def update_link():
    link_id = request.form['link_id']
    title = request.form['title']
    url = request.form['url']
    abstract = request.form['abstract']

    conn = psycopg2.connect(app.config['CONNECTION_STRING'])
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, tag FROM tags")
    # Get a dictionary of all this user's tags, with tag as key and id as value
    dbtags = { t["tag"] : t["id"] for t in cur.fetchall() }
    # Get a list of the posted tags and the file description
    tags = [tag.strip() for tag in request.form["tags"].split("|")]

    # Delete all the tag joins for this file
    cur.execute("DELETE FROM tags_links WHERE link_id = %s", [link_id])
    newtags = []
    alltags = []

    # Loop through all the posted tags
    for tag in tags:
        # If a tag isn't already in the db
        if tag not in dbtags:
            cur.execute("INSERT INTO tags (tag) VALUES (%s) RETURNING id", [tag])
            # Add the new tag and id to the dbtags dict so we don't have to query for it again
            dbtags[tag] = cur.fetchone()['id']
            newtags.append(tag)
        # Add the tag to the list of tags to be applied to this link
        alltags.append(dbtags[tag])

    conn.commit()

    print alltags

    if link_id == "0":
        cur.execute("INSERT INTO links (title, url, abstract) VALUES (%s, %s, %s) RETURNING id", [title, url, abstract])
        link_id = cur.fetchone()['id']
    else:
        cur.execute("UPDATE links SET title = %s, url = %s, abstract = %s WHERE id = %s", [title, url, abstract, link_id])

    conn.commit()

    for tag_id in alltags:
        # Insert a join record for this tag/file
        cur.execute("INSERT INTO tags_links (tag_id, link_id) VALUES (%s, %s)", [tag_id, link_id])

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