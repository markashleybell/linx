delete from tags_links;
delete from tags;
delete from links;
alter sequence tags_id_seq restart with 1;
alter sequence links_id_seq restart with 1;

--drop table tags_links;
--drop table tags;
--drop table links;