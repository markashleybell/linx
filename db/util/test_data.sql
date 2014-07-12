delete from tags_links;
delete from tags;
delete from links;
alter sequence tags_id_seq restart with 1;
alter sequence links_id_seq restart with 1;

INSERT INTO links 
  (title, url, abstract, tags) 
VALUES 
  ('Google', 'http://www.google.com', 'A search engine', 'search|google'),
  ('Bing', 'http://www.bing.com', 'Another search engine', 'search|microsoft');

INSERT INTO tags 
  (tag) 
VALUES 
  ('search'),
  ('google'),
  ('microsoft');

INSERT INTO tags_links
  (link_id, tag_id) 
VALUES 
  (1, 1),
  (1, 2),
  (2, 1),
  (2, 3);

