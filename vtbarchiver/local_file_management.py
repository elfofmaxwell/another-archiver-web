# -*- coding: utf-8 -*-

import os

from flask import current_app, g

from vtbarchiver.db_functions import get_db

def scan_local_videos(video_dir): 
    db = get_db()
    cur = db.cursor()
    try: 
        for root_path, dir_names, file_names in os.walk(video_dir): 
            for file_name_full in file_names: 
                file_name, file_ext = os.path.splitext(file_name_full)
                if file_ext.lower() in ('.mp4', '.webm'): 
                    pseudo_vid = file_name[-12:-1]
                    print(pseudo_vid)
                    cur.execute('SELECT id FROM video_list WHERE video_id=?', (pseudo_vid, ))
                    if cur.fetchall(): 
                        video_id = pseudo_vid
                        video_path = os.path.join(root_path, file_name_full)
                        cur.execute(
                            """
                            INSERT INTO local_videos 
                            (video_id, video_path, thumb_path) VALUES (?, ?, '')
                            ON CONFLICT (video_id) 
                            DO UPDATE SET video_path=?
                            """, 
                            (video_id, video_path, video_path)
                        )
                        db.commit()
    finally: 
        cur.close()


def get_relpath_to_static(video_path): 
    static_path = os.path.join(os.path.abspath(current_app.root_path), 'static')
    return os.path.relpath(video_path, static_path)


