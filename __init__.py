import psycopg2
import psycopg2.extras
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
from flask import Flask, render_template, request, send_from_directory
app = Flask(__name__)

app.config.from_pyfile('config.cfg')

paging_sql = """
             SELECT
                 l1.*
             FROM
                 links l1, tags_links m1, tags t1
             WHERE
                 m1.tag_id = t1.id
             AND
                 (t1.tag IN ({0}))
             AND
                 l1.id = m1.link_id
             GROUP BY
                 l1.id
             HAVING
                 COUNT(l1.id) = {1}
             LIMIT %s
             OFFSET %s
             """

@app.route("/")
@app.route("/<int:page>")
def index(page=1):
    pagesize = 2
    offset = (page - 1) * pagesize
    
    query = request.args.get("q")

    sql = "SELECT * FROM links ORDER BY id LIMIT %s OFFSET %s;"
    params = [pagesize, offset]

    if query is not None:
        # Try and tidy up the tag query terms a bit
        query_terms = [s.lower().strip() for s in query.split('|') if s.strip() is not '']
        # Create parameter placeholders for IN clauses
        in_list = ','.join('%s' for s in query_terms)
        # Subsitute the placeholders in the SQL string with the correct values
        sql = paging_sql.format(in_list, len(query_terms))
        # Slightly unwieldy, but safe way of supplying the param list
        params = query_terms.extend([pagesize, offset])
        print sql
        print params

    
    conn = psycopg2.connect(app.config['CONNECTION_STRING'])
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(sql, params)
    dic = cur.fetchall()
    cur.close()
    conn.close()

    print dic
    return render_template('index.html', result=dic)

# @app.route('/static.html')
@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

if __name__ == "__main__":
    app.run(debug=True)