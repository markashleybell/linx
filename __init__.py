import os
import pymssql

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from flask import Flask, Blueprint, render_template, request, send_from_directory, \
     redirect, url_for, jsonify, flash
from flask.ext.login import LoginManager, current_user, login_required, \
     login_user, logout_user, UserMixin, confirm_login, fresh_login_required
from contextlib import contextmanager
from passlib.hash import sha512_crypt
from flask_sslify import SSLify


def get_connection():
    conn = pymssql.connect(
        server=app.config['DB_SERVER'],
        database=app.config['DB_NAME']
    )
    return conn


def unique_substrings(s):
    """Return all unique substrings of a string with length >= 2"""
    seen = set()
    for k in xrange(2, len(s)+1):
        for i in xrange(len(s)-k+1):
            result = s[i:i+k]
            if result not in seen:
                seen.add(result)
                yield result


def delete_orphaned_tags(conn, cur):
    """Clean up orphaned tags (not associated with any link)"""
    cur.execute('DELETE FROM tags WHERE tags.user_id = %s AND NOT EXISTS (SELECT * FROM tags_links tl WHERE tl.tag_id = tags.id)', (current_user.id))


def insert_and_associate_tags(conn, cur, link_id, tags):
    """Given a list of tags and a link ID, insert any tags which don't already
    exist in the database, then associate this link with all the tags"""
    # Get all of this user's tags from the database
    cur.execute('SELECT id, tag FROM tags WHERE user_id = %s', (current_user.id))
    # Create a dictionary of the existing tags, with tag as key and id as value
    dbtags = { t['tag'] : t['id'] for t in cur.fetchall() }
    # Delete all the tag joins for this link
    cur.execute('DELETE FROM tags_links WHERE link_id = %s', (link_id))
    conn.commit()
    # Loop through all the posted tags
    for tag in tags:
        # If a tag isn't already in the db
        if tag not in dbtags:
            cur.execute('INSERT INTO tags (tag, user_id) VALUES (%s, %s); SELECT CAST(SCOPE_IDENTITY() AS INT) AS id;', (tag, current_user.id))
            # Add the new tag and id to the dbtags dict so we don't have to query for it again
            dbtags[tag] = cur.fetchone()['id']
        # Insert a join record for this tag/link
        cur.execute('INSERT INTO tags_links (tag_id, link_id) VALUES (%s, %s)', (dbtags[tag], link_id))
    conn.commit()
    delete_orphaned_tags(conn, cur)


def process_tag_data_string(data_string):
    return [tag.lower().strip() for tag in data_string.split('|')]


# Set up application
app = Flask(__name__)
sslify = SSLify(app)

# Load configuration
app.config.from_pyfile('config.cfg')
app.secret_key = app.config['SECRET_KEY']


# Set up login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '.login'
login_manager.login_message = 'Please log in.'


@app.context_processor
def view_helpers():
    def get_pagination_range(total_pages, size, current_page):
        minpage = max(1, (current_page - size))
        maxpage = min(total_pages, (current_page + size))

        output = []

        if minpage != 1:
            output.extend(['1', '...'])

        output.extend([str(i) for i in range(minpage, maxpage + 1)])

        if maxpage != total_pages:
            output.extend(['...', str(total_pages)])

        return output
    return dict(get_pagination_range=get_pagination_range)


class User(UserMixin):
    """User class based on Flask-Login UserMixin"""
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(userid):
    """Callback to load user from db, called by Flask-Login"""
    user = None
    with get_connection() as conn:
        cur = conn.cursor(as_dict=True)
        cur.execute('SELECT id, username FROM users WHERE id = %s', (userid))
        user = cur.fetchone()
    if user is not None:
        return User(int(user['id']))
    return None



# Get tag search type from config
tag_search_method = app.config['TAG_SEARCH_METHOD']

# Normal (non-query) SQL
list_sql = """
           SELECT * FROM links WHERE user_id = %s
           """

# Tag query SQL
query_sql = """
            SELECT
                l1.id, l1.title, l1.url, l1.abstract, l1.tags
            FROM
                links l1, tags_links m1, tags t1
            WHERE
                l1.user_id = %s
            AND
                m1.tag_id = t1.id
            AND
                t1.tag IN %s
            AND
                l1.id = m1.link_id
            GROUP BY
                l1.id, l1.title, l1.url, l1.abstract, l1.tags
            HAVING
                COUNT(l1.id) = %s
            """

