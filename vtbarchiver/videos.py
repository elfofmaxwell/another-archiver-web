# -*- coding: utf-8 -*-

from math import ceil

from flask import (current_app, g, Blueprint, flash, redirect, render_template, request, url_for)

from vtbarchiver.db_functions import get_db
from vtbarchiver.management import login_required
from vtbarchiver.local_file_management import get_relpath_to_static

bp = Blueprint('videos', __name__, url_prefix='/videos')


@bp.route('/', defaults={'page': 1})
@bp.route('/page/<int:page>')
def videos(page): 
    db = get_db()
    try: 
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) video_num FROM video_list")
        video_num = cur.fetchone()['video_num']
        page_entry_num = 5
        page_num = ceil(video_num/page_entry_num)
        cur.execute(
            '''
            SELECT vl.video_id video_id, vl.title title, vl.upload_date upload_date, vl.thumb_url thumb_url, lv.id local_id, ch.channel_name channel_name
            FROM video_list vl
            LEFT OUTER JOIN local_videos lv
            ON vl.video_id = lv.video_id
            JOIN channel_list ch
            ON vl.channel_id = ch.channel_id
            ORDER BY vl.upload_date DESC
            LIMIT ? OFFSET ?
            ''', 
            (page_entry_num, (page-1)*page_num)
        )
        videos_on_page = cur.fetchall()

        return render_template('videos/videos.html', page_num=page_num, videos_on_page=videos_on_page)
    finally: 
        cur.close()


@bp.route('/<video_id>')
def single_video(video_id): 
    db = get_db()
    cursor = db.cursor()
    try: 
        cursor.execute(
            '''
            SELECT vl.video_id video_id, vl.title title, vl.channel_id channel_id, vl.upload_date upload_date, vl.thumb_url video_thumb, ch.channel_name channel_name
            FROM video_list vl 
            JOIN channel_list ch
            ON vl.channel_id = ch.channel_id
            WHERE vl.video_id = ?
            ''', 
            (video_id, )
        )
        video_info = cursor.fetchone()
        cursor.execute('SELECT video_path, thumb_path FROM local_videos WHERE video_id=?', (video_id, ))
        local_video_info = cursor.fetchone()
        video_relpath = ''
        if local_video_info: 
            video_relpath = get_relpath_to_static(local_video_info['video_path'])
        cursor.execute('SELECT talent_name FROM talent_participation WHERE video_id = ?', (video_id, ))
        participator_list = cursor.fetchall()
        participators = ','.join([i['talent_name'] for i in participator_list])

        cursor.execute('SELECT stream_type FROM stream_type WHERE video_id = ?', (video_id, ))
        stream_type_list = cursor.fetchall()
        stream_type = ','.join([i['stream_type'] for i in stream_type_list])

        return render_template('videos/single_video.html', video_info=video_info, video_relpath=video_relpath, participators=participators, stream_type=stream_type)
    finally: 
        cursor.close()


@bp.route('/<video_id>/add-talent', methods=('POST', 'GET'))
@login_required
def add_talent(video_id): 
    if request.method == 'POST': 
        
        talent_list = request.form['talents'].strip().split(',')
        
        db = get_db()
        cur = db.cursor()
        try: 
            cur.execute('DELETE FROM talent_participation WHERE video_id=?', (video_id, ))
            for talent_name in talent_list: 
                cur.execute('INSERT INTO talent_participation (talent_name, video_id) VALUES (?, ?)', (talent_name.strip(), video_id))
            db.commit()
        finally:
            cur.close()
        
    return redirect(url_for('videos.single_video', video_id=video_id))


@bp.route('/<video_id>/add-stream-type', methods=('POST', 'GET'))
@login_required
def add_stream_type(video_id): 
    if request.method == 'POST': 
        
        stream_type_list = request.form['stream_type'].strip().split(',')
        
        db = get_db()
        cur = db.cursor()
        try: 
            cur.execute('DELETE FROM stream_type WHERE video_id=?', (video_id, ))
            for stream_type in stream_type_list: 
                cur.execute('INSERT INTO stream_type (stream_type, video_id) VALUES (?, ?)', (stream_type.strip(), video_id))
            db.commit()
        finally:
            cur.close()
        
    return redirect(url_for('videos.single_video', video_id=video_id))