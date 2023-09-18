from googleapiclient.discovery import build
import pandas as pd
import isodate 
from config import api_key, api_service_name, api_version

# Get credentials and create an API client
youtube = build(api_service_name, api_version, developerKey=api_key)

# Get channel stats
def get_channel_info(channel_id):
        request = youtube.channels().list(
                part='snippet,contentDetails,statistics',
                id=channel_id
        )
        response = request.execute()

        data = {'channel_name': response['items'][0]['snippet']['title'],
                'subscribers': response['items'][0]['statistics']['subscriberCount'],
                'total_views': response['items'][0]['statistics']['viewCount'],
                'videos_count': response['items'][0]['statistics']['videoCount'],
                'playlist_uploads_id': response['items'][0]['contentDetails']['relatedPlaylists']['uploads'],
                'profile_pic_url': response['items'][0]['snippet']['thumbnails']['default']['url'],
                'country': response['items'][0]['snippet']['country']         
        }

        return data

#----//----//----//----//----//----//----//----//----//----//----//----//----//----//

# Get videos from playlist
def get_video_ids(playlist_id):
        video_ids = []

        request = youtube.playlistItems().list(
                part="snippet,contentDetails",
                maxResults=50,
                playlistId=playlist_id
        )
        response = request.execute()

        for item in response['items']:
                video_ids.append(item['contentDetails']['videoId'])


        # Get next page results
        token = ''
        while token != None:
                request = youtube.playlistItems().list(
                part="snippet,contentDetails",
                maxResults=50,
                playlistId=playlist_id,
                pageToken=response.get('nextPageToken')
                )
                response = request.execute()

                for item in response['items']:
                        video_ids.append(item['contentDetails']['videoId'])

                token = response.get('nextPageToken')
        
        return video_ids

#----//----//----//----//----//----//----//----//----//----//----//----//----//----//

# Get video info by ID
def get_video_info(video_ids):
        all_videos_info = []

        for i in range(0, len(video_ids), 50):
                request = youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_ids[i:i+50]
                )
                response = request.execute()

                for video in response['items']:
                        info = {'video_id': video['id'],   
                                # info                            
                                'channelTitle': video['snippet']['channelTitle'], 
                                'title': video['snippet']['title'], 
                                'description': video['snippet']['description'], 
                                'tags': video['snippet']['tags'] if 'tags' in video['snippet'] else None,
                                'publishedAt': video['snippet']['publishedAt'],

                                # statistics
                                'viewCount': video['statistics']['viewCount'],
                                'likeCount': video['statistics']['likeCount'] if 'likeCount' in video['statistics'] else 0,
                                'favoriteCount': video['statistics']['favoriteCount'],
                                'commentCount': video['statistics']['commentCount'] if 'commentCount' in video['statistics'] else 0,

                                # content details
                                'duration': video['contentDetails']['duration'],
                                'definition': video['contentDetails']['definition'], 
                        }

                        all_videos_info.append(info)

        return all_videos_info



#----//----//----//----//----//----//----//----//----//----//----//----//----//----//

# Get comments by video ID
def get_all_comments(video_ids):
        all_comments = []

        for video_id in video_ids:
                request = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id
                )
                response = request.execute()
                comments = []
                for item in response['items']:
                        comments.append(item['snippet']['topLevelComment']['snippet']['textOriginal'])

                comments_in_video = {
                        'video_id': video_id,
                        'comments': comments
                }

                all_comments.append(comments_in_video)

        return all_comments

#----//----//----//----//----//----//----//----//----//----//----//----//----//----//

# comments = get_all_comments(video_ids)
# print(pd.DataFrame(comments))

def get_channel_stats(channel_id):
    channel_info = get_channel_info(channel_id)

    video_ids = get_video_ids(channel_info['playlist_uploads_id'])

    video_info = get_video_info(video_ids)

    df = pd.DataFrame(video_info)

    # Converting numeric cols to int
    numeric_cols = ['viewCount', 'likeCount', 'favoriteCount', 'commentCount']
    df[numeric_cols] = df[numeric_cols].astype(int)

    # Converting date col to date type
    df['publishedAt'] = pd.to_datetime(df['publishedAt'])

    # Converting video duration values from ISO
    df['duration'] = df['duration'].apply(lambda x: isodate.parse_duration(x).total_seconds())
       
    # Creating CSV File
    df.to_csv('output/download.csv', encoding='utf-8')

    return channel_info, video_info