@app.route('/linx')
@app.route('/linx/<int:page>')
@login_required
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
    params = (current_user.id, offset, pagesize)
    countparams = (current_user.id)
    
    # If any tags were passed in as a query
    if query is not None:
        # Try and tidy up the tag query terms a bit
        query_terms = [s.lower().strip() for s in query.split('|') if s.strip() is not '']
        # Use the query SQL
        sql = query_sql
        params = (current_user.id, tuple(query_terms), len(query_terms), offset, pagesize)
        countparams = (current_user.id, tuple(query_terms), len(query_terms))

    # Set up the connection
    with get_connection() as conn:
        cur = conn.cursor(as_dict=True)
        # Get the total number of results *before* limit/offset
        cur.execute('SELECT COUNT(*) AS total FROM (' + sql + ') AS results', countparams)
        total = int(cur.fetchone()['total'])
        # Set up paging data for convenience
        pages = total / pagesize if total % pagesize == 0 else total / pagesize + 1
        paging = { 'page': page, 'pagesize': pagesize, 'total': total, 'pages': pages }
        # Get the result data
        cur.execute('SELECT * FROM (' + sql + ') AS results ORDER BY id DESC OFFSET %s ROWS FETCH NEXT %s ROWS ONLY', params)
        results = cur.fetchall()

    return render_template('index.html', results=results, query_terms=query_terms, paging=paging)


@app.route('/linx/login', methods=['GET'])
def login():
    return render_template('login.html', next=request.args['next'])


