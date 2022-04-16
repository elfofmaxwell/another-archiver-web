# -*- coding: utf-8 -*-
import datetime
import json
import os

import google_auth_oauthlib
import googleapiclient.discovery
import googleapiclient.errors
import isodate
from flask import current_app
from sudachipy import dictionary, tokenizer


def to_isoformat(date_obj: datetime.date) -> str: 
    """generate current date in server side

    Args:
        date_obj (datetime.date): datetime.date object to parse

    Returns:
        str: YYYY-MM-DDThh-mm-ssZ utc iso time string
    """
    return datetime.datetime.isoformat(date_obj, timespec="seconds")+'Z'


def calculate_date_from_delta(delta_days: int) -> str: 
    """calculate the date `delta_days` days ago from current time

    Args:
        delta_days (int): number of days

    Returns:
        str: date in iso string
    """
    return to_isoformat(datetime.datetime.utcnow() - datetime.timedelta(days=delta_days))+'Z'


def calculate_date_week(delta_week: int) -> str: 
    """calculate the date `delta_week` weeks ago from current time

    Args:
        delta_week (int): delta_week: number of weeks

    Returns:
        str: date in iso string
    """
    return to_isoformat(datetime.datetime.utcnow() - datetime.timedelta(days=delta_week))+'Z'


def week_stops(start_date_str: str, end_date_str: str) -> list[str]: 
    """calculate the intervals for weekly statistics; if diff between start date and end date is less than 1 week, the interval would be 1 day rather than 1 week

    Args:
        start_date_str (str): ISO 8601 date for lower bound of query duration
        end_date_str (str): ISO 8601 date for upper bound of query duration

    Returns:
        list[str]: list from date earlier than that day to today with step size of 1 week, from earlist to latest
    """
    # remove 'z'
    end_date_obj = datetime.datetime.fromisoformat(end_date_str[:-1])
    start_date_obj = datetime.datetime.fromisoformat(start_date_str[:-1])
    week_stop_list = [end_date_obj]
    current_stop = week_stop_list[0]

    # calculate diff between start date and end date 
    if (end_date_obj - start_date_obj).days > 7: 
        step_size = datetime.timedelta(weeks=1)
    else: 
        step_size = datetime.timedelta(days=1)
    # calculate previous stops based on interval
    while current_stop > start_date_obj: 
        current_stop = current_stop - step_size
        week_stop_list.append(current_stop)
    # reverse the list so that the stops are from oldest to newest
    week_stop_list.reverse()
    return list(map(to_isoformat, week_stop_list))


def parse_duration(duration_str_pt: str) -> int: 
    """parse iso duration string to seconds

    Args:
        duration_str_pt (str): iso duration string

    Returns:
        int: duration length in second
    """
    return isodate.parse_duration(duration_str_pt).seconds


def tag_title(title: str) -> str: 
    """tokenize title based on split mode A, used for full text search

    Args:
        title (str): string for tokenization

    Returns:
        str: tokenized input
    """
    tokenizer_obj = dictionary.Dictionary().create()
    mode = tokenizer.Tokenizer.SplitMode.A
    tagged_title =' '.join([m.surface() for m in tokenizer_obj.tokenize(title, mode)])
    return tagged_title


def build_youtube_api():
    """generate youtube client

    Returns:
        YouTubeApiClient: youtube api client
    """
    # set api credentials
    scopes = ['https://www.googleapis.com/auth/youtube.force-ssl']
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "0"
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = os.path.join(current_app.root_path, "secrets.json")
    refresh_token_file = os.path.join(current_app.root_path, "refresh_token.json")
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
    # if no refresh token, request brand new token set
    if not os.path.isfile(refresh_token_file): 
        credentials = flow.run_console()
        with open(refresh_token_file, 'w') as f: 
            json.dump(credentials.refresh_token, f)
    # if there is refresh token, use it to get new access token
    else: 
        with open(client_secrets_file) as f: 
            client_info = json.load(f)
        client_id = client_info["installed"]["client_id"]
        with open(refresh_token_file) as f: 
            refresh_token = json.load(f)
        flow.oauth2session.refresh_token(flow.client_config['token_uri'], refresh_token=refresh_token, client_id=client_id, client_secret=flow.client_config['client_secret'])
        credentials = google_auth_oauthlib.helpers.credentials_from_session(flow.oauth2session, flow.client_config)
    # create api client
    youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)
    return youtube


def build_video_detail(title: str='', upload_date: str='', duration: str='', upload_index: int=0, thumb_url: str='', local_path: str='', video_id: str='', channel_id: str='', channel_name: str='', talent_names: list[str]=[], stream_types: list[str]=[]) -> dict: 
    """use arguments to generate a jsonifiable dict for video detail api

    Args:
        title (str, optional): video title. Defaults to ''.
        upload_date (str, optional): upload datetime in iso8601. Defaults to ''.
        duration (str, optional): duration in iso8601. Defaults to ''.
        upload_index (int, optional): upload index for the video in its channel. Defaults to 0.
        thumb_url (str, optional): thumbnail picture url. Defaults to ''.
        local_path (str, optional): local path for archived video. Defaults to ''.
        video_id (str, optional): video ID. Defaults to ''.
        channel_id (str, optional): channel ID of the uploader. Defaults to ''.
        channel_name (str, optional): channel Name of the uploader. Defaults to ''.
        talent_names (list[str], optional): list of talents who participated in the video. Defaults to [].
        stream_types (list[str], optional): list of type tags of the video. Defaults to [].

    Returns:
        dict: jsonifiable dict for video detail api
    """
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


def build_video_overview(video_id: str='', title: str='', uploadDate: str='', duration: str='', uploadIndex: int=0, thumbUrl: str='', local_path: str='') -> dict: 
    """use arguments to generate a jsonifiable dict for video overview api

    Args:
        video_id (str, optional): video ID. Defaults to ''.
        title (str, optional): video title. Defaults to ''.
        uploadDate (str, optional): upload datetime in iso8601. Defaults to ''.
        duration (str, optional): video duration in iso8601. Defaults to ''.
        uploadIndex (int, optional): upload index for the video in its channel. Defaults to 0.
        thumbUrl (str, optional): thumbnail picture url. Defaults to ''.
        local_path (str, optional): local path for archived video. Defaults to ''.

    Returns:
        dict: jsonifiable dict for video overview api
    """
    return {
        'videoId': video_id, 
        'title': title,
        'uploadDate': uploadDate,
        'duration': duration,
        'uploadIndex': uploadIndex, 
        'thumbUrl': thumbUrl,
        'localPath': local_path,
    }


def build_channel_detail(channel_id: str = '', channel_name: str = '', thumb_url: str = '', talent_name: str = '', video_num: int = 0, checkpoint_idx: int = 0) -> dict: 
    """use arguments to generate a jsonifiable dict for channel detail api

    Args:
        channel_id (str, optional): channel ID. Defaults to ''.
        channel_name (str, optional): channel Name. Defaults to ''.
        thumb_url (str, optional): picture url for channel thumbnail. Defaults to ''.
        talent_name (str, optional): the name of the channel owner. Defaults to ''.
        video_num (int, optional): number of videos in the channel. Defaults to 0.
        checkpoint_idx (int, optional): current download checkpoint of the channel. Defaults to 0.

    Returns:
        dict: jsonifiable dict for channel detail api
    """
    return {
        'channelId': channel_id,
        'channelName': channel_name,
        'thumbUrl': thumb_url,
        'talentName': talent_name,
        'videoNum': video_num,
        'checkpointIndex': checkpoint_idx,
    }
