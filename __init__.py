import psycopg2
import psycopg2.extras
import psycopg2.extensions
from psycopg2.pool import ThreadedConnectionPool

psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

from flask import Flask, render_template, request, send_from_directory, redirect, url_for, jsonify
from contextlib import contextmanager


@contextmanager
def get_connection():
    """Connection factory for pooled dbconnections"""
    conn = connection_pool.getconn()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    else:
        conn.commit()
    finally:
        connection_pool.putconn(conn)


def unique_substrings(s):
    """Return all unique substrings of a string with length >= 2"""
    seen = set()
    for k in xrange(2, len(s)+1):
        for i in xrange(len(s)-k+1):
            result = s[i:i+k]
            if result not in seen:
                seen.add(result)
                yield result


def insert_and_associate_tags(conn, cur, link_id, tags):
    """Given a list of tags and a link ID, insert any tags which don't already
    exist in the database, then associate this link with all the tags"""
    # Get all of this user's tags from the database
    cur.execute('SELECT id, tag FROM tags')
    # Create a dictionary of the existing tags, with tag as key and id as value
    dbtags = { t['tag'] : t['id'] for t in cur.fetchall() }
    # Delete all the tag joins for this link
    cur.execute('DELETE FROM tags_links WHERE link_id = %s', [link_id])
    conn.commit()
    # Loop through all the posted tags
    for tag in tags:
        # If a tag isn't already in the db
        if tag not in dbtags:
            cur.execute('INSERT INTO tags (tag) VALUES (%s) RETURNING id', [tag])
            # Add the new tag and id to the dbtags dict so we don't have to query for it again
            dbtags[tag] = cur.fetchone()['id']
        # Insert a join record for this tag/link
        cur.execute('INSERT INTO tags_links (tag_id, link_id) VALUES (%s, %s)', [dbtags[tag], link_id])

    conn.commit()
    # Clean up orphaned tags (not associated with any link)
    cur.execute('DELETE FROM tags t WHERE NOT EXISTS (SELECT * FROM tags_links tl WHERE tl.tag_id = t.id)', [link_id])

def process_tag_data_string(data_string):
    return [tag.lower().strip() for tag in data_string.split('|')]

# Set up application
app = Flask(__name__)
# Load configuration
app.config.from_pyfile('config.cfg')
# Set up - connection pool
connection_pool = ThreadedConnectionPool(1, 20, app.config['CONNECTION_STRING'])
# Get tag search type from config
tag_search_method = app.config['TAG_SEARCH_METHOD']

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


@app.route('/')
@app.route('/<int:page>')
def index(page=1):
    # Paging variables
    pagesize = app.config['PAGE_SIZE']
    offset = (page - 1) * pagesize
    # Other variables
    results = None
    paging = None
    # Optional query parameters
    query = request.args.get('q')
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
    with get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Get the total number of results *before* limit/offset
        cur.execute('SELECT COUNT(*) FROM (' + sql + ') AS total', params[:2])
        total = int(cur.fetchone()['count'])
        # Set up paging data for convenience
        pages = total / pagesize if total % pagesize == 0 else total / pagesize + 1
        paging = { 'page': page, 'pagesize': pagesize, 'total': total, 'pages': pages }
        # Get the result data
        cur.execute('SELECT * FROM (' + sql + ') AS results LIMIT %s OFFSET %s', params)
        results = cur.fetchall()

    return render_template('index.html', results=results, query_terms=query_terms, paging=paging)


@app.route('/links', methods=['GET'])
def link_list():
    links = None
    with get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT id, title, url, abstract, tags FROM links', [])
        links = cur.fetchall()

    return jsonify(links=[{'id': l['id'], 'title': l['title'], 'url': l['url'], 'abstract': l['abstract'], 'tags': l['tags'].split('|')} for l in links])


@app.route('/links', methods=['POST'])
def link_create():
    title = request.form['title']
    url = request.form['url']
    abstract = request.form['abstract']
    tags = process_tag_data_string(request.form['tags'])

    with get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('INSERT INTO links (title, url, abstract) VALUES (%s, %s, %s) RETURNING id', [title, url, abstract])
        id = cur.fetchone()['id']
        insert_and_associate_tags(conn, cur, id, tags)

    return jsonify({'id': id, 'title': title, 'url': url, 'abstract': abstract, 'tags': tags})


@app.route('/links/new', methods=['GET'])
@app.route('/links/<int:id>', methods=['GET'])
def link_retrieve(id=0):
    link = None
    with get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT id, title, url, abstract, tags FROM links WHERE id = %s', [id])
        link = cur.fetchone()

    return render_template('link.html', link=link)    


@app.route('/links/<int:id>', methods=['POST'])
def link_update(id):
    title = request.form['title']
    url = request.form['url']
    abstract = request.form['abstract']
    tags = process_tag_data_string(request.form['tags'])

    with get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('UPDATE links SET title = %s, url = %s, abstract = %s WHERE id = %s', [title, url, abstract, id])
        insert_and_associate_tags(conn, cur, id, tags)

    return jsonify({'id': id, 'title': title, 'url': url, 'abstract': abstract, 'tags': tags})


@app.route('/links/<int:id>', methods=['DELETE'])
def link_delete(id):
    with get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('DELETE FROM tags_links WHERE link_id = %s', [id])
        cur.execute('DELETE FROM links WHERE id = %s', [id])
    
    return '', 204


@app.route('/tags')
def tags():
    with get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Get all of this user's tags from the database
        cur.execute('SELECT id, tag FROM tags')
        tags = cur.fetchall()

    # If search type B, return each tag with a list of its unique substrings
    # as tokens, to allow partial string matching with Bloodhound
    tags_processed = list([{'tag': t['tag'],'tokens': list(unique_substrings(t['tag'])) if tag_search_method == 'B' else [t['tag']]} for t in tags])

    return jsonify(tags=tags_processed)


@app.route('/manage-tags')
def manage_tags():
    with get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Get all of this user's tags from the database
        cur.execute('SELECT id, tag, (SELECT COUNT(*) FROM tags_links WHERE tags_links.tag_id = tags.id) AS usecount FROM tags ORDER BY tag')
        tags = cur.fetchall()

    return render_template('manage_tags.html', tags=tags)


@app.route('/manage-tags-update', methods=['POST'])
def manage_tags_update():
    with get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # ID of the tag we are going to merge all the others with
        target_id = int(request.form['target'])
        # All tags which will be merged with the target
        merge_tags = process_tag_data_string(request.form['tags'])
        cur.execute('SELECT id, tag FROM tags WHERE tag IN %s', [tuple(merge_tags)])
        # Get all the IDs for the tags to be merged into our target tag
        ids = [t['id'] for t in cur.fetchall()]
        # For each tag we merge, update all existing references to 
        # its ID to the ID of the target, then delete the merged tag
        for id in ids:
            cur.execute('UPDATE tags_links SET tag_id = %s WHERE tag_id = %s AND NOT EXISTS (SELECT link_id FROM tags_links tl WHERE tl.tag_id = %s AND tl.link_id = tags_links.link_id)', [target_id, id, target_id])
            cur.execute('DELETE FROM tags_links WHERE tag_id = %s', [id])
            cur.execute('DELETE FROM tags WHERE id = %s', [id])

    return redirect(url_for('manage_tags'))


@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


if __name__ == '__main__':
    app.run(debug=True, threaded=True)