CREATE DATABASE linx
GO

USE linx
GO

-- Users
CREATE TABLE users (
    id INT IDENTITY(1, 1) NOT NULL,
    username NVARCHAR(256) NOT NULL,
    password NVARCHAR(256) NOT NULL,
    CONSTRAINT pk_users PRIMARY KEY CLUSTERED (id ASC)
)
GO

-- Links
CREATE TABLE links (
    id INT IDENTITY(1, 1) NOT NULL,
    title NVARCHAR(256) NOT NULL,
    url NVARCHAR(256) NOT NULL,
    abstract NVARCHAR(512) NULL,
    tags NVARCHAR(256) NULL,
    user_id int NOT NULL,
    CONSTRAINT pk_links PRIMARY KEY CLUSTERED (id ASC)
)
GO

ALTER TABLE links WITH CHECK ADD CONSTRAINT fk_links_user_id
FOREIGN KEY (user_id) REFERENCES users (id)
GO

-- Tags
CREATE TABLE tags (
    id INT IDENTITY(1, 1) NOT NULL,
    tag NVARCHAR(50) NOT NULL,
    user_id int NOT NULL,
    CONSTRAINT pk_tags PRIMARY KEY CLUSTERED (id ASC)
)
GO

ALTER TABLE tags WITH CHECK ADD CONSTRAINT fk_tags_user_id
FOREIGN KEY (user_id) REFERENCES users (id)
GO

-- Tag/Link association
CREATE TABLE tags_links (
    tag_id int NOT NULL,
    link_id int NOT NULL,
    CONSTRAINT pk_tags_links PRIMARY KEY CLUSTERED (tag_id ASC, link_id ASC)
)
GO

ALTER TABLE tags_links WITH CHECK ADD CONSTRAINT fk_tags_links_tag_id
FOREIGN KEY (tag_id) REFERENCES tags (id)
ALTER TABLE tags_links WITH CHECK ADD CONSTRAINT fk_tags_links_link_id
FOREIGN KEY (link_id) REFERENCES links (id)
GO

-- Update display tags fields in link records after tag association added/removed
CREATE TRIGGER update_display_tags_delete
ON tags_links
FOR INSERT, DELETE
AS
BEGIN
    DECLARE @Delete BIT = CASE WHEN (SELECT COUNT(*) FROM DELETED) > 0 THEN 1 ELSE 0 END
    DECLARE @Insert BIT = CASE WHEN (SELECT COUNT(*) FROM INSERTED) > 0 THEN 1 ELSE 0 END

    DECLARE @LinkID INT = CASE WHEN @Delete = 1 THEN (SELECT TOP 1 link_id FROM DELETED) ELSE (SELECT TOP 1 link_id FROM INSERTED) END

	UPDATE 
		links 
	SET 
		tags = (
			SELECT STUFF((SELECT '|' + tag
							FROM tags
							INNER JOIN tags_links ON tags_links.tag_id = tags.id
							WHERE tags_links.link_id = @LinkID
							FOR XML PATH ('')), 1, 1, '') 
		) 
	WHERE 
		id = @LinkID
END
GO

-- Insert test user
INSERT INTO users
    (username, password)
VALUES
    ('me@markashleybell.com', '$6$rounds=100000$WFAb1fBhbTt5G9hF$uWKzu5Y2mwIG4myHU9fBp3uKcYOHebWJNtNEbtUV7aDpB6AYcZ3cXnSBT8S9N5X5qL/5SgFk2MFRUhEE6s.1q/')
GO
