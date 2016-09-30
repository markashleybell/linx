-- Users
CREATE TABLE users
(
  id INT IDENTITY(1, 1) NOT NULL,
  username NVARCHAR(256) NOT NULL,
  password NVARCHAR(256) NOT NULL,
  CONSTRAINT pk_users PRIMARY KEY (id)
)

-- Links
CREATE TABLE links
(
  id INT IDENTITY(1, 1) NOT NULL,
  title NVARCHAR(256) NOT NULL,
  url NVARCHAR(256) NOT NULL,
  abstract NVARCHAR(512) NULL,
  tags NVARCHAR(256) NULL,
  user_id int NOT NULL references users(id),
  CONSTRAINT pk_links PRIMARY KEY (id ASC)
)

-- Tags
CREATE TABLE tags
(
  id INT IDENTITY(1, 1) NOT NULL,
  tag NVARCHAR(50) NOT NULL,
  user_id int NOT NULL references users(id),
  CONSTRAINT pk_tags PRIMARY KEY (id ASC)
)

-- Tag/Link association
CREATE TABLE tags_links
(
  tag_id int NOT NULL references tags(id),
  link_id int NOT NULL references links(id),
  CONSTRAINT pk_tags_links PRIMARY KEY (tag_id ASC, link_id ASC)
)

-- Update display tags fields in link records after tag association added/removed
CREATE TRIGGER update_display_tags_delete
ON tags_links
FOR INSERT, DELETE
AS
BEGIN
    DECLARE @Delete BIT = CASE WHEN (SELECT COUNT(*) FROM DELETED) > 0 THEN 1 ELSE 0 END
    DECLARE @Insert BIT = CASE WHEN (SELECT COUNT(*) FROM INSERTED) > 0 THEN 1 ELSE 0 END

    DECLARE @LinkID INT = CASE WHEN @Delete = 1 THEN DELETED.link_id ELSE INSERTED.link_id END

    UPDATE 
        links 
    SET 
        tags = (
            SELECT 
                string_agg(tag, '|') -- TODO: update to SQL concat syntax
            FROM 
                tags 
            INNER JOIN 
                tags_links ON tags_links.tag_id = tags.id 
            WHERE tags_links.link_id = @LinkID
        ) 
    WHERE id = @LinkID;
END
GO

-- Insert test user
INSERT INTO users
    (id, username, password)
VALUES
    (1, 'me@markashleybell.com', '$6$rounds=100000$WFAb1fBhbTt5G9hF$uWKzu5Y2mwIG4myHU9fBp3uKcYOHebWJNtNEbtUV7aDpB6AYcZ3cXnSBT8S9N5X5qL/5SgFk2MFRUhEE6s.1q/');
