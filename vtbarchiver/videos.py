# -*- coding: utf-8 -*-

import datetime
import urllib.parse
from math import ceil

from flask import (Blueprint, current_app, flash, g, jsonify, redirect,
                   render_template, request, url_for)

from vtbarchiver.db_functions import (find_common_items, find_tags,
                                      full_text_search, get_db,
                                      time_range_filter)
from vtbarchiver.local_file_management import get_relpath_to_static
from vtbarchiver.management import api_login_required, login_required
from vtbarchiver.misc_funcs import Pagination, tag_title

bp = Blueprint('videos', __name__, url_prefix='/videos')


@bp.route('/', defaults={'page': 1})
@bp.route('/page/<int:page>')
def videos(page): 
    db = get_db()
    try: 
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) video_num FROM video_list")
        video_num = cur.fetchone()['video_num']
        page_entry_num = 10
        page_num = max(ceil(video_num/page_entry_num), 1)
        cur.execute(
            '''
            SELECT vl.video_id video_id, vl.title title, vl.upload_date upload_date, vl.duration duration, vl.thumb_url thumb_url, lv.id local_id, ch.channel_name channel_name
            FROM video_list vl
            LEFT OUTER JOIN local_videos lv
            ON vl.video_id = lv.video_id
            JOIN channel_list ch
            ON vl.channel_id = ch.channel_id
            ORDER BY vl.upload_date DESC
            LIMIT ? OFFSET ?
            ''', 
            (page_entry_num, (page-1)*page_entry_num)
        )
        videos_on_page = cur.fetchall()
        pagination = Pagination(current_page=page, page_num=page_num, pagination_length=5)
        pagination.links = [url_for('videos.videos', page=i) for i in pagination.list]
        pagination.first_link = url_for('videos.videos', page=1)
        pagination.last_link = url_for('videos.videos', page=page_num)
        return render_template('videos/videos.html', page_num=page_num, pagination = pagination, videos_on_page=videos_on_page)
    finally: 
        cur.close()


def build_video_detail(title: str='', upload_date: str='', duration: str='', upload_index: int=0, thumb_url: str='', local_path: str='', video_id: str='', channel_id: str='', channel_name: str='', talent_names: list=[], stream_types: list=[]): 
    return {
        'title': title,
        'uploadDate': upload_date,
        'duration': duration,
        'uploadIndex': upload_index, 
        'thumbUrl': thumb_url,
        'localPath': local_path,
        'videoId': video_id,
        'channelId': channel_id, 
        'channelName': channel_name, 
        'talentNames': talent_names, 
        'streamTypes': stream_types
    }


