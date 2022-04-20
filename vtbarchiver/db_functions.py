# -*- coding: utf-8 -*-

import datetime
import sqlite3
from functools import reduce

import click
from flask import current_app, g
from flask.cli import with_appcontext

from vtbarchiver.misc_funcs import (calculate_date_from_delta, parse_duration,
                                    to_isoformat, week_stops)


def get_db() -> sqlite3.Connection: 
    """get a db connection for each request

    Returns:
        sqlite3.Connection: sqlite connection obj with row factory
    """
    # get new db if there is no one for current request
    if 'db' not in g: 
        g.db = sqlite3.connect(
            current_app.config['DATABASE'], 
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    """close db when connection closed

    Args:
        e (Error, optional): connection error. Defaults to None.
    """
    # close db if there is a db in current request  
    db = g.pop('db', None)
    if db is not None: 
        db.close()


def init_db(): 
    """use init_db.sql to initialize a new db, all previous data would be dropped
    """
    db = get_db()
    cur = db.cursor()
    with current_app.open_resource('init_db.sql') as f: 
        cur.executescript(f.read().decode('utf8'))
    cur.close()
    db.commit()


@click.command('init-db')
@with_appcontext
def init_db_command(): 
    """cli implement for init_db
    """
    init_db()
    click.echo('Database created/reinitialized')


def full_text_search(table_name: str, search_key: str) -> list[str]: 
    """full text search on db

    Args:
        table_name (str): the table name to query on
        search_key (str): the search key

    Returns:
        list[str]: video ID list matching the search keys
    """
    db = get_db()
    cur = db.cursor()
    try: 
        cur.execute('SELECT video_id FROM %s WHERE %s MATCH ? ORDER BY rank' % (table_name, table_name), (search_key, ))
        searched_results = [i['video_id'] for i in cur.fetchall()]
        return searched_results
    finally: 
        cur.close()


def time_range_filter(start_time: str, end_time: str) -> list[str]: 
    """get video ID's within specified time range

    Args:
        start_time (str): lower bound for time range in iso8601 UTC time YYYY-MM-DDThh-mm-ssZ
        end_time (str): upper bound for time range in iso8601 UTC time YYYY-MM-DDThh-mm-ssZ

    Returns:
        list[str]: video ID list in time range
    """
    db = get_db()
    cur = db.cursor()
    try: 
        cur.execute('SELECT video_id FROM video_list WHERE upload_date>? AND upload_date<?', (start_time, end_time))
        searched_results = [i['video_id'] for i in cur.fetchall()]
        return searched_results
    finally: 
        cur.close()


def find_common_items(*lists_for_reduction: list) -> list: 
    """take multiple lists and return their common items in a list

    Returns:
        list: list of common items
    """
    # find common items in 2 list, used for reduction
    def find_common_2(list1, list2): 
        """find common items for 2 list

        Args:
            list1 (list): first list
            list2 (list): second list

        Returns:
            list: list with common items
        """
        return list(set(list1).intersection(list2))
    # reduce the lists if there is multiple input
    if len(lists_for_reduction) > 1: 
        return reduce(find_common_2, lists_for_reduction)
    # return the original list if there is only one arg
    elif len(lists_for_reduction) == 1: 
        return lists_for_reduction[0]
    else: 
        return []


def find_tags(table_name: str, column_name: str, tag_list: list[str]) -> list[str]:
    """find video ID with given tag in specified table and column

    Args:
        table_name (str): table to query
        column_name (str): column to query
        tag_list (list[str]): tags for filter

    Returns:
        list[str]: video ID list fulfilling the filter
    """
    db = get_db()
    cur = db.cursor()
    result_list_set = []
    try: 
        for tag in tag_list: 
            cur.execute("SELECT video_id FROM %s WHERE %s=? COLLATE NOCASE" % (table_name, column_name), (tag, ))
            result_list = [i['video_id'] for i in cur.fetchall()]
            result_list_set.append(result_list)
        reduced_result_list = find_common_items(*result_list_set)
        return reduced_result_list
    finally:
        cur.close()


def tag_suggestions(tag_type: str, query_str: str): 
    """get tags from db that partial matches the user input and return the tags as suggestions.

    Args:
        tag_type (str): which tag type to check: 'talents' or 'stream_type'
        query_str (str): user input

    Returns:
        _type_: list of candidate tags
    """
    suggestion_list = []
    db = get_db()
    cur = db.cursor()
    try: 
        if tag_type == 'talents': 
            cur.execute('SELECT talent_name FROM talent_participation WHERE talent_name LIKE ? GROUP BY talent_name', ('%'+query_str+'%', ))
            suggestion_list = [i['talent_name'] for i in cur.fetchall()]
        elif tag_type == 'tags': 
            cur.execute('SELECT stream_type FROM stream_type WHERE stream_type LIKE ? GROUP BY stream_type', ('%'+query_str+'%', ))
            suggestion_list = [i['stream_type'] for i in cur.fetchall()] 
        return suggestion_list
    finally: 
        cur.close()


class ChannelStats(): 
    """class for channel statistics
    """
    def __init__(self, channel_id: str) -> None:
        """initialize channel stats basic params

        Args:
            channel_id (str): channel ID
        """
        self.channel_id = channel_id
        # if there is no lower time bound specified, use unix time 0 as lower bound
        self.time_origin = "1970-01-01T00:00:00Z"
    
    def get_time_stamp(self, time_delta: int, lower_date_stamp_input: str, upper_date_stamp_input: str) -> tuple[str, str]: 
        """get time range lower and upper bound for searching. Time delta precedent the other 2 types. 0 or negative time delta would not be used; empty date stamp would not be used. 

        Args:
            time_delta (int): time delta from now in days
            lower_date_stamp_input (str): iso datetime string at UTC for lower time range bound; if empty string provided, unix time origin would be used
            upper_date_stamp_input (str): iso datetime string at UTC for upper time range bound; if empty string provided, current time would be used

        Returns:
            tuple[str, str]: iso datetime string at UTC for lower time range bound, iso date string at UTC for upper time range bound
        """
        if time_delta <= 0: 
            lower_date_stamp = self.time_origin
            if lower_date_stamp_input: 
                lower_date_stamp = lower_date_stamp_input
            if upper_date_stamp_input: 
                upper_date_stamp = upper_date_stamp_input
            else: 
                upper_date_stamp = to_isoformat(datetime.datetime.utcnow())
        else: 
            lower_date_stamp = calculate_date_from_delta(time_delta)
            upper_date_stamp = to_isoformat(datetime.datetime.utcnow())
        
        return lower_date_stamp, upper_date_stamp

    def talents_stats(self, time_delta=0, lower_date_stamp='', upper_date_stamp='')->dict: 
        """talent statistic for chart.js api

        Args:
            time_delta (int, optional): time delta from now in days. Defaults to 0.
            lower_date_stamp (str, optional): iso time string at UTC for lower time bound. Defaults to '' for unix origin.
            upper_date_stamp (str, optional): iso time sting at UTC for upper time bound. Defaults to '' for current time.

        Returns:
            dict: jsonifiable dict for chart.js api {talentName: [labels], num: [data]}
        """
        db = get_db()
        cur = db.cursor()
        
        lower_date_stamp, upper_date_stamp = self.get_time_stamp(time_delta, lower_date_stamp, upper_date_stamp)

        try: 
            # build api dict
            talent_count_dict = {
                "talentName": [], 
                "num": [], 
            }
            # get the talent name of the given channel
            cur.execute('SELECT talent_name FROM channel_list WHERE channel_id=?', (self.channel_id, ))
            channel_talent_name = cur.fetchone()['talent_name']
            # count talent tags for all videos
            cur.execute(
                '''
                SELECT tp.talent_name talent_name, COUNT(*) num 
                FROM talent_participation tp 
                JOIN video_list vl 
                ON tp.video_id = vl.video_id
                WHERE vl.channel_id = ? and vl.upload_date >= ? AND vl.upload_date < ?
                GROUP BY tp.talent_name
                '''
            , (self.channel_id, lower_date_stamp, upper_date_stamp))
            talent_count_results = cur.fetchall()
            # add counted results into dataset except channel owner's tag
            for i in talent_count_results: 
                if i['talent_name'] != channel_talent_name: 
                    talent_count_dict['talentName'].append(i['talent_name'])
                    talent_count_dict['num'].append(i['num'])
            # count videos that only have channel owners tag, considering as solo stream
            cur.execute(
                '''
                SELECT tp.video_id talent_name, COUNT(*) num 
                FROM talent_participation tp 
                JOIN video_list vl 
                ON tp.video_id = vl.video_id 
                WHERE vl.channel_id = ? AND vl.upload_date >= ? AND vl.upload_date < ?
                GROUP BY tp.video_id 
                HAVING COUNT(*)=1;
                ''', (self.channel_id, lower_date_stamp, upper_date_stamp)
            )
            talent_count_dict['talentName'].append('solo')
            talent_count_dict['num'].append(len(cur.fetchall()))
            return talent_count_dict

        finally: 
            cur.close()

    
    def tag_stats(self, time_delta=0, lower_date_stamp='', upper_date_stamp='')->dict: 
        """stream type statistic with chart.js api format

        Args:
            time_delta (int, optional): time range in days. Defaults to 0.
            lower_date_stamp (str, optional): iso date string for time range lower bound. Defaults to '' for unix time origin.
            upper_date_stamp (str, optional): iso date string for range upper bound. Defaults to '' for current time.

        Returns:
            dict: jsonifiable dict for chart.js api {streamType: [labels], num: [data]}
        """
        '''
        stats on tags, return a list of dictionaries "tag_name": appeared times, with one "unknown": video number (number of videos without tags)
        '''
        db = get_db()
        cur = db.cursor()
        lower_date_stamp, upper_date_stamp = self.get_time_stamp(time_delta, lower_date_stamp, upper_date_stamp)
        try: 
            # count tags and add to data set
            cur.execute(
                '''
                SELECT st.stream_type stream_type, COUNT(*) num 
                FROM stream_type st 
                JOIN video_list vl 
                ON st.video_id = vl.video_id
                WHERE vl.channel_id = ? and vl.upload_date >= ? AND vl.upload_date < ?
                GROUP BY st.stream_type
                '''
            , (self.channel_id, lower_date_stamp, upper_date_stamp))
            type_count_results = cur.fetchall()
            type_count_dict = {
                "streamType": [i['stream_type'] for i in type_count_results], 
                "num": [i['num'] for i in type_count_results], 
            }
            
            # count videos without tags and add to dataset as unknown
            cur.execute(
                '''
                SELECT COUNT(*) num
                FROM video_list vl
                LEFT OUTER JOIN stream_type st
                ON vl.video_id = st.video_id
                WHERE (st.video_id IS NULL) AND vl.channel_id=? AND vl.upload_date >= ? AND vl.upload_date < ?
                ''', (self.channel_id, lower_date_stamp, upper_date_stamp)
            )
            type_count_dict['streamType'].append("unknown")
            type_count_dict['num'].append(cur.fetchone()['num'])

            return type_count_dict

        finally: 
            cur.close()

    def duration_stats(self, time_delta=0, lower_date_stamp='', upper_date_stamp='')->dict: 
        """total video duration in each week/days statistic

        Args:
            time_delta (int, optional): time range in days. Defaults to 0.
            lower_date_stamp (str, optional): iso date string for time range lower bound. Defaults to '' for unix time origin.
            upper_date_stamp (str, optional): iso date string for range upper bound. Defaults to '' for current time.

        Returns:
            dict: jsonifiable dict for chart.js api {week: [labels], duration: [data]}
        """
        db = get_db()
        cur = db.cursor()
        duration_dict = {"week": [], "duration": []}
        current_time = datetime.datetime.utcnow()

        try: 
            # get lower and upper time range bound with step size of week
            if time_delta > 0: 
                upper_date_stamp = to_isoformat(current_time)
                earlist_query_date = to_isoformat(current_time - datetime.timedelta(weeks=time_delta//7))
            else: 
                if lower_date_stamp: 
                    earlist_query_date = lower_date_stamp
                else: 
                    cur.execute('SELECT upload_date FROM video_list WHERE channel_id = ? ORDER BY upload_date', (self.channel_id, ))
                    earlist_query_date = cur.fetchone()['upload_date']
                if not upper_date_stamp: 
                    upper_date_stamp = to_isoformat(current_time)
            # get time stops
            week_stop_list = week_stops(earlist_query_date, upper_date_stamp)
            for i in range(len(week_stop_list)-1): 
                # for each week, get duration of each video
                cur.execute(
                    '''
                    SELECT video_id, duration FROM video_list WHERE channel_id = ? AND upload_date >= ? AND upload_date < ?
                    ''', (self.channel_id, week_stop_list[i], week_stop_list[i+1])
                )
                week_duration_list = list(map(parse_duration, [i['duration'] for i in cur.fetchall()]))
                # summing video duration for the week
                if week_duration_list: 
                    week_duration_sec = reduce(lambda duration_1, duration_2: duration_1+duration_2, week_duration_list)
                else: 
                    week_duration_sec = 0
                # add to data set
                duration_dict['week'].append(week_stop_list[i])
                duration_dict['duration'].append(week_duration_sec)
            
            return duration_dict

        finally: 
            cur.close()
    
    def duration_distr(self, time_delta=0, lower_date_stamp='', upper_date_stamp=''):
        """video length distribution in given time range

        Args:
            time_delta (int, optional): time range in days. Defaults to 0.
            lower_date_stamp (str, optional): iso date string for time range lower bound. Defaults to '' for unix time origin.
            upper_date_stamp (str, optional): iso date string for range upper bound. Defaults to '' for current time.

        Returns:
            dict: jsonifiable dict for chart.js api {duration: [labels], num: [data]}
        """
        '''
        return list of dict: distribution of video length, <30min, 30-60, 60-90, 90-120, 120-150, 150-180, 180-
        '''
        # function to filter videos within given duration range
        def duration_filter_factory(min_duration: int, max_duration: int=-1)->function: 
            """generate a function that judges whether a given duration is in specified duration range

            Args:
                min_duration (int): minimum duration in second
                max_duration (int, optional): max duration in second. Defaults to -1 (no upper bound).

            Returns:
                function: is the video's duration in given duration range?
            """
            if max_duration > 0:
                def duration_filter(duration_sec: int)->bool: 
                    """is the video's duration in given duration range?

                    Args:
                        duration_sec (int): the video's duration in second

                    Returns:
                        bool: is the video's duration in given duration range?
                    """
                    return (duration_sec >= min_duration and duration_sec < max_duration)
            else: 
                def duration_filter(duration_sec: int)->bool: 
                    """is the video's duration in given duration range?

                    Args:
                        duration_sec (int): the video's duration in second

                    Returns:
                        bool: is the video's duration in given duration range?
                    """
                    return (duration_sec >= min_duration)
            return duration_filter

        db = get_db()
        cur = db.cursor()
        duration_distr = {"duration": [], "num": []}
        lower_date_stamp, upper_date_stamp = self.get_time_stamp(time_delta, lower_date_stamp, upper_date_stamp)
        try: 
            # get video duration for each video within the date range
            cur.execute(
                '''
                SELECT duration FROM video_list WHERE channel_id = ? AND upload_date >= ? AND upload_date < ?
                ''', (self.channel_id, lower_date_stamp, upper_date_stamp)
            )
            # convert the dict list to duration numerical list
            duration_list = list(map(parse_duration, [i['duration'] for i in cur.fetchall()]))
            # count the number of videos in each duration range
            ## uses 0-30, 30-60, 60-90, 90-120, 120-150, 150-180, 180~ as steps
            for i in range(6): 
                duration_distr['num'].append(len(list(filter(duration_filter_factory(i*1800, (i+1)*1800), duration_list))))
            duration_distr['duration'] = ['<30', '30-60', '60-90', '90-120', '120-150', '150-180', '>180']
            duration_distr['num'].append(len(list(filter(duration_filter_factory(10800), duration_list))))
            return duration_distr

        finally: 
            cur.close()


    def video_num_stats(self, time_delta=0, lower_date_stamp='', upper_date_stamp=''): 
        """uploaded video number in each week/days statistic

        Args:
            time_delta (int, optional): time range in days. Defaults to 0.
            lower_date_stamp (str, optional): iso date string for time range lower bound. Defaults to '' for unix time origin.
            upper_date_stamp (str, optional): iso date string for range upper bound. Defaults to '' for current time.

        Returns:
            dict: jsonifiable dict for chart.js api {week: [labels], num: [data]}
        """
        '''
        return list of dict: {start_date_of_week: video_num_that_week}
        '''
        db = get_db()
        cur = db.cursor()
        num_dict = {"week": [], "num": []}
        current_time = datetime.datetime.utcnow()
        try: 
            # get lower and upper date bound with step size of week
            if time_delta > 0: 
                upper_date_stamp = to_isoformat(current_time)
                earlist_query_date = to_isoformat(current_time - datetime.timedelta(weeks=time_delta//7))
            else: 
                if lower_date_stamp: 
                    earlist_query_date = lower_date_stamp
                else: 
                    cur.execute('SELECT upload_date FROM video_list WHERE channel_id = ? ORDER BY upload_date', (self.channel_id, ))
                    earlist_query_date = cur.fetchone()['upload_date']
                if not upper_date_stamp: 
                    upper_date_stamp = to_isoformat(current_time)
            # get stop list
            week_stop_list = week_stops(earlist_query_date, upper_date_stamp)
            for i in range(len(week_stop_list)-1): 
                # count the number of videos in each time interval
                cur.execute(
                    '''
                    SELECT COUNT(*) num FROM video_list WHERE channel_id = ? AND upload_date >= ? AND upload_date < ?
                    ''', (self.channel_id, week_stop_list[i], week_stop_list[i+1])
                )
                num_dict['week'].append(week_stop_list[i])
                num_dict['num'].append(cur.fetchone()['num'])
            
            return num_dict
        
        finally: 
            cur.close()


def get_new_hex_vid()->str: 
    """get a new unique auto-incremental video id for unarchived content without known id

    Returns:
        str: new generated video ID based on hex integer
    """
    db = get_db()
    cur = db.cursor()
    try: 
        # get existing hex video ID
        cur.execute(r"SELECT video_id FROM video_list WHERE video_id LIKE '\_\_%\_\_' ESCAPE '\'")
        existed_hex_vids = cur.fetchall()
        # get the max hex video ID
        if existed_hex_vids:
            max_int_vid = max([int(i['video_id'].strip('_'), 16) for i in existed_hex_vids])
        else: 
            max_int_vid = 0
        # generate the new hex video ID
        new_hex_vid = '__%#07x__'%(max_int_vid+1)
        return new_hex_vid
    finally: 
        cur.close()


def regenerate_upload_index(channel_id: str): 
    """sort videos of the given channel and regenerate upload index

    Args:
        channel_id (str): channel ID
    """
    db = get_db()
    cur = db.cursor()
    try: 
        # sort video
        cur.execute('SELECT id FROM video_list WHERE channel_id=? ORDER BY upload_date', (channel_id, ))
        id_by_date = cur.fetchall()
        # give new index
        for upload_idx in range(len(id_by_date)): 
            cur.execute('UPDATE video_list SET upload_idx=? WHERE id=?', (upload_idx+1, id_by_date[upload_idx][0]))
        db.commit()
    finally:
        cur.close()
