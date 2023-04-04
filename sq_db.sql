CREATE TABLE IF NOT EXISTS mainmenu (
id integer PRIMARY KEY AUTOINCREMENT,
title text NOT NULL,
url text NOT NULL
);

CREATE TABLE IF NOT EXISTS vacancy (
id integer PRIMARY KEY AUTOINCREMENT,
name text NOT NULL,
city text NOT NULL,
salary text NOT NULL,
schedule text NOT NULL,
description text NOT NULL,
time integer NOT NULL
);