@app.route('/linx/login', methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']
    next = request.form['next']

    userdetails = None
    with get_connection() as conn:
        cur = conn.cursor(as_dict=True)
        cur.execute('SELECT id, password FROM users WHERE username = %s', (username))
        userdetails = cur.fetchone()
    
    if userdetails is not None and sha512_crypt.verify(password, userdetails['password']):
        login_user(User(userdetails['id']), remember=True)
        return redirect(next)

    return render_template('login.html', next=next, username=username)


@app.route('/linx/logout', methods=['GET'])
def logout():
    logout_user();
    return redirect(url_for('.index'))


@app.route('/linx/links', methods=['GET'])
@login_required
def link_list():
    links = None
    with get_connection() as conn:
        cur = conn.cursor(as_dict=True)
        cur.execute('SELECT id, title, url, abstract, tags FROM links WHERE user_id = %s', (current_user.id))
        links = cur.fetchall()

    return jsonify(links=[{'id': l['id'], 'title': l['title'], 'url': l['url'], 'abstract': l['abstract'], 'tags': l['tags'].split('|')} for l in links])


@app.route('/linx/links', methods=['POST'])
@login_required
def link_create():
    title = request.form['title']
    url = request.form['url']
    abstract = request.form['abstract']
    tags = process_tag_data_string(request.form['tags'])

    with get_connection() as conn:
        cur = conn.cursor(as_dict=True)
        
        # Check if a record with the same URL already exists in the database
        cur.execute('SELECT COUNT(id) AS count FROM links WHERE url = %s AND user_id = %s', (url, current_user.id)) 
        exists = int(cur.fetchone()['count'])
        # If there is, return an error message
        if exists is not 0:
            return jsonify({'error': 'This url has already been bookmarked.'})


        # Otherwise, just save the details
        cur.execute('INSERT INTO links (title, url, abstract, user_id) VALUES (%s, %s, %s, %s); SELECT CAST(SCOPE_IDENTITY() AS INT) AS id;', (title, url, abstract, current_user.id))
        id = cur.fetchone()['id']
        insert_and_associate_tags(conn, cur, id, tags)

    return jsonify({'id': id, 'title': title, 'url': url, 'abstract': abstract, 'tags': tags})


@app.route('/linx/links/new', methods=['GET'])
@app.route('/linx/links/<int:id>', methods=['GET'])
@login_required
def link_retrieve(id=0):
    link = None
    with get_connection() as conn:
        cur = conn.cursor(as_dict=True)
        cur.execute('SELECT id, title, url, abstract, tags FROM links WHERE id = %s AND user_id = %s', (id, current_user.id))
        link = cur.fetchone()

    return render_template('link.html', link=link)    


@app.route('/linx/links/<int:id>', methods=['POST'])
@login_required
def link_update(id):
    title = request.form['title']
    url = request.form['url']
    abstract = request.form['abstract']
    tags = process_tag_data_string(request.form['tags'])

    with get_connection() as conn:
        cur = conn.cursor(as_dict=True)
        cur.execute('UPDATE links SET title = %s, url = %s, abstract = %s WHERE id = %s AND user_id = %s', (title, url, abstract, id, current_user.id))
        insert_and_associate_tags(conn, cur, id, tags)

    return jsonify({'id': id, 'title': title, 'url': url, 'abstract': abstract, 'tags': tags})


@app.route('/linx/links/<int:id>', methods=['DELETE'])
@login_required
def link_delete(id):
    with get_connection() as conn:
        cur = conn.cursor(as_dict=True)
        # Check that the current user owns the link we're going to delete
        cur.execute('SELECT COUNT(id) AS count FROM links WHERE id = %s AND user_id = %s', (id, current_user.id)) 
        exists = int(cur.fetchone()['count'])
        if exists is not 0:
            cur.execute('DELETE FROM tags_links WHERE link_id = %s', (id))
            cur.execute('DELETE FROM links WHERE id = %s AND user_id = %s', (id, current_user.id))
            conn.commit()
            delete_orphaned_tags(conn, cur)

    return '', 204


@app.route('/linx/tags')
@login_required
def tags():
    with get_connection() as conn:
        cur = conn.cursor(as_dict=True)
        # Get all of this user's tags from the database
        cur.execute('SELECT id, tag FROM tags WHERE user_id = %s', (current_user.id))
        tags = cur.fetchall()

    # If search type B, return each tag with a list of its unique substrings
    # as tokens, to allow partial string matching with Bloodhound
    tags_processed = list([{'tag': t['tag'],'tokens': list(unique_substrings(t['tag'])) if tag_search_method == 'B' else [t['tag']]} for t in tags])

    return jsonify(tags=tags_processed)


@app.route('/linx/manage-tags')
@login_required
def manage_tags():
    with get_connection() as conn:
        cur = conn.cursor(as_dict=True)
        # Get all of this user's tags from the database
        cur.execute('SELECT id, tag, (SELECT COUNT(*) FROM tags_links WHERE tags_links.tag_id = tags.id) AS usecount FROM tags WHERE user_id = %s ORDER BY tag', (current_user.id))
        tags = cur.fetchall()

    return render_template('manage_tags.html', tags=tags)


@app.route('/linx/manage-tags-update', methods=['POST'])
@login_required
def manage_tags_update():
    with get_connection() as conn:
        cur = conn.cursor(as_dict=True)
        # ID of the tag we are going to merge all the others with
        target_id = int(request.form['target'])
        # All tags which will be merged with the target
        merge_tags = process_tag_data_string(request.form['tags'])
        # Make sure we only get tags for the current user
        cur.execute('SELECT id, tag FROM tags WHERE user_id = %s AND tag IN %s', (current_user.id, tuple(merge_tags)))
        # Get all the IDs for the tags to be merged into our target tag
        ids = [t['id'] for t in cur.fetchall()]
        # For each tag we merge, update all existing references to 
        # its ID to the ID of the target, then delete the merged tag
        # Updates and deletes are safe because we're only enumerating tag IDs for this user
        for id in ids:
            cur.execute('UPDATE tags_links SET tag_id = %s WHERE tag_id = %s AND NOT EXISTS (SELECT link_id FROM tags_links tl WHERE tl.tag_id = %s AND tl.link_id = tags_links.link_id)', (target_id, id, target_id))
            cur.execute('DELETE FROM tags_links WHERE tag_id = %s', (id))
            cur.execute('DELETE FROM tags WHERE id = %s', (id))
            conn.commit()

    return redirect(url_for('manage_tags'))


@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


if __name__ == '__main__':
    # app.run(debug=True, threaded=True)
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(os.environ['HTTP_PLATFORM_PORT'])
    loop = IOLoop.instance()
    loop.start()
