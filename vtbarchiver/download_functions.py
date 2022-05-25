# -*- coding: utf-8 -*-
import os
import random
import subprocess
import time

import click
import yaml
from flask import current_app, g
from flask.cli import with_appcontext

from vtbarchiver.db_functions import get_db
from vtbarchiver.local_file_management import scan_local_videos


def check_lock(): 
    lock_path = os.path.join(current_app.root_path, 'download.lock')
    return os.path.isfile(lock_path)


@click.command('download-single')
@click.option('--video_id', required=True)
@click.option('--sequenced', default=False)
@with_appcontext
def download_single_video(video_id, sequenced): 
    # check if there is any other download process running
    db = get_db()
    cur = db.cursor()

    if check_lock(): 
        return -1

    # create download lock
    my_pid = os.getpid()
    lock_path = os.path.join(current_app.root_path, 'download.lock') 
    with open(lock_path, 'w') as f: 
        f.write(str(my_pid))

    try: 
        # find video
        cur.execute("SELECT channel_id, upload_date FROM video_list WHERE video_id=?", (video_id, ))
        single_video = cur.fetchone()
        if not single_video: 
            print("No such video! ")
            return -1
        # skip unarchived contents
        if (video_id[:2] == '__') and (video_id[-2:] == '__'):
            if sequenced:  
                callback_args = ['flask', 'download-channels', '--callback', single_video['channel_id']]
                subprocess.Popen(callback_args, env=os.environ.copy())
            return 0

        # load config and create download path
        conf_path = current_app.config['DL_CONF_PATH']
        with open(conf_path) as f: 
            conf = yaml.safe_load(f)
        download_path = os.path.join(conf['download_path'], single_video['channel_id'], 'by_upload_date')
        if not os.path.isdir(download_path): 
            os.makedirs(download_path)
        sleep_time = int(conf['sleep_time'])
        slow_mode = True
        if conf['slow_mode'] == 'False': 
            slow_mode = False
        cookie_path = conf['cookie_path']
        if cookie_path == None: 
            cookie_path = ''

        # construct dict for video downloading
        video_info = {
            'url': 'https://www.youtube.com/watch?v='+video_id, 
            'date_path': os.path.join(download_path, single_video['upload_date'][:10])
        }
        # construct download target folder
        if not os.path.isdir(video_info['date_path']): 
            os.makedirs(video_info['date_path'])

        # construct argument for yt-dlp
        dlp_args = [
            'yt-dlp', 
            '--path', video_info['date_path'], 
            '-o', r'%(id)s/%(id)s.%(ext)s',
            '--write-thumbnail', 
            '--write-info-json',
            '--write-description', 
            video_info['url']
        ]

        if os.path.isfile(cookie_path): 
            dlp_args.insert(-2, '--cookies')
            dlp_args.insert(-2, cookie_path)
        # run yt-dlp and display messages, save log if log option is on
        completed_dlp = subprocess.run(dlp_args, capture_output=True)
        dlp_stdout = completed_dlp.stdout.decode('utf-8')
        dlp_stderr = completed_dlp.stderr.decode('utf-8')
        print(dlp_stdout, dlp_stderr)

        if slow_mode and sequenced: 
            sleep_length = random.randint(sleep_time-0.1*sleep_time, sleep_time+0.1*sleep_time)
            for i in range(sleep_length): 
                time.sleep(1)

        if sequenced: 
            callback_args = ['flask', 'download-channels', '--callback', single_video['channel_id']]
            subprocess.Popen(callback_args, env=os.environ.copy())
        else: 
            scan_path = conf['local_videos']
            if scan_path: 
                scan_local_videos(scan_path)


    except: 
        raise
    finally: 
        cur.close()
        os.remove(lock_path)


@click.command('download-channels')
@click.option('--callback', default='')
@with_appcontext
def download_channels_cmd(callback): 
    db = get_db()
    cur = db.cursor()

    if check_lock(): 
        return -1

    try: 
        if callback: 
            channel_id = callback
            cur.execute("SELECT checkpoint_idx FROM channel_list WHERE channel_id=?", (channel_id, ))
            checkpoint_idx = cur.fetchone()['checkpoint_idx']
            cur.execute('UPDATE channel_list SET checkpoint_idx=? WHERE channel_id=?', (checkpoint_idx+1, channel_id))
            db.commit()
        cur.execute('SELECT channel_id FROM channel_list')
        selected_channels = [i['channel_id'] for i in cur.fetchall()]

        def filter_deprecated_channel(single_channel_id): 
            if (single_channel_id[:2] == '__') and (single_channel_id[-2:] == '__'): 
                return False
            else: 
                return True
        channel_list = list(filter(filter_deprecated_channel, selected_channels))
        next_video_id = ''
        for channel in channel_list: 
            cur.execute('SELECT checkpoint_idx FROM channel_list WHERE channel_id=?', (channel, ))
            current_idx = int(cur.fetchone()['checkpoint_idx'])
            cur.execute('SELECT video_id FROM video_list WHERE channel_id=? and upload_idx=?', (channel, current_idx+1))
            searched_next_video = cur.fetchone()
            if searched_next_video:
                next_video_id = searched_next_video['video_id']
                break
        if next_video_id: 
            downloader_args = ['flask', 'download-single', '--video_id', next_video_id, '--sequenced', 'True']
            subprocess.Popen(downloader_args, env=os.environ.copy())
        else: 
            conf_path = current_app.config['DL_CONF_PATH']
            with open(conf_path) as f: 
                conf = yaml.safe_load(f)
            scan_path = conf['local_videos']
            if scan_path: 
                scan_local_videos(scan_path)


    finally: 
        cur.close()
    
