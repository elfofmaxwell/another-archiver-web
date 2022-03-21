DROP TABLE IF EXISTS channel_list;
DROP TABLE IF EXISTS video_list;
DROP TABLE IF EXISTS talent_participation;
DROP TABLE IF EXISTS stream_type;
DROP TABLE IF EXISTS local_videos;
DROP TABLE IF EXISTS admin_list;

CREATE TABLE channel_list (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
    channel_id TEXT NOT NULL UNIQUE, 
    channel_name TEXT NOT NULL, 
    talent_name TEXT NOT NULL DEFAULT '', 
    channel_description TEXT NOT NULL, 
    thumb_url TEXT NOT NULL, 
    checkpoint_idx INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE video_list (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
    video_id TEXT NOT NULL UNIQUE, 
    title TEXT NOT NULL, 
    upload_date TEXT NOT NULL, 
    duration TEXT NOT NULL, 
    channel_id TEXT NOT NULL, 
    upload_idx INTEGER NOT NULL DEFAULT 0, 
    thumb_url TEXT NOT NULL
);


CREATE TABLE talent_participation (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
    talent_name TEXT NOT NULL, 
    video_id TEXT NOT NULL
); 


CREATE TABLE stream_type (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
    stream_type TEXT NOT NULL, 
    video_id TEXT NOT NULL
); 


CREATE TABLE local_videos (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
    video_id TEXT NOT NULL UNIQUE, 
    video_path TEXT NOT NULL, 
    thumb_path TEXT NOT NULL DEFAULT ''
);

CREATE TABLE admin_list (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
    username TEXT UNIQUE NOT NULL, 
    passwd_hash TEXT NOT NULL
);
