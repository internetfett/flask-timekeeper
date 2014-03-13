drop table if exists project;
create table project (
  id integer primary key autoincrement,
  name text not null,
  description text
);

drop table if exists timekeeper;
create table timekeeper (
  id integer primary key autoincrement,
  project_id integer not null,
  start_date timestamp not null,
  stop_date timestamp,
  description text,
  foreign key(project_id) references project(id)
);