def single_video(video_id): 
    db = get_db()
    cursor = db.cursor()
    video_detail = build_video_detail()
    try: 
        cursor.execute(
            '''
            SELECT vl.video_id video_id, vl.title title, vl.channel_id channel_id, vl.upload_date upload_date, vl.duration duration, vl.thumb_url thumb_url, ch.channel_name channel_name
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
        participators = [i['talent_name'] for i in participator_list]

        cursor.execute('SELECT stream_type FROM stream_type WHERE video_id = ?', (video_id, ))
        stream_type_list = cursor.fetchall()
        stream_types = [i['stream_type'] for i in stream_type_list]

        video_detail = build_video_detail(**video_info, local_path=video_relpath, talent_names=participators, stream_types=stream_types)
    finally: 
        cursor.close()
        return video_detail


@bp.route('/<video_id>/add-talent', methods=('POST', 'GET'))
@api_login_required
def add_talent(video_id): 
    if request.method == 'POST': 
        
        talent_list = request.form['talents'].strip().split(',')
        
        db = get_db()
        cur = db.cursor()
        try: 
            cur.execute('DELETE FROM talent_participation WHERE video_id=?', (video_id, ))
            for talent_name in talent_list: 
                cur.execute('INSERT INTO talent_participation (talent_name, video_id) VALUES (?, ?)', (talent_name.strip(), video_id))
            cur.execute('UPDATE search_video SET talents=? WHERE video_id=?', (';'.join(talent_list), video_id))
            db.commit()
        finally:
            cur.close()
        
        return jsonify({
            'type': '200', 
            'result': 'success', 
            'message': 'talents has been added', 
        })
    else: 
        return jsonify({
            'type': '500', 
            'result': 'fail', 
            'message': 'internal error'
        })


@bp.route('/<video_id>/add-stream-type', methods=('POST', 'GET'))
@api_login_required
def add_stream_type(video_id): 
    if request.method == 'POST': 
        
        stream_type_list = request.form['stream_type'].strip().split(',')
        
        db = get_db()
        cur = db.cursor()
        try: 
            cur.execute('DELETE FROM stream_type WHERE video_id=?', (video_id, ))
            for stream_type in stream_type_list: 
                cur.execute('INSERT INTO stream_type (stream_type, video_id) VALUES (?, ?)', (stream_type.strip(), video_id))
            cur.execute('UPDATE search_video SET stream_type=? WHERE video_id=?', (';'.join(stream_type_list), video_id))
            db.commit()
        finally:
            cur.close()
        
        return jsonify({
            'type': '200', 
            'result': 'success', 
            'message': 'tags has been added', 
        })
    else: 
        return jsonify({
            'type': '500', 
            'result': 'fail', 
            'message': 'internal error'
        })


@bp.route('/search')
def search_video(): 
    page = request.args.get('page', 1, type=int)
    talent_str = request.args.get('talents', '')
    tag_str = request.args.get('tags', '')
    time_range_str = request.args.get('time-range', '')
    talent_list = [i.strip() for i in talent_str.strip().split(',')]
    tag_list = [i.strip() for i in tag_str.strip().split(',')]
    time_range = time_range_str.split(';')
    search_keys = request.args.get('search-keys', '')
    time_descending_str = request.args.get('time-descending', 'false')
    if time_descending_str == 'true': 
        time_descending = True
    else: 
        time_descending = False
    page_entry_num = 10
    

    if not (search_keys or talent_str or tag_str or time_range_str): 
        return redirect(url_for('videos.videos'))

    list_for_reduction = []
    if talent_str: 
        talent_result = find_tags('talent_participation', 'talent_name', talent_list)
        list_for_reduction.append(talent_result)
    if tag_str: 
        tag_result = find_tags('stream_type', 'stream_type', tag_list)
        list_for_reduction.append(tag_result)
    if search_keys: 
        tagged_keys = tag_title(search_keys)
        tagged_search_result = full_text_search('search_video', tagged_keys)
        search_result = full_text_search('search_video', search_keys)
        combined_search_result = list(set(tagged_search_result + search_result))
        list_for_reduction.append(combined_search_result)
    if time_range_str: 
        time_range_result = time_range_filter(*time_range)
        list_for_reduction.append(time_range_result)
    reduced_result = find_common_items(*list_for_reduction)
    page_num = max(ceil(len(reduced_result)/page_entry_num), 1)
    if not time_descending: 
        video_id_for_query = reduced_result[(page-1)*page_entry_num:page*page_entry_num]
    else: 
        video_id_for_query = reduced_result[:]

    db = get_db()
    cur = db.cursor()
    videos_query_result = []
    try: 
        for video_id in video_id_for_query: 
            cur.execute(
                '''
                SELECT vl.video_id video_id, vl.title title, vl.upload_date upload_date, vl.duration duration, vl.thumb_url thumb_url, lv.id local_id, ch.channel_name channel_name
                FROM video_list vl
                LEFT OUTER JOIN local_videos lv
                ON vl.video_id = lv.video_id
                JOIN channel_list ch
                ON vl.channel_id = ch.channel_id
                WHERE vl.video_id = ?
                ''', (video_id, )
            )
            videos_query_result.append(cur.fetchone())

        if time_descending: 
            videos_on_page = sorted(videos_query_result, key=lambda single_video_obj: single_video_obj['upload_date'], reverse=True)[(page-1)*page_entry_num:page*page_entry_num]
        else: 
            videos_on_page = videos_query_result


        pagination_params = {
            'talents': talent_str, 
            'tags': tag_str, 
            'search-keys': search_keys, 
            'time-range': time_range_str,
            'page': page, 
            'time-descending': str(time_descending).lower()
        }
        pagination = Pagination(current_page=page, page_num=page_num, pagination_length=5)
        for each_page in pagination.list: 
            pagination_params['page'] = each_page
            pagination.links.append(url_for('videos.search_video')+'?'+urllib.parse.urlencode(pagination_params))
        
        pagination_params['page']=1
        pagination.first_link = url_for('videos.search_video')+'?'+urllib.parse.urlencode(pagination_params)
        pagination_params['page']=page_num
        pagination.last_link = url_for('videos.search_video')+'?'+urllib.parse.urlencode(pagination_params)

        return render_template('videos/videos.html', page_num=page_num, pagination = pagination, videos_on_page=videos_on_page)
    finally:
        cur.close()

