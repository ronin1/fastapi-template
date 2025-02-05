-- setup a single table to track match results

create table if not exists color_matches (
    id serial primary key,
    usr varchar(64) not null,
    run varchar(64) not null,
    input text not null,
    body jsonb not null
);

create index if not exists color_matches_usr_idx on color_matches (usr);

create index if not exists color_matches_run_idx on color_matches (run);