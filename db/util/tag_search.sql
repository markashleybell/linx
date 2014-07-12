SELECT
    l1.*
FROM
    links l1, tags_links m1, tags t1
WHERE
    m1.tag_id = t1.id
AND
    (t1.tag IN ('search', 'google'))
AND
    l1.id = m1.link_id
GROUP BY
    l1.id
HAVING
    COUNT(l1.id) = 2