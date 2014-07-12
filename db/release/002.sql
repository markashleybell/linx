-- Users
CREATE TABLE users
(
  id serial NOT NULL,
  username character varying(256) NOT NULL,
  password character varying(256) NOT NULL,
  CONSTRAINT pk_users PRIMARY KEY (id)
)
WITH (OIDS=FALSE);

ALTER TABLE users OWNER TO postgres;

-- Insert new user record - this is not my real password :)
INSERT INTO users
    (id, username, password)
VALUES
    (1, 'me@markashleybell.com', '$6$rounds=100000$WFAb1fBhbTt5G9hF$uWKzu5Y2mwIG4myHU9fBp3uKcYOHebWJNtNEbtUV7aDpB6AYcZ3cXnSBT8S9N5X5qL/5SgFk2MFRUhEE6s.1q/');

-- Add foreign keys to links and tags tables
ALTER TABLE links 
    ADD COLUMN user_id int references users(id);

ALTER TABLE tags
    ADD COLUMN user_id int references users(id);

-- Associate all existing records with new user record
UPDATE links SET user_id = 1;
UPDATE tags SET user_id = 1;

-- Make foreign key columns non-nullable
ALTER TABLE links 
    ALTER COLUMN user_id SET NOT NULL;

ALTER TABLE tags 
    ALTER COLUMN user_id SET NOT NULL;