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

'''
def single_download_cycle(channel_id: str, download_path, cookie_path='', verbosity=0): 
    db = get_db()
    cur = db.cursor()
    try: 
        
        # retrieve checkpoint from channel_list
        cur.execute('SELECT channel_name, checkpoint_idx FROM channel_list WHERE channel_id=?', (channel_id, ))
        searched_checkpoint_idx = cur.fetchall()
        if not searched_checkpoint_idx: 
            raise NameError('No valid channel data')
        channel_name = searched_checkpoint_idx[0][0]
        checkpoint_idx = searched_checkpoint_idx[0][1]

        # retrieve video data for download
        cur.execute('SELECT video_id, upload_date, title FROM video_list WHERE channel_id=? and upload_idx=?', (channel_id, checkpoint_idx+1))
        searched_video_info = cur.fetchall()
        if not searched_video_info: 
            print("%s %s: all video downloaded" % (channel_name, channel_id))
            return 0
        video_info = {
            'url': 'https://www.youtube.com/watch?v='+searched_video_info[0][0], 
            'date_path': os.path.join(download_path, searched_video_info[0][1][:10])
        }
        
        # construct download target folder
        if not os.path.isdir(video_info['date_path']): 
            os.makedirs(video_info['date_path'])

        # construct argument for yt-dlp
        dlp_args = [
            'yt-dlp', 
            '--path', video_info['date_path'], 
            '--write-thumbnail', 
            video_info['url']
        ]

        if os.path.isfile(cookie_path): 
            dlp_args.insert(-2, '--cookies')
            dlp_args.insert(-2, cookie_path)
        # run yt-dlp and display messages, save log if log option is on
        completed_dlp = subprocess.run(dlp_args, capture_output=True)
        dlp_stdout = completed_dlp.stdout.decode('utf-8')
        dlp_stderr = completed_dlp.stderr.decode('utf-8')
        if verbosity >= 2: 
            print(dlp_stdout, dlp_stderr)
        elif verbosity >= 1: 
            if dlp_stderr: 
                print(dlp_stderr)
            print("%s %s: %s %s on %s has finished. " % (channel_name, channel_id, searched_video_info[0][0], searched_video_info[0][2]))
        else: 
            if dlp_stderr: 
                print(dlp_stderr)

        # update checkpoint
        cur.execute('UPDATE channel_list SET checkpoint_idx=? WHERE channel_id=?', (checkpoint_idx+1, channel_id))
        return 1
    except: 
        raise
    finally: 
        cur.close()
        db.commit()


def download_list(channel_id: str, auto_continue=True, verbosity=0): 

    #args: channel_id (str); auto_continue (Boolean); verbose (int)
    #Download all videos in video_list for a given channel; if auto_continue is set to False, confirmation is required before next download and slow mode would not work

    # load config file
    conf_path = current_app.config['DL_CONF_PATH']
    with open(conf_path) as f: 
        conf = yaml.safe_load(f)
    download_path = os.path.join(conf['download_path'], channel_id, 'by_upload_date')
    if not os.path.isdir(download_path): 
        os.makedirs(download_path)
    sleep_time = int(conf['sleep_time'])
    slow_mode = True
    if conf['slow_mode'] == 'False': 
        slow_mode = False
    cookie_path = conf['cookie_path']
    if cookie_path == None: 
        cookie_path = ''
    
    # keep download until all videos downloaded or manually stopped
    while True: 
        # download
        continue_flag = single_download_cycle(channel_id, download_path, cookie_path, verbosity=verbosity)
        if not continue_flag: 
            return 0
        
        # ask for stop if not auto_continue
        if not auto_continue: 
            while True: 
                ask_continue = input('Continue? y|n')
                if ask_continue.lower() in ('y', 'n'): 
                    break
            if ask_continue.lower == 'n': 
                return 0
        # sleep if in slow mode
        if slow_mode and auto_continue: 
            sleep_length = random.randint(sleep_time-0.1*sleep_time, sleep_time+0.1*sleep_time)
            for i in range(sleep_length): 
                time.sleep(1)
    

def download_channels(auto_continue=True, verbosity=0): 
    db = get_db()
    cur = db.cursor()
    try: 

        # get channel list
        cur.execute('SELECT channel_id FROM channel_list')
        searched_channel_list = cur.fetchall()
        if not searched_channel_list: 
            raise NameError('No valid channel data')
        channel_list = [i[0] for i in searched_channel_list]

        for channel_id in channel_list: 
            download_list_result = download_list(channel_id, auto_continue=auto_continue, verbosity=verbosity)
        
        return 0

    except: 
        raise

    finally: 
        cur.close()
'''

def check_lock(): 
    lock_path = os.path.join(current_app.root_path, 'download.lock')
    return os.path.isfile(lock_path)
'''
@click.command('download-channels')
@with_appcontext
def download_channels_command(): 
    my_pid = os.getpid()
    print(my_pid)
    if not check_lock():
        lock_path = os.path.join(current_app.root_path, 'download.lock') 
        with open(lock_path, 'w') as f: 
            f.write(str(my_pid))
        try: 
            download_channels(verbosity=2)
        finally: 
            os.remove(lock_path)

'''





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
            '--write-thumbnail', 
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

    finally: 
        cur.close()
    
