# -*- coding: utf-8 -*-
import datetime
import json
import os

import google_auth_oauthlib
import googleapiclient.discovery
import googleapiclient.errors
import isodate
from flask import current_app, g
from sudachipy import dictionary, tokenizer


def get_pagination(current_page, page_num, pagination_length): 
    if pagination_length > page_num: 
        pagination_list = list(range(1, page_num+1))
        return pagination_list
    tmp_pagination_list = list(range(current_page - (pagination_length-1)//2, current_page - (pagination_length-1)//2 + pagination_length))
    pagination_list = tmp_pagination_list[:]
    if tmp_pagination_list[0] < 1: 
        pagination_list = [i + 1 - tmp_pagination_list[0] for i in tmp_pagination_list]
    elif tmp_pagination_list[-1] > page_num: 
        pagination_list = [i - (tmp_pagination_list[-1]-page_num) for i in tmp_pagination_list]
    return pagination_list


class Pagination(): 
    def __init__(self, current_page, page_num, pagination_length) -> None:
        self.list = get_pagination(current_page, page_num, pagination_length)
        self.active_page = current_page
        self.links = []
        self.first_link = ''
        self.last_link = ''


def to_isoformat(date_obj): 
    return datetime.datetime.isoformat(date_obj, timespec="seconds")+'Z'


def calculate_date_from_delta(delta_days: int): 
    '''
    calculate the date since which delta_time days have passed
    delta_time: days since now
    '''
    return to_isoformat(datetime.datetime.utcnow() - datetime.timedelta(days=delta_days))+'Z'


def calculate_date_week(delta_week: int): 
    return to_isoformat(datetime.datetime.utcnow() - datetime.timedelta(days=delta_week))+'Z'


def week_stops(start_date_str, end_date_str): 
    '''
    input: ISO 8601 date, return list from date earlier than that day to today with step size of 1 week, from earlist to latest
    '''
    end_date_obj = datetime.datetime.fromisoformat(end_date_str[:-1])
    week_stop_list = [end_date_obj]
    current_stop = week_stop_list[0]
    while current_stop > datetime.datetime.fromisoformat(start_date_str[:-1]): 
        current_stop = current_stop - datetime.timedelta(weeks=1)
        week_stop_list.append(current_stop)
    week_stop_list.reverse()
    return list(map(to_isoformat, week_stop_list))


def parse_duration(duration_str_pt): 
    return isodate.parse_duration(duration_str_pt).seconds


def tag_title(title: str) -> str: 
    '''
    return tokenized title based on split mode A
    '''
    tokenizer_obj = dictionary.Dictionary().create()
    mode = tokenizer.Tokenizer.SplitMode.A
    tagged_title =' '.join([m.surface() for m in tokenizer_obj.tokenize(title, mode)])
    return tagged_title


def build_youtube_api():
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
