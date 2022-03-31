# -*- coding: utf8 -*- 

from flask import current_app

from vtbarchiver.channel_records import fetch_channel
from vtbarchiver.db_functions import get_db
from vtbarchiver.misc_funcs import build_youtube_api, tag_title


class VideoInfo(): 
    '''
    Attributions: video_id, title, upload_date
    '''
    def __init__(self, video_id: str, title: str, upload_date: str, thumb_url: str) -> None:
        '''
        args: video_id (str), title (str), upload_date (str);
        Store video info in a VideoInfo object
        '''
        self.video_id = video_id
        self.title = title
        self.upload_date = upload_date
        self.thumb_url = thumb_url
        self.duration = ''


def retrieve_video_info(video_dict: dict): 
    '''
    video_dict: a single video's information diction getting from youtube playlist item api
    Return a VideoInfo object
    '''
    video_info = VideoInfo(
        video_id=video_dict["snippet"]["resourceId"]["videoId"], 
        title=video_dict["snippet"]["title"], 
        upload_date=video_dict["snippet"]["publishedAt"], 
        thumb_url=video_dict["snippet"]["thumbnails"]["high"]["url"]
    )
    return video_info


def fetch_uploaded_list(channel_id: str): 
    '''
    Args: channel_id (str)
    Fetching uploaded video list from youtube for a given channel
    '''

    youtube = build_youtube_api()

    # connect to db 
    db = get_db()
    try: 
        cur = db.cursor()
        # retrieve local video list
        cur.execute('SELECT id, video_id FROM video_list WHERE channel_id=? ORDER BY upload_idx DESC', (channel_id, ))
        existing_video_list = cur.fetchall()
        
        # get channel detail => upload video playlist
        request = youtube.channels().list(
            id = channel_id, 
            part = "contentDetails", 
            maxResults = 1
        )
        response = request.execute()
        uploads_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # get detail of videos inside upload playlist
        request = youtube.playlistItems().list(
            part="snippet", 
            playlistId=uploads_id, 
            maxResults=50, 
        )

        # keep ask for next page if there is more results and not fetched
        all_new_fetched = False
        while request: 
            response = request.execute()
            for single_video in response["items"]: 
                if single_video['snippet']['resourceId']['kind'] == 'youtube#video': 
                    single_video_info = retrieve_video_info(single_video)
                    # if returned video info match existing video info, stop
                    if single_video_info.video_id in [i[1] for i in existing_video_list]: 
                        all_new_fetched = True
                        break
                    
                    duration_request = youtube.videos().list(
                        part="contentDetails", 
                        id=single_video_info.video_id
                    )
                    duration_response = duration_request.execute()
                    single_video_info.duration = duration_response['items'][0]['contentDetails']['duration']

                    cur.execute('INSERT INTO video_list (video_id, title, upload_date, duration, channel_id, thumb_url) VALUES (?, ?, ?, ?, ?, ?)', (single_video_info.video_id, single_video_info.title, single_video_info.upload_date, single_video_info.duration, channel_id, single_video_info.thumb_url))

                    tagged_title = tag_title(single_video_info.title)
                    cur.execute('INSERT INTO search_video (video_id, title, tagged_title) VALUES (?, ?, ?)', (single_video_info.video_id, single_video_info.title, tagged_title))
            if all_new_fetched: 
                break
            request = youtube.playlistItems().list_next(request, response)
        cur.execute('SELECT id FROM video_list WHERE channel_id=? ORDER BY upload_date', (channel_id, ))
        id_by_date = cur.fetchall()
        for upload_idx in range(len(id_by_date)): 
            cur.execute('UPDATE video_list SET upload_idx=? WHERE id=?', (upload_idx+1, id_by_date[upload_idx][0]))
    except: 
        raise
    finally: 
        cur.close()
        db.commit()


def add_talent_name(channel_id):
    db = get_db()
    cur = db.cursor()
    try: 
        cur.execute('SELECT talent_name FROM channel_list WHERE channel_id = ?', (channel_id, ))
        talent_name = cur.fetchone()['talent_name']
        cur.execute('SELECT vl.video_id vl_id, tp.talent_name tp_name, tp.video_id tp_id FROM video_list vl LEFT OUTER JOIN talent_participation tp ON vl.video_id = tp.video_id WHERE vl.channel_id=?', (channel_id, ))
        video_talent_list = cur.fetchall()
        for video_talent in video_talent_list: 
            if (video_talent['tp_id'] == None) or (video_talent['tp_name'] == ''): 
                cur.execute('INSERT INTO talent_participation (talent_name, video_id) VALUES (?, ?)', (talent_name, video_talent['vl_id']))
                cur.execute('UPDATE search_video SET talents=? WHERE video_id=?', ('%s;'%talent_name, video_talent['vl_id']))
        db.commit()
    except: 
        raise
    finally: 
        cur.close()




def fetch_all(): 
    db = get_db()
    try: 
        cur = db.cursor()

        # get channel list
        cur.execute('SELECT channel_id FROM channel_list')
        searched_channel_list = cur.fetchall()
        if not searched_channel_list: 
            raise NameError('No valid channel data')
        channel_list = [i[0] for i in searched_channel_list]

        for channel_id in channel_list: 
            fetch_channel(channel_id)
            fetch_uploaded_list(channel_id)
            add_talent_name(channel_id)
        
        return 0

    except: 
        raise
    
    finally: 
        cur.close()

