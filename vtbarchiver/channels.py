# -*- coding: utf-8 -*-

from math import ceil

from flask import (Blueprint, current_app, flash, g, jsonify, redirect,
                   render_template, request, url_for)

from vtbarchiver.channel_records import fetch_channel, update_checkpoint
from vtbarchiver.db_functions import get_db
from vtbarchiver.fetch_video_list import add_talent_name as add_name
from vtbarchiver.fetch_video_list import fetch_all, fetch_uploaded_list
from vtbarchiver.management import login_required
from vtbarchiver.misc_funcs import Pagination

bp = Blueprint('channels', __name__, url_prefix='/channels')


# get channels
def get_channels(): 
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT channel_id, channel_name, thumb_url FROM channel_list')
    channel_list = cur.fetchall()
    return channel_list


# add channel
def add_channel(new_channel_id): 
    new_channel_overview = fetch_channel(new_channel_id)
    if new_channel_overview['channelId']: 
        fetch_uploaded_list(new_channel_id)
    return new_channel_overview


# single channel detail
def build_channel_detail(channel_id: str = '', channel_name: str = '', thumb_url: str = '', talent_name: str = '', video_num: int = 0, checkpoint_idx: int = 0): 
    return {
        'channelId': channel_id,
        'channelName': channel_name,
        'thumbUrl': thumb_url,
        'talentName': talent_name,
        'videoNum': video_num,
        'checkpointIndex': checkpoint_idx,
    }

def single_channel_detail(channel_id=''): 
    channel_detail = build_channel_detail()
    db = get_db()
    cur = db.cursor()
    try: 
        if channel_id: 
            cur.execute("SELECT * FROM channel_list WHERE channel_id = ?", (channel_id, ))
            channel_info = cur.fetchone()
            if channel_info: 
                channel_detail['channelId'] = channel_info['channel_id']
                channel_detail['channelName'] = channel_info['channel_name']
                channel_detail['thumbUrl'] = channel_info['thumb_url']
                channel_detail['talentName'] = channel_info['talent_name']
                channel_detail['checkpointIndex'] = channel_info['checkpoint_idx']
                cur.execute("SELECT COUNT(*) video_num FROM video_list WHERE channel_id = ?", (channel_id, ))
                channel_detail['videoNum'] = cur.fetchone()['video_num']
        return channel_detail
    finally: 
        cur.close()


def build_video_overview(title: str='', uploadDate: str='', duration: str='', uploadIndex: int=0, thumbUrl: str='', local_path: str=''): 
    return {
        'title': title,
        'uploadDate': uploadDate,
        'duration': duration,
        'uploadIndex': uploadIndex, 
        'thumbUrl': thumbUrl,
        'localPath': local_path,
    }


def single_channel_videos(channel_id: str, page=1, page_entry_num=5): 
    db = get_db()
    cur = db.cursor()
    channel_video_list = []
    try: 
        cur.execute("SELECT COUNT(*) video_num FROM video_list WHERE channel_id = ?", (channel_id, ))
        video_num = cur.fetchone()['video_num']
        page_num = max(ceil(video_num/page_entry_num), 1)
        cur.execute(
            '''
            SELECT vl.video_id video_id, vl.title title, vl.upload_date upload_date, vl.duration duration, vl.thumb_url thumb_url, vl.upload_idx upload_idx, lv.id local_id
            FROM video_list vl
            LEFT OUTER JOIN local_videos lv
            ON vl.video_id = lv.video_id
            WHERE vl.channel_id = ? 
            ORDER BY vl.upload_idx DESC
            LIMIT ? OFFSET ?
            ''', 
            (channel_id, page_entry_num, (page-1)*page_entry_num)
        )
        videos_on_page = cur.fetchall()

        if videos_on_page: 
            for video in videos_on_page: 
                channel_video_list.append(build_video_overview(video['title'], video['upload_date'], video['duration'], video['upload_idx'], video['thumb_url'], video['local_id']))
        return video_num, channel_video_list
    finally: 
        cur.close()
        

