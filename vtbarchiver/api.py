# -*- coding: utf-8 -*-

from flask import Blueprint, current_app, g, jsonify, request

from vtbarchiver.db_functions import (ChannelStats, get_db, get_new_hex_vid,
                                      tag_suggestions)
from vtbarchiver.management import login_required
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
def manually_add_video(): 
    if (g.user is None) or request.method == 'GET': 
        return jsonify({'400': 'bad request'})
    if request.method == 'POST': 
        
        db = get_db()
        cur = db.cursor()
        try: 
            cur.execute('SELECT video_id FROM video_list WHERE video_id=?', (request.form['video_id'],))
            existed_video_list = cur.fetchall()
            if existed_video_list: 
                return jsonify({'error': 'video existed'})
            
            # get video info from youtube
            if request.form['unarchive_check'] == 'false': 
                youtube = build_youtube_api()
                video_info_request = youtube.videos().list(
                    part="snippet,contentDetails", 
                    id=request.form['video_id']
                )
                video_info_response = video_info_request.excute()
                if not video_info_response['items']: 
                    return jsonify({'error': 'No such video ID'})
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
            # regenerate upload_idx
            cur.execute('SELECT id FROM video_list WHERE channel_id=? ORDER BY upload_date', (request.form['channel_id'], ))
            id_by_date = cur.fetchall()
            for upload_idx in range(len(id_by_date)): 
                cur.execute('UPDATE video_list SET upload_idx=? WHERE id=?', (upload_idx+1, id_by_date[upload_idx][0]))
            db.commit()
            return jsonify({'success': '%s has been added' % request.form['channel_id']})
        finally: 
            cur.close()
