from googleapiclient.discovery import build
import pandas as pd
import isodate 
import datetime
import ast
import os

# # (Development)
# from config import api_key 

# (Production)
api_key = os.environ.get('API_KEY')

# Get credentials and create an API client
youtube = build('youtube', 'v3', developerKey=api_key)

# Get channel info
def get_channel_info(channel_id):
        request = youtube.channels().list(
                part='snippet,contentDetails,statistics',
                id=channel_id
        )
        response = request.execute()

        # Check if channel ID is valid
        if(response['pageInfo']['totalResults'] == 0 or response['items'][0]['statistics']['videoCount'] == '0'):
                return 'error'

        data = {'channel_name': response['items'][0]['snippet']['title'],
                'subscribers': response['items'][0]['statistics']['subscriberCount'],
                'total_views': response['items'][0]['statistics']['viewCount'],
                'videos_count': response['items'][0]['statistics']['videoCount'],
                'playlist_uploads_id': response['items'][0]['contentDetails']['relatedPlaylists']['uploads'],
                'profile_pic_url': response['items'][0]['snippet']['thumbnails']['default']['url'],
                'country': response['items'][0]['snippet']['country'] if 'country' in response['items'][0]['snippet'] else '-'        
        }

        return data

#----//----//----//----//----//----//----//----//----//----//----//----//----//----//

# Get videos from playlist
def get_video_ids(playlist_id, videos_count):
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
        while token != None and int(videos_count)>50:
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
                                'title': str(video['snippet']['title']).replace('&', 'and'), 
                                'description': video['snippet']['description'], 
                                'tags': video['snippet']['tags'] if 'tags' in video['snippet'] else None,
                                'publishedAt': video['snippet']['publishedAt'],
                                'thumbnail_url': video['snippet']['thumbnails']['default']['url'],

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

