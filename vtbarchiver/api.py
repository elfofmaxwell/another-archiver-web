# -*- coding: utf-8 -*-

import os
import subprocess

from flask import Blueprint, abort, current_app, g, jsonify, request, session

from vtbarchiver.channels import (add_channel, edit_checkpoint, edit_talent,
                                  get_channels, single_channel_detail,
                                  single_channel_videos)
from vtbarchiver.db_functions import (ChannelStats, get_db, get_new_hex_vid,
                                      regenerate_upload_index, tag_suggestions)
from vtbarchiver.download_functions import check_lock
from vtbarchiver.fetch_video_list import add_talent_name, fetch_all
from vtbarchiver.management import (api_login_required, check_password_hash,
                                    login_required, try_login)
from vtbarchiver.misc_funcs import build_youtube_api, tag_title
from vtbarchiver.videos import build_video_detail, single_video

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.errorhandler(400)
def bad_request(e): 
    return jsonify({}), 400


@bp.route('/get-tag-suggestion')
def get_tag_suggestion(): 
    tag_type = request.args.get('tagType', '')
    query_str = request.args.get('queryStr', '')
    return jsonify(tag_suggestions(tag_type, query_str))


@bp.route('/channel-stats')
def channel_stats(): 
    channel_stat_results = {}

    channel_id = request.args.get('channelId', '')
    stats_type = request.args.get('statsType', '')
    lower_date_stamp = request.args.get('lowerDateStamp', '')
    upper_date_stamp = request.args.get('upperDateStamp', '')
    try: 
        time_delta = request.args.get('timeDelta', 0, type=int) 
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
                channel_stat_results['talentStats'] = channel_obj.talents_stats(time_delta, lower_date_stamp, upper_date_stamp)
            
            if stats_type == "tag-stats" or stats_type == "all": 
                channel_stat_results['tagStats'] = channel_obj.tag_stats(time_delta, lower_date_stamp, upper_date_stamp)
            
            if stats_type == "duration-stats" or stats_type == "all": 
                channel_stat_results['durationStats'] = channel_obj.duration_stats(time_delta, lower_date_stamp, upper_date_stamp)

            if stats_type == "duration-distr" or stats_type == "all": 
                channel_stat_results['durationDistr'] = channel_obj.duration_distr(time_delta, lower_date_stamp, upper_date_stamp)

            if stats_type == "video-num-stats" or stats_type == "all": 
                channel_stat_results["videoNumStats"] = channel_obj.video_num_stats(time_delta, lower_date_stamp, upper_date_stamp)

        return jsonify(channel_stat_results)
    finally: 
        cur.close()


@bp.route('/get-new-hex-vid')
@api_login_required
def new_hex_vid():
    return jsonify(get_new_hex_vid())


@bp.route('/manually-add-video', methods=("POST",))
@api_login_required
def manually_add_video(): 
    db = get_db()
    cur = db.cursor()
    video_id = request.json.get('videoId', '')
    title = request.json.get('title', '')
    upload_date = request.json.get('uploadDate', '')
    duration = request.json.get('duration', '')
    thumb_url = request.json.get('thumbUrl', '')
    channel_id = request.json.get('channelId', '')
    talent_names = request.json.get('talentNames', [])
    stream_types = request.json.get('streamTypes', [])
    unarchived_content = request.json.get('unarchivedContent', False)
    try: 
        cur.execute('SELECT video_id FROM video_list WHERE video_id=?', (video_id,))
        existed_video_list = cur.fetchall()
        if existed_video_list: 
            video_detail = single_video(video_id)
            video_detail['serverMessage'] = 'Video existed. '
            return jsonify(video_detail)
        
        # get video info from youtube
        if (not unarchived_content) and video_id: 
            youtube = build_youtube_api()
            video_info_request = youtube.videos().list(
                part="snippet,contentDetails", 
                id=video_id
            )
            video_info_response = video_info_request.excute()
            if not video_info_response['items']: 
                video_detail = build_video_detail()
                video_detail['serverMessage'] = 'Cannot find YouTube video with ID=%s' % video_id
                return jsonify(video_detail)
            title = video_info_response['items'][0]['snippet']['title']
            upload_date = video_info_response['items'][0]['snippet']['publishedAt']
            duration = video_info_response['items'][0]['contentDetails']['duration']
            thumb_url = video_info_response['items'][0]['snippet']['thumbnails']['high']['url']
        # insert into video_list
        if (video_id and title and upload_date and duration and thumb_url and channel_id): 
            cur.execute(
                'INSERT INTO video_list (video_id, title, upload_date, duration, channel_id, thumb_url) VALUES (?, ?, ?, ?, ?, ?)', 
                (video_id, title, upload_date, duration, channel_id, thumb_url)
            )
            # insert into talent_participation and stream_type
            tagged_title = tag_title(title)
            for talent_name in talent_names: 
                cur.execute('INSERT INTO talent_participation (talent_name, video_id) VALUES (?, ?)', (talent_name.strip(), video_id))
            for stream_type in stream_types: 
                cur.execute('INSERT INTO stream_type (stream_type, video_id) VALUES (?, ?)', (stream_type.strip(), video_id))
            # insert into search_video
            cur.execute(
                'INSERT INTO search_video (video_id, title, tagged_title, talents, stream_type) VALUES (?, ?, ?, ?, ?)', 
                (video_id, title, tagged_title, ';'.join(talent_names), ';'.join(stream_types))
            )
            db.commit()
            # regenerate upload_idx
            regenerate_upload_index(channel_id)
            return jsonify(single_video(video_id))
        else: 
            video_detail = build_video_detail()
            video_detail['serverMessage'] = 'Insufficient argument'
            return jsonify(video_detail)
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


