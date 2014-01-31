-- Links
CREATE TABLE links
(
  id serial NOT NULL,
  title character varying(50) NOT NULL,
  url character varying(256) NOT NULL,
  abstract character varying(512) NULL,
  CONSTRAINT pk_links PRIMARY KEY (id)
)
WITH (OIDS=FALSE);

ALTER TABLE links OWNER TO postgres;

-- Tags
CREATE TABLE tags
(
  id serial NOT NULL,
  "name" character varying(50) NOT NULL,
  CONSTRAINT pk_tags PRIMARY KEY (id)
)
WITH (OIDS=FALSE);

ALTER TABLE tags OWNER TO postgres;

-- Tag/Link association
CREATE TABLE tags_links
(
  tag_id int NOT NULL references tags(id),
  link_id int NOT NULL references links(id),
  CONSTRAINT pk_tags_links PRIMARY KEY (tag_id, link_id)
)
WITH (OIDS=FALSE);

ALTER TABLE tags_links OWNER TO postgres;