-- Links
CREATE TABLE links
(
  id serial NOT NULL,
  title character varying(256) NOT NULL,
  url character varying(256) NOT NULL,
  abstract character varying(512) NULL,
  tags character varying(256) NULL,
  CONSTRAINT pk_links PRIMARY KEY (id)
)
WITH (OIDS=FALSE);

ALTER TABLE links OWNER TO postgres;

-- Tags
CREATE TABLE tags
(
  id serial NOT NULL,
  tag character varying(50) NOT NULL,
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

-- Function to update display tags field 
CREATE OR REPLACE FUNCTION update_display_tags() RETURNS trigger AS $update_display_tags$
    BEGIN
        UPDATE links SET tags = (SELECT string_agg(tag, '|') FROM tags INNER JOIN tags_links ON tags_links.tag_id = tags.id WHERE tags_links.link_id = new.link_id) WHERE id = new.link_id;
        RETURN NULL;
    END;
$update_display_tags$ LANGUAGE plpgsql;

-- Trigger to call display tag update on tag join table update
DROP TRIGGER update_display_tags ON tags_links;
CREATE TRIGGER update_display_tags AFTER INSERT OR UPDATE ON tags_links
    FOR EACH ROW EXECUTE PROCEDURE update_display_tags();