########## ---------- angular api's ---------- ##########


@bp.route('/check-login')
def check_login(): 
    if g.user: 
        return jsonify({'userId': g.user['id'], 'userName': g.user['username']})
    else: 
        return jsonify({'userId': -1, 'userName': ''})


@bp.route('/login', methods = ('POST', ))
def login(): 
    if request.method == 'POST': 
        # get form contents
        username = request.json['userName']
        password = request.json['password']

        user_info = try_login(username, password)        

        return jsonify({'userId': user_info.userid, 'userName': user_info.username})

    return jsonify({'userId': -1, 'userName': ''})


@bp.route('/logout')
def logout(): 
    session.clear()
    return jsonify({'userId': -1, 'userName': ''})


@bp.route('/channels')
def channels(): 
    channel_list = get_channels()
    return jsonify([{
        'channelId': i['channel_id'], 
        'channelName': i['channel_name'], 
        'thumbUrl': i['thumb_url']
    } for i in channel_list])


@bp.route('/add-channel', methods = ('POST',))
@api_login_required
def add_channel_api(): 
    new_channel_overview = {'channelId': '', 'channelName': '', 'thumbUrl': ''}
    new_channel_id = request.json['channelId']
    new_channel_overview = add_channel(new_channel_id)
    return jsonify(new_channel_overview)


@bp.route('/fetch-channels')
@api_login_required
def fetch_channels_api(): 
    fetched_channel_list = fetch_all()
    return jsonify(fetched_channel_list)


@bp.route('/channel/<channel_id>')
def channel_detail_api(channel_id: str): 
    channel_detail = single_channel_detail(channel_id)
    return jsonify(channel_detail)


@bp.route('/channel-videos/<channel_id>')
def channel_video_api(channel_id):
    page = request.args.get('page', 1)
    page_entry_num = request.args.get('pageEntryNum', 5)
    video_num, channel_videos = single_channel_videos(channel_id, int(page), int(page_entry_num))
    return jsonify({
        'videoNum': video_num, 
        'videoList': channel_videos
    })


@bp.route('/update-idx/<channel_id>', methods=("POST",))
@api_login_required
def update_channel_idx_api(channel_id): 
    checkpoint_idx = request.json.get('checkpointIdx', 0)
    video_id = request.json.get('videoId', '')
    offset = request.json.get('offset', 0)
    update_result = edit_checkpoint(channel_id, checkpoint_idx=checkpoint_idx, video_id=video_id, offset=offset)
    if update_result == 1: 
        return jsonify(single_channel_detail(channel_id))
    else: 
        return jsonify(single_channel_detail())


@bp.route('/update-talent-name/<channel_id>', methods=("POST",))
@api_login_required
def update_channel_talent_name_api(channel_id: str): 
    new_talent_name = request.json.get('talentName', '')
    update_result = False
    if new_talent_name: 
        update_result = edit_talent(channel_id, new_talent_name)
    if not update_result: 
        return jsonify(single_channel_detail(channel_id))
    else: 
        return jsonify(single_channel_detail())


# add talent name for videos without a known talent name
@bp.route('/add-video-talent-name/<channel_id>')
@api_login_required
def add_video_talent_name_api(channel_id: str): 
    add_result = add_talent_name(channel_id)
    if not add_result: 
        return single_channel_detail(channel_id)
    else: 
        return single_channel_detail()