# single channel page
@bp.route('/<channel_id>/', defaults={'page': 1})
@bp.route('/<channel_id>/page/<int:page>')
def single_channel(channel_id, page): 
    db = get_db()
    try: 
        cur = db.cursor()
        cur.execute("SELECT * FROM channel_list WHERE channel_id = ?", (channel_id, ))
        channel_info = cur.fetchone()

        cur.execute("SELECT COUNT(*) video_num FROM video_list WHERE channel_id = ?", (channel_id, ))
        video_num = cur.fetchone()['video_num']
        page_entry_num = 5
        page_num = max(ceil(video_num/page_entry_num), 1)
        cur.execute(
            '''
            SELECT vl.video_id video_id, vl.title title, vl.upload_date upload_date, vl.duration duration, vl.thumb_url thumb_url, vl.upload_idx upload_idx, lv.id local_id
            FROM video_list vl
            LEFT OUTER JOIN local_videos lv
            ON vl.video_id = lv.video_id
            WHERE vl.channel_id = ? 
            ORDER BY vl.upload_idx DESC
            LIMIT ? OFFSET ?
            ''', 
            (channel_id, page_entry_num, (page-1)*page_entry_num)
        )
        videos_on_page = cur.fetchall()
        pagination = Pagination(current_page=page, page_num=page_num, pagination_length=5)
        pagination.links = [url_for('channels.single_channel', channel_id=channel_id, page=i) for i in pagination.list]
        return render_template('channels/single_channel.html', channel_info=channel_info, page_num=page_num, pagination = pagination, video_num=video_num, videos_on_page=videos_on_page)
    finally: 
        cur.close()


# edit checkpoint
def edit_checkpoint(channel_id: str, checkpoint_idx: int, video_id: str, offset: int): 
    '''
    args: channel_id (str); checkpoint_idx (int, key arg, optional); video_id(str, key arg, optional); offset (int, key arg, optional)
    move checkpoint for a given channel. Priority: checkpoint_idx > video_id > offset
    '''
    if (not checkpoint_idx) and (not video_id) and (not offset): 
        return -1

    db = get_db()
    cur = db.cursor()
    try: 

        if checkpoint_idx>0: 
            new_checkpoint_idx = int(checkpoint_idx)

        elif video_id: 
            cur.execute('SELECT upload_idx FROM video_list WHERE video_id=?', (video_id,))
            upload_idx_searching = cur.fetchall()
            if not upload_idx_searching: 
                return -1
            new_checkpoint_idx = upload_idx_searching[0][0]

        elif offset: 
            cur.execute('SELECT checkpoint_idx FROM channel_list WHERE channel_id=?', (channel_id,))
            old_checkpoint = cur.fetchall()[0][0]
            new_checkpoint_idx = int(old_checkpoint) + int(offset)
            if new_checkpoint_idx < 0: 
                return -1

        cur.execute('UPDATE channel_list SET checkpoint_idx=? WHERE channel_id=?', (new_checkpoint_idx, channel_id))
        return cur.rowcount

    except: 
        raise

    finally: 
        cur.close()
        db.commit()


# edit talent name for a channel
def edit_talent(channel_id, talent_name): 
    db = get_db()
    try: 
        cur = db.cursor()
        cur.execute('UPDATE channel_list SET talent_name=? WHERE channel_id=?', (talent_name, channel_id))
        if cur.rowcount != 1: 
            return 1
        db.commit()
        return 0
    finally: 
        cur.close()


# delete channel
@bp.route('/<channel_id>/delete-channel')
@login_required
def delete_channel(channel_id): 
    print('Get delete signal: %s' % channel_id)
    db = get_db()
    cur = db.cursor()
    try: 
        cur.execute('SELECT video_id FROM video_list WHERE channel_id=?', (channel_id, ))
        video_id_list = [i['video_id'] for i in cur.fetchall()]
        for video_id in video_id_list: 
            cur.execute('DELETE FROM talent_participation WHERE video_id=?', (video_id, ))
            cur.execute('DELETE FROM stream_type WHERE video_id=?', (video_id, ))
            cur.execute('DELETE FROM local_videos WHERE video_id=?', (video_id, ))
            cur.execute('DELETE FROM video_list WHERE video_id=?', (video_id, ))
            cur.execute('DELETE FROM search_video WHERE video_id=?', (video_id, ))
        cur.execute('DELETE FROM channel_list WHERE channel_id=?', (channel_id, ))
        db.commit()
        return redirect(url_for('channels.channels'))
    finally: 
        cur.close()
