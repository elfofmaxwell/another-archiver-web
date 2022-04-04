# -*- coding: utf-8 -*-

import os
import subprocess

from flask import Blueprint, current_app, g, jsonify, request

from vtbarchiver.db_functions import (ChannelStats, get_db, get_new_hex_vid,
                                      regenerate_upload_index, tag_suggestions)
from vtbarchiver.download_functions import check_lock
from vtbarchiver.management import api_login_required, login_required
from vtbarchiver.misc_funcs import build_youtube_api, tag_title

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/get-tag-suggestion')
def get_tag_suggestion(): 
    tag_type = request.args.get('tag-type', '')
    query_str = request.args.get('query-str', '')
    return jsonify(suggestions=tag_suggestions(tag_type, query_str))


@bp.route('/channel-stats')
def channel_stats(): 
    channel_stat_results = {}

    channel_id = request.args.get('channel-id', '')
    stats_type = request.args.get('stats-type', '')
    lower_date_stamp = request.args.get('lower-date-stamp', '')
    upper_date_stamp = request.args.get('upper-date-stamp', '')
    try: 
        time_delta = request.args.get('time-delta', 0, type=int) 
    except: 
        return jsonify(channel_stat_results)

    db = get_db()
    cur = db.cursor()

    try: 
        if channel_id: 
            cur.execute('SELECT COUNT(*) num FROM channel_list WHERE channel_id=?', (channel_id, ))
            if cur.fetchone()['num'] == 0: 
                return jsonify(channel_stat_results)
            
            channel_obj = ChannelStats(channel_id)

            if stats_type == "talents-stats" or stats_type == "all": 
                channel_stat_results['talent_stats'] = channel_obj.talents_stats(time_delta, lower_date_stamp, upper_date_stamp)
            
            if stats_type == "tag-stats" or stats_type == "all": 
                channel_stat_results['tag_stats'] = channel_obj.tag_stats(time_delta, lower_date_stamp, upper_date_stamp)
            
            if stats_type == "duration-stats" or stats_type == "all": 
                channel_stat_results['duration_stats'] = channel_obj.duration_stats(time_delta, lower_date_stamp, upper_date_stamp)

            if stats_type == "duration-distr" or stats_type == "all": 
                channel_stat_results['duration_distr'] = channel_obj.duration_distr(time_delta, lower_date_stamp, upper_date_stamp)

            if stats_type == "video-num-stats" or stats_type == "all": 
                channel_stat_results["video_num_stats"] = channel_obj.video_num_stats(time_delta, lower_date_stamp, upper_date_stamp)

        return jsonify(channel_stat_results)
    finally: 
        cur.close()


@bp.route('/get-new-hex-vid')
def new_hex_vid():
    return jsonify(new_hex_vid=get_new_hex_vid())


@bp.route('/manually-add-video', methods=("POST", 'GET'))
@api_login_required
def manually_add_video(): 
    if request.method == 'GET': 
        return jsonify({'type': '400', 'result': 'fail', 'message': 'bad request'})
    if request.method == 'POST': 
        
        db = get_db()
        cur = db.cursor()
        try: 
            cur.execute('SELECT video_id FROM video_list WHERE video_id=?', (request.form['video_id'],))
            existed_video_list = cur.fetchall()
            if existed_video_list: 
                return jsonify({'type': '400', 'result': 'fail', 'message': 'video existed'})
            
            # get video info from youtube
            if request.form['unarchive_check'] == 'false': 
                youtube = build_youtube_api()
                video_info_request = youtube.videos().list(
                    part="snippet,contentDetails", 
                    id=request.form['video_id']
                )
                video_info_response = video_info_request.excute()
                if not video_info_response['items']: 
                    return jsonify({'type': '400', 'result': 'fail', 'message': 'No such video ID'})
                title = video_info_response['items'][0]['snippet']['title']
                upload_date = video_info_response['items'][0]['snippet']['publishedAt']
                duration = video_info_response['items'][0]['contentDetails']['duration']
                thumb_url = video_info_response['items'][0]['snippet']['thumbnails']['high']['url']
            # use video info from form 
            else: 
                title = request.form['title']
                upload_date = request.form['upload_date']
                duration = request.form['duration']
                thumb_url = request.form['thumb_url']
            # insert into video_list
            cur.execute(
                'INSERT INTO video_list (video_id, title, upload_date, duration, channel_id, thumb_url) VALUES (?, ?, ?, ?, ?, ?)', 
                (request.form['video_id'], title, upload_date, duration, request.form['channel_id'], thumb_url)
            )
            # insert into talent_participation and stream_type
            tagged_title = tag_title(title)
            talent_names = request.form['talent_names'].strip().split(',')
            stream_types = request.form['stream_types'].strip().split(',')
            for talent_name in talent_names: 
                cur.execute('INSERT INTO talent_participation (talent_name, video_id) VALUES (?, ?)', (talent_name.strip(), request.form['video_id']))
            for stream_type in stream_types: 
                cur.execute('INSERT INTO stream_type (stream_type, video_id) VALUES (?, ?)', (stream_type.strip(), request.form['video_id']))
            # insert into search_video
            cur.execute(
                'INSERT INTO search_video (video_id, title, tagged_title, talents, stream_type) VALUES (?, ?, ?, ?, ?)', 
                (request.form['video_id'], title, tagged_title, ';'.join(talent_names), ';'.join(stream_types))
            )
            db.commit()
            # regenerate upload_idx
            regenerate_upload_index(request.form['channel_id'])
            return jsonify({'type': '200', 'result': 'success', 'message': '%s has been added' % request.form['channel_id']})
        finally: 
            cur.close()