# Notation for long numbers
def formatNumber(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

def get_channel_stats(channel_id):
        channel_info = get_channel_info(channel_id)

        # Invalid channel ID
        if channel_info == 'error':
                return None, None

        video_ids = get_video_ids(channel_info['playlist_uploads_id'], channel_info['videos_count'])
        video_info = get_video_info(video_ids)


        # Prepare and create CSV -------------//-------------//-------------//
        df = pd.DataFrame(video_info)

        # Converting numeric cols to int   
        numeric_cols = ['viewCount', 'likeCount', 'favoriteCount', 'commentCount']
        df[numeric_cols] = df[numeric_cols].astype(int)

        # Converting date col to date type
        df['publishedAt'] = pd.to_datetime(df['publishedAt'])

        # Converting video duration values from ISO
        df['duration'] = df['duration'].apply(lambda x: isodate.parse_duration(x).total_seconds())

        # Creating CSV File
        df.to_csv('/tmp/download.csv', encoding='utf-8', index=False)


        # Insights -------------//-------------//-------------//-------------//
        insights = {}

        # TOTAL LIKES -------------//-------------//-------------//
        insights['total_likes'] = formatNumber(int(df['likeCount'].sum()))


        # UPLOADS -------------//-------------//-------------//

        total_uploads = df['video_id'].count()

        last_post_day = df['publishedAt'][0]
        first_post_day = df['publishedAt'].iloc[-1]

        delta = last_post_day - first_post_day

        # Uploads per Month
        n_months = delta.days/30
        insights['avg_uploads_per_month'] = round(total_uploads/n_months, 2)

        # Uploads per Week
        n_weeks = delta.days/7
        insights['avg_uploads_per_week'] = round(total_uploads/n_weeks, 2)

        # Uploads per Day
        n_days = delta.days
        insights['avg_uploads_per_day'] = round(total_uploads/n_days, 2)


        # AVG METRICS -------------//-------------//-------------//

        # avg views/video
        insights['avg_views_per_video'] = round(df['viewCount'].median())

        # avg likes/vieo
        insights['avg_likes_per_video'] = round(df['likeCount'].median())

        # avg comments/video
        insights['avg_comments_per_video'] = round(df['commentCount'].median())

        # avg video duration
        insights['avg_video_duration'] = str(datetime.timedelta(seconds = round(df['duration'].median())))


        # ENGAGEMENT RATE -------------//-------------//-------------//
        insights['avg_engagement_rate'] = round((insights['avg_likes_per_video'] + insights['avg_comments_per_video']) / insights['avg_views_per_video'], 2) 


        # TOP 10 HASHTAGS -------------//-------------//-------------//

        all_tags = []

        for tag_group in df[df['tags'].notna()]['tags']:
                if tag_group:
                        all_tags.append(ast.literal_eval(str(tag_group)))    


        flat_list = [item for sublist in all_tags for item in sublist]

        top_hashtags = pd.Series(flat_list).value_counts()[:10].to_dict()

        insights['top_hashtags'] = top_hashtags


        # TOP VIDEOS -------------//-------------//-------------//

        top_10_video = df.sort_values(by=['viewCount'], ascending=False)[:10][['video_id','title', 'thumbnail_url', 'viewCount', 'likeCount', 'commentCount', 'duration']]

        top_videos = []

        for i in range(0, len(top_10_video)-1):
                video = top_10_video.iloc[i]

                data = {
                        'video_url': 'https://www.youtube.com/watch?v=' + video['video_id'],
                        'title': video['title'],
                        'thumbnail_url': video['thumbnail_url'],
                        'thumbnail_url_hq': str(video['thumbnail_url']).replace('default', 'hqdefault'),
                        'viewCount': str(formatNumber(video['viewCount'])),
                        'likeCount': str(formatNumber(video['likeCount'])),
                        'commentCount': str(formatNumber(video['commentCount'])),
                        'engagement_rate': str(round((video['likeCount']+video['commentCount'])/video['viewCount'], 2)),
                        'duration': str(datetime.timedelta(seconds = round(video['duration'])))
                }
                top_videos.append(data)
        
        insights['top_videos'] = top_videos


        # Week Days Upload distribution -------------//-------------//-------------//
        weekdays_count = df['publishedAt'].apply(lambda x: x.weekday()).value_counts().to_dict()

        weekdays_dist = {}

        weekdays_dist['Monday'] = weekdays_count[0] if 0 in weekdays_count else 0
        weekdays_dist['Tuesday'] = weekdays_count[1] if 1 in weekdays_count else 0
        weekdays_dist['Wednesday'] = weekdays_count[2] if 2 in weekdays_count else 0
        weekdays_dist['Thursday'] = weekdays_count[3] if 3 in weekdays_count else 0
        weekdays_dist['Friday'] = weekdays_count[4] if 4 in weekdays_count else 0
        weekdays_dist['Saturday'] = weekdays_count[5] if 5 in weekdays_count else 0
        weekdays_dist['Sunday'] = weekdays_count[6] if 6 in weekdays_count else 0

        
        insights['weekdays_dist'] = weekdays_dist


        # Upload Time distribution -------------//-------------//-------------//
        dates = []
        times = []

        for date_time in df['publishedAt']:
                dates.append(date_time.strftime('%Y-%m-%d'))
                times.append(date_time.strftime('%H:%M'))
        
        dates.reverse()
        times.reverse()

        insights['dates'] = dates
        insights['times'] = times
        

        # Format channel info numbers to dot notation -------------//-------------//-------------//
        channel_info['subscribers'] = formatNumber(int(channel_info['subscribers']))
        channel_info['total_views'] = formatNumber(int(channel_info['total_views']))
        channel_info['videos_count'] = formatNumber(int(channel_info['videos_count']))
        insights['avg_views_per_video'] = formatNumber(insights['avg_views_per_video'])
        insights['avg_likes_per_video'] = formatNumber(insights['avg_likes_per_video'])
        insights['avg_comments_per_video'] = formatNumber(insights['avg_comments_per_video'])

        return channel_info, insights