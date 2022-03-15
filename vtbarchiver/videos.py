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
            SELECT vl.video_id video_id, vl.title title, vl.upload_date upload_date, vl.thumb_url thumb_url, vl.talents talents, lv.id local_id, ch.channel_name channel_name
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
    try: 
        cursor = db.cursor()
        cursor.execute(
            '''
            SELECT vl.video_id video_id, vl.title title, vl.channel_id channel_id, vl.upload_date upload_date, vl.thumb_url video_thumb, vl.talents talents, ch.channel_name channel_name
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

        return render_template('videos/single_video.html', video_info=video_info, video_relpath=video_relpath)
    finally: 
        cursor.close()


@bp.route('/<video_id>/add-talent', methods=('POST', 'GET'))
@login_required
def add_talent(video_id): 
    if request.method == 'POST': 
        db = get_db()
        try: 
            cur = db.cursor()
            cur.execute('UPDATE video_list SET talents=? WHERE video_id=?', (request.form['talents'].strip(), video_id))
            db.commit()
        finally:
            cur.close()
    return redirect(url_for('videos.single_video', video_id=video_id))