@bp.route('/<video_id>/manually-update-video', methods=("POST", 'GET'))
@api_login_required
def manually_update_video(video_id): 
    if request.method == 'GET': 
        return jsonify({'type': '400', 'result': 'fail', 'message': 'bad request'})
    if request.method == 'POST': 

        db = get_db()
        cur = db.cursor()
        try: 
            cur.execute("SELECT title, upload_date, duration, channel_id, thumb_url FROM video_list WHERE video_id=?", (video_id, ))
            old_video_obj = cur.fetchone()
            new_video_info = {
                'title': old_video_obj['title'],
                'upload_date': old_video_obj['upload_date'], 
                'duration': old_video_obj['duration'],
                'channel_id': old_video_obj['channel_id'], 
                'thumb_url': old_video_obj['thumb_url'],
            }
            for k, v in request.form.items(): 
                if v: 
                    new_video_info[k] = v
            cur.execute(
                'UPDATE video_list SET title=?, upload_date=?, duration=?, channel_id=?, thumb_url=? WHERE video_id=?', 
                (new_video_info['title'], new_video_info['upload_date'], new_video_info['duration'], new_video_info['channel_id'], new_video_info['thumb_url'], video_id)
            )
            tagged_title = tag_title(new_video_info['title'])
            cur.execute(
                'UPDATE search_video SET title=?, tagged_title=? WHERE video_id=?', 
                (new_video_info['title'], tagged_title, video_id)
            )
            db.commit()
            regenerate_upload_index(new_video_info['channel_id'])
            return jsonify({'type': '200', 'result': 'success', 'message': '%s has been updated' % video_id})
        finally:
            cur.close()
        

@bp.route('/<video_id>/delete-video')
@api_login_required
def delete_video(video_id):
    db = get_db()
    cur = db.cursor()
    try: 
        cur.execute('SELECT channel_id FROM video_list WHERE video_id=?', (video_id, ))
        channel_id = cur.fetchone()['channel_id']
        cur.execute('DELETE FROM video_list WHERE video_id=?', (video_id, ))
        cur.execute('DELETE FROM talent_participation WHERE video_id=?', (video_id, ))
        cur.execute('DELETE FROM stream_type WHERE video_id=?', (video_id, ))
        cur.execute('DELETE FROM search_video WHERE video_id=?', (video_id, ))
        cur.execute('DELETE FROM local_videos WHERE video_id=?', (video_id, ))
        db.commit()
        regenerate_upload_index(channel_id)
        return jsonify({'type': '200', 'result': 'success', 'message': '%s has been deleted'%video_id})
    finally: 
        cur.close()


@bp.route('/downloading')
@api_login_required
def check_downloading(): 
    if check_lock(): 
        return jsonify({'type': '200', 'result': 'success', 'message': 'downloading'})
    else: 
        return jsonify({'type': '200', 'result': 'success', 'message': 'free'})


@bp.route('<video_id>/download')
@api_login_required
def download_single_video(video_id):
    downloader_args = ['flask', 'download-single', '--video_id', video_id]
    subprocess.Popen(downloader_args, env=os.environ.copy())
    return jsonify({'type': '200', 'result': 'success', 'message': 'downloading'})
