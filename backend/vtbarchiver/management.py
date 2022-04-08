# -*- coding: utf-8 -*- 


import functools
import getpass
import os
import subprocess

import click
import psutil
import yaml
from flask import (Blueprint, abort, current_app, flash, g, jsonify, redirect,
                   render_template, request, session, url_for)
from flask.cli import with_appcontext
from werkzeug.security import check_password_hash, generate_password_hash

from vtbarchiver.db_functions import get_db, tag_suggestions
from vtbarchiver.download_functions import check_lock
from vtbarchiver.local_file_management import (get_relpath_to_static,
                                               scan_local_videos)
from vtbarchiver.misc_funcs import tag_title

bp = Blueprint('management', __name__, url_prefix='/management')


# load user with cookie
@bp.before_app_request
def load_logged_in_user(): 
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


# login required wrapper
def login_required(view): 
    @functools.wraps(view)
    
    def wrapped_view(**kwargs): 
        # if no user in current request, redirect for login
        if g.user is None: 
            return redirect(url_for('management.login'))
        # else excute view
        return view(**kwargs)
    
    return wrapped_view


# login required wrapper for api
def api_login_required(view): 
    @functools.wraps(view)
    
    def wrapped_view(**kwargs): 
        # if no user in current request, redirect for login
        if g.user is None: 
            abort(400)
        # else excute view
        return view(**kwargs)
    
    return wrapped_view


# login page
@bp.route('/login', methods=('GET', 'POST'))
def login(): 
    if request.method == 'POST': 
        # get form contents
        username = request.form['username']
        password = request.form['password']

        # search for user in db
        db = get_db()
        error = None
        cur = db.cursor()
        try: 
            cur.execute('SELECT * FROM admin_list WHERE username = ?', (username, ))
            user = cur.fetchone()
        finally: 
            cur.close()
        
        # check whether password is corret
        if (not user) or (not check_password_hash(user['passwd_hash'], password)): 
            error = 'Invalid username or password, please try again'

        
        # if correct, renew cookie and redirect to management panel
        if error is None: 
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('management.settings'))
        
        # push error
        flash(error)
    
    # show login page
    return render_template('management/login.html')


# logout
@bp.route('/logout')
def logout(): 
    session.clear()
    return redirect(url_for('home.index'))


# settings
@bp.route('/settings', methods=('GET', 'POST'))
@login_required
def settings(): 
    config_path = current_app.config['DL_CONF_PATH']
    with open(config_path) as f: 
        dl_configs = yaml.safe_load(f)

    if request.method == 'POST': 
        for config_key in dl_configs: 
            dl_configs[config_key] = request.form[config_key]
        with open(config_path, 'w') as f: 
            yaml.safe_dump(dl_configs, f)
    
    return render_template('management/settings.html', dl_configs=dl_configs, is_downloading = check_lock())


# start download all channels
@bp.route('/trigger-download')
@login_required
def trigger_download(): 
    if not check_lock():
        flask_env = os.environ.copy()
        subprocess.Popen(['flask', 'download-channels'], env=flask_env)

    return redirect(url_for('management.settings'))


# stop download process
@bp.route('/stop-tasks')
@login_required
def stop_tasks(): 
    if check_lock(): 
        lock_path = os.path.join(current_app.root_path, 'download.lock')
        with open(lock_path) as f: 
            working_pid = int(f.readline())
        p = psutil.Process(working_pid)
        p.terminate()
        os.remove(lock_path)
    
    return redirect(url_for('management.settings'))


# scan for videos
@bp.route('/scan-local')
@login_required
def scan_local(): 
    config_path = os.path.join(current_app.root_path, 'config.yaml')
    with open(config_path) as f: 
        config = yaml.safe_load(f)
    scan_path = config['local_videos']
    scan_local_videos(scan_path)

    return redirect(url_for('management.settings'))

# use cli to add admin user
@click.command('add-admin')
@with_appcontext
def add_admin_command(): 
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
    db = get_db()
    cur = db.cursor()
    try: 
        cur.execute('DELETE FROM search_video')
        cur.execute('SELECT video_id, title FROM video_list')
        video_list = cur.fetchall()
        for single_video in video_list: 
            cur.execute('SELECT talent_name FROM talent_participation WHERE video_id = ?', (single_video['video_id'], ))
            talent_names = ';'.join([i['talent_name'] for i in cur.fetchall()])
            cur.execute('SELECT stream_type FROM stream_type WHERE video_id = ?', (single_video['video_id'], ))
            stream_type = ';'.join([i['stream_type'] for i in cur.fetchall()])
            tagged_title = tag_title(single_video['title'])
            cur.execute(
                'INSERT INTO search_video (video_id, title, tagged_title, talents, stream_type) VALUES (?, ?, ?, ?, ?)', 
                (single_video['video_id'], single_video['title'], tagged_title, talent_names, stream_type)
                )
    except: 
        raise
    else: 
        click.echo('Search index reganerated. ')
        db.commit()
    finally: 
        cur.close()


def try_login(username, password): 

    class UserInfo(): 
        def __init__(self, userid=-1, username='') -> None:
            '''
            userid: int, default -1
            username: string, default ''
            '''
            self.userid = userid
            self.username = username
            

    db = get_db()
    error = None
    cur = db.cursor()
    try: 
        cur.execute('SELECT * FROM admin_list WHERE username = ?', (username, ))
        user = cur.fetchone()
    finally: 
        cur.close()
    
    # check whether password is corret
    if (not user) or (not check_password_hash(user['passwd_hash'], password)): 
        error = 'Invalid username or password, please try again'

    
    # if correct, renew cookie and redirect to management panel
    if error is None: 
        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        return UserInfo(user['id'], user['username'])
    
    return UserInfo()
