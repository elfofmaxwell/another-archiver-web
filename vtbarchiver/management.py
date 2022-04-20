# -*- coding: utf-8 -*- 


import functools
import getpass
from distutils.command.config import config

import click
import yaml
from flask import Blueprint, abort, current_app, g, redirect, session, url_for
from flask.cli import with_appcontext
from werkzeug.security import check_password_hash, generate_password_hash

from vtbarchiver.db_functions import get_db
from vtbarchiver.misc_funcs import tag_title

bp = Blueprint('management', __name__, url_prefix='/management')


# load user with cookie
@bp.before_app_request
def load_logged_in_user(): 
    """load user information to current `g`
    """
    # load cookie
    user_id = session.get('user_id')

    # if there is no user_id in cookie, set user to None
    if user_id is None: 
        g.user = None
    # if there is user_id, retrieve user information and load into current g
    else: 
        db = get_db()
        cur = db.cursor()
        try: 
            cur.execute('SELECT * FROM admin_list WHERE id = ?', (user_id, ))
            g.user = cur.fetchone()
        finally: 
            cur.close()


# login required wrapper for api
def api_login_required(view): 
    """factory for a decorator to make view function require login for apis

    Args:
        view (function): view function that requires login

    Returns:
        function: the decorator
    """
    @functools.wraps(view)
    def wrapped_view(**kwargs): 
        """a decorator to make view function require login for apis

        Returns:
            function: wrapped view function
        """
        # if no user in current request, abort in 400
        if g.user is None: 
            abort(400)
        # else excute view
        return view(**kwargs)
    
    return wrapped_view


def get_settings()->dict: 
    """get settings in dict form from local config.yaml

    Returns:
        dict: dict with settings
    """
    config_path = current_app.config['DL_CONF_PATH']
    with open(config_path) as f: 
        dl_configs = yaml.safe_load(f)
    setting_dict = {}
    # convert string "True" or "False" to boolean
    slow_mode = dl_configs.get('slow_mode', '')
    if slow_mode == 'False': 
        setting_dict['slowMode'] = False
    else: 
        setting_dict['slowMode'] = True
    # get value and set default value if there is no valid entry
    setting_dict['sleepTime'] = int(dl_configs.get('sleep_time', 0))
    setting_dict['cookiePath'] = dl_configs.get('cookie_path', '')
    setting_dict['downloadPath'] = dl_configs.get('download_path', '')
    setting_dict['scanPath'] = dl_configs.get('local_videos', '')
    return setting_dict


def put_settings(setting_dict: dict)->dict:
    """put settings in the setting dict into config.yaml

    Args:
        setting_dict (dict): dict with settings

    Returns:
        dict: current setting dict from the updated config.yaml
    """
    dl_config = {}
    slow_mode = setting_dict.get('slowMode', 'true')
    dl_config['slow_mode'] = str(slow_mode != 'false')
    dl_config['sleep_time'] = str(setting_dict.get('sleepTime', ''))
    dl_config['cookie_path'] = str(setting_dict.get('cookiePath', ''))
    dl_config['download_path'] = str(setting_dict.get('downloadPath', ''))
    dl_config['local_videos'] = str(setting_dict.get('scanPath', ''))
    config_path = current_app.config['DL_CONF_PATH']
    with open(config_path, 'w') as f: 
        yaml.safe_dump(dl_config, f)
    return get_settings()


# use cli to add admin user
@click.command('add-admin')
@with_appcontext
def add_admin_command(): 
    """cli interface to add a manager account
    """
    while True: 
        # check if username is empty
        while True: 
            new_username = input("Please enter username: ")
            if new_username: 
                break
            print("Username cannot be empty! Please retry")
        
        # check if password is empty or consistent
        while True: 
            new_passwd = getpass.getpass("New password: ")
            repeated_passwd = getpass.getpass("Confirm password: ")
            if (new_passwd == repeated_passwd) and new_passwd: 
                break
            print("Password not match! Please retry. ")
        
        # add user to database
        db = get_db()
        try: 
            db.execute('INSERT INTO admin_list (username, passwd_hash) VALUES (?, ?)', (new_username, generate_password_hash(new_passwd)))
            db.commit()
        except db.IntegrityError: 
            continue
        else: 
            break
    print('New admin added. ')


@click.command('reindex-search')
@with_appcontext
def regenerate_search_index(): 
    """cli interface to regenerate search index for all videos
    """
    db = get_db()
    cur = db.cursor()
    try: 
        # delete current index
        cur.execute('DELETE FROM search_video')
        # get video id and title for videos
        cur.execute('SELECT video_id, title FROM video_list')
        video_list = cur.fetchall()
        for single_video in video_list: 
            # for each video, get talent names and stream types, concatenate the tags to form searching text
            cur.execute('SELECT talent_name FROM talent_participation WHERE video_id = ?', (single_video['video_id'], ))
            talent_names = ';'.join([i['talent_name'] for i in cur.fetchall()])
            cur.execute('SELECT stream_type FROM stream_type WHERE video_id = ?', (single_video['video_id'], ))
            stream_type = ';'.join([i['stream_type'] for i in cur.fetchall()])
            # tokenize the title
            tagged_title = tag_title(single_video['title'])
            # dump the generated indices
            cur.execute(
                'INSERT INTO search_video (video_id, title, tagged_title, talents, stream_type) VALUES (?, ?, ?, ?, ?)', 
                (single_video['video_id'], single_video['title'], tagged_title, talent_names, stream_type)
                )
    except: 
        raise
    else: 
        # display information and submit changes if there is nothing wrong
        click.echo('Search index reganerated. ')
        db.commit()
    finally: 
        cur.close()


class UserInfo(): 
    def __init__(self, userid=-1, username='') -> None:
        """user info class

        Args:
            userid (int, optional): user id. Defaults to -1.
            username (str, optional): user name. Defaults to ''.
        """
        self.userid = userid
        self.username = username


def try_login(username, password)->UserInfo: 
    """login a user

    Args:
        username (str): username
        password (str): password

    Returns:
        UserInfo: information of logged in user, if login failed, username would be empty
    """

    db = get_db()
    error = None
    cur = db.cursor()
    try: 
        # get user info from db
        cur.execute('SELECT * FROM admin_list WHERE username = ?', (username, ))
        user = cur.fetchone()
    finally: 
        cur.close()
    
    # check whether password is corret
    if (not user) or (not check_password_hash(user['passwd_hash'], password)): 
        error = 'Invalid username or password, please try again'
    # if correct, renew cookie and return the logged in user's info
    if error is None: 
        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        return UserInfo(user['id'], user['username'])
    # if login failed, return an empty user info obj
    return UserInfo()
