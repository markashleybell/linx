import codecs, re, os, glob, htmlentitydefs

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)


def get_data(sets):
    for item in sets:
        match = re.search('<dt><a href="(.*?)".*?>(.*?)</a><dd>(.*)', item, re.IGNORECASE | re.MULTILINE)
        if match:
            yield { 'url': match.group(1), 'title': unescape(match.group(2)), 'abstract': unescape(match.group(3)), 'tags': [] }


for f in glob.glob('*.html'):
    source = codecs.open(f, 'r', 'utf-8')

    lines = [l.strip() for l in source.readlines()]

    titles = [t for t in lines if t.startswith('<DT>')]
    definitions = [d for d in lines if d.startswith('<DD>')]

    sets = [t + d for t, d in zip(titles, definitions)]

    results = [i for i in get_data(sets)]

    for r in results:
        for match in re.finditer(r'\s\#([a-z0-9-]+)', r['abstract'], re.IGNORECASE | re.MULTILINE):
            r['tags'].append(match.group(1))
            r['abstract'] = re.sub(r'(\s\#[a-z0-9\-]+)', '', r['abstract'], 0, re.IGNORECASE | re.MULTILINE).strip()
        r['tags'].append('new')
    
    #print results[0]#['abstract'].encode('utf-8')

    output = []

    for result in results:
        output.append("INSERT INTO links (title, url, abstract, tags) VALUES ('" + result['title'].replace("'", "''") + "', '" + result['url'] + "', '" + result['abstract'].replace("'", "''") + "', '" + '|'.join(result['tags']) + "');")

    o = codecs.open(os.path.split(f)[1].replace('html', 'sql'), 'w', 'utf-8')
    o.write(u'\r\n'.join(output))
    o.close()