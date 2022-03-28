# -*- coding: utf-8 -*-

from flask import Blueprint, current_app, g, jsonify, request

from vtbarchiver.db_functions import ChannelStats, get_db, tag_suggestions

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

