# -*- coding: utf-8 -*-

from flask import current_app

from vtbarchiver.db_functions import get_db
from vtbarchiver.misc_funcs import build_youtube_api


def fetch_channel(channel_id: str)->dict: 
    """update channel information of the given channel from youtube api

    Args:
        channel_id (string): Channel ID

    Raises:
        ValueError: If the channel ID is not applicable, the error is raised

    Returns:
        dict: channel overview dict
    """
    youtube = build_youtube_api()
    

    db = get_db()
    try: 
        # connect to db and create table for channel_list if not existing
        cur = db.cursor()

        # get channel detail
        request = youtube.channels().list(
            id = channel_id, 
            part = "snippet", 
            maxResults = 1
        )
        response = request.execute()
        if response['pageInfo']['totalResults']: 
            channel_info = response['items'][0]['snippet']
        else: 
            raise ValueError('No such channel')

        cur.execute('SELECT id FROM channel_list WHERE channel_id=?', (channel_id,))
        existing_id = cur.fetchall()
        
        if existing_id: 
            cur.execute('UPDATE channel_list SET channel_name=?, channel_description=?, thumb_url=? WHERE id=?', (channel_info['title'], channel_info['description'], channel_info['thumbnails']["medium"]["url"], existing_id[0][0]))
        else: 
            cur.execute('INSERT INTO channel_list (channel_id, channel_name, channel_description, thumb_url) VALUES (?, ?, ?, ?)', (channel_id, channel_info['title'], channel_info['description'], channel_info['thumbnails']["medium"]["url"]))
        db.commit()
        return {'channelId': channel_id, 'channelName': channel_info['title'], 'thumbUrl': channel_info['thumbnails']["medium"]["url"]}
    
    except: 
        return {'channelId': '', 'channelName': '', 'thumbUrl': ''}

    finally: 
        cur.close()


def update_checkpoint(channel_id: str, checkpoint_idx=0, video_id='', offset=0)->int: 
    """Update checkpoint index of a channel. Priority: checkpoint index > video ID > offset

    Args:
        channel_id (str): channel ID to be updated
        checkpoint_idx (int, optional): new checkpoint index. Defaults to 0.
        video_id (str, optional): video ID of the new checkpoint. Defaults to ''.
        offset (int, optional): offset to current checkpoint index. Defaults to 0.

    Returns:
        int: number of channels updated, -1 for invalid input
    """
    # return -1 if no new checkpoint provided
    if (not checkpoint_idx) and (not video_id) and (not offset): 
        return -1

    db = get_db()
    try: 
        cur = db.cursor()

        # get new index
        if checkpoint_idx: 
            new_checkpoint_idx = int(checkpoint_idx)
        elif video_id: 
            cur.execute('SELECT upload_idx FROM video_list WHERE video_id=?', (video_id,))
            upload_idx_searching = cur.fetchall()
            if not upload_idx_searching: 
                return -1
            new_checkpoint_idx = upload_idx_searching[0][0]
        elif offset: 
            cur.execute('SELECT checkpoint_idx FROM channel_list WHERE channel_id=?', (channel_id,))
            old_checkpoint = cur.fetchall()[0][0]
            new_checkpoint_idx = int(old_checkpoint) + int(offset)
            if new_checkpoint_idx < 0: 
                return -1

        # update the table
        cur.execute('UPDATE channel_list SET checkpoint_idx=? WHERE channel_id=?', (new_checkpoint_idx, channel_id))
        return cur.rowcount

    except: 
        raise

    finally: 
        cur.close()
        db.commit()

