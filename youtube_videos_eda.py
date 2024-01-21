import pandas as pd
import plotly_express as px
import numpy as np
from dateutil import parser
import isodate
# Google API
from googleapiclient.discovery import build
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import streamlit as st
st.set_page_config(page_title='Myanmar Telemedicine Channels',page_icon=':bar_chart',layout='wide')
st.title('Exploratory Data Analysing Using Youtube Video Data from Most Popular Myanmar Telemedicine Channels')

st.header('Introduction', divider='red')
st.caption("YouTube, a dynamic platform processing over 3 billion searches monthly, stands as the second-largest search engine globally. Deciphering the elements that contribute to a video's success on YouTube poses a challenge. In this exploration, we delve into the statistical landscape of the top five Telemedicine YouTube channels from Myanmar, unraveling the mysteries behind video views, subscribers, and more.")


api_key = 'AIzaSyARZvA4lT3s1w8s-E3HePFZ4sh_eivCPz0'
channel_id = 'UCwaed_IVBHjym8YVXhE9vLA'
channel_ids = ['UCwaed_IVBHjym8YVXhE9vLA', #myancare
               'UC3VMnv-y9D4PdEn29HE_Dtg', #mydoctor
               'UC_LoVzylC4pqCw8bJlquw1g', #zwaka
               'UC2IbWQXYC5SOQgWPKK7rvmg', #healtppy
               'UCHYkIkrhNMJQF2HzKbaTr5A', #ondoctor
]

youtube = build('youtube','v3', developerKey=api_key)

#function to get channel statistics 

def get_channel_stats(youtube, channel_ids):
        all_data = []
        request = youtube.channels().list(
            part='snippet,contentDetails,statistics',
            id=','.join(channel_ids))
        response = request.execute()

        for i in range(len(response['items'])):
            data = dict(channel_name = response['items'][i]['snippet']['title'],
                        subscribers = response['items'][i]['statistics']['subscriberCount'],
                        views = response['items'][i]['statistics']['viewCount'],
                        total_video = response['items'][i]['statistics']['videoCount'],
                        playlistId = response['items'][i]['contentDetails']['relatedPlaylists']['uploads'])
            all_data.append(data)
        return pd.DataFrame(all_data)

def get_video_ids(youtube, playlist_id):
        """
        Get list of video IDs of all videos in the given playlist
        Params:
        
        youtube: the build object from googleapiclient.discovery
        playlist_id: playlist ID of the channel
        
        Returns:
        List of video IDs of all videos in the playlist
        
        """
        
        request = youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId = playlist_id,
                    maxResults = 50)
        response = request.execute()
        
        video_ids = []
        
        for i in range(len(response['items'])):
            video_ids.append(response['items'][i]['contentDetails']['videoId'])
            
        next_page_token = response.get('nextPageToken')
        more_pages = True
        
        while more_pages:
            if next_page_token is None:
                more_pages = False
            else:
                request = youtube.playlistItems().list(
                            part='contentDetails',
                            playlistId = playlist_id,
                            maxResults = 50,
                            pageToken = next_page_token)
                response = request.execute()
        
                for i in range(len(response['items'])):
                    video_ids.append(response['items'][i]['contentDetails']['videoId'])
                
                next_page_token = response.get('nextPageToken')
            
        return video_ids

def get_video_details(youtube, video_ids):
        """
        Get video statistics of all videos with given IDs
        Params:
        
        youtube: the build object from googleapiclient.discovery
        video_ids: list of video IDs
        
        Returns:
        Dataframe with statistics of videos, i.e.:
            'channelTitle', 'title', 'description', 'tags', 'publishedAt'
            'viewCount', 'likeCount', 'favoriteCount', 'commentCount'
            'duration', 'definition', 'caption'
        """
            
        all_video_info = []
        
        for i in range(0, len(video_ids), 50):
            request = youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=','.join(video_ids[i:i+50])
            )
            response = request.execute() 

            for video in response['items']:
                stats_to_keep = {'snippet': ['channelTitle', 'title', 'description', 'tags', 'publishedAt'],
                                'statistics': ['viewCount', 'likeCount', 'favouriteCount', 'commentCount'],
                                'contentDetails': ['duration', 'definition', 'caption']
                                }
                video_info = {}
                video_info['video_id'] = video['id']

                for k in stats_to_keep.keys():
                    for v in stats_to_keep[k]:
                        try:
                            video_info[v] = video[k][v]
                        except:
                            video_info[v] = None

                all_video_info.append(video_info)
                
        return pd.DataFrame(all_video_info)

def get_comments_in_videos(youtube, video_ids):
        """
        Get top level comments as text from all videos with given IDs (only the first 10 comments due to quote limit of Youtube API)
        Params:
        
        youtube: the build object from googleapiclient.discovery
        video_ids: list of video IDs
        
        Returns:
        Dataframe with video IDs and associated top level comment in text.
        
        """
        all_comments = []
        
        for video_id in video_ids:
            try:   
                request = youtube.commentThreads().list(
                    part="snippet,replies",
                    videoId=video_id
                )
                response = request.execute()
            
                comments_in_video = [comment['snippet']['topLevelComment']['snippet']['textOriginal'] for comment in response['items'][0:10]]
                comments_in_video_info = {'video_id': video_id, 'comments': comments_in_video}

                all_comments.append(comments_in_video_info)
                
            except: 
                # When error occurs - most likely because comments are disabled on a video
                print('Could not get comments for video ' + video_id)
            
        return pd.DataFrame(all_comments)

channel_data = get_channel_stats(youtube, channel_ids)
channel_data = pd.DataFrame(channel_data)

# Convert count columns to numeric columns
numeric_cols = ['subscribers', 'views', 'total_video']
channel_data[numeric_cols] = channel_data[numeric_cols].apply(pd.to_numeric, errors='coerce')

# Group by 'channel_name' and sum 'subscribers'
import streamlit as st
import plotly.express as px
from plotly.subplots import make_subplots

# Assuming 'channel_data' is your DataFrame

table1 = channel_data.groupby('channel_name')['subscribers'].sum().sort_values(ascending=False)
table1 = pd.DataFrame(table1)

# Group by 'channel_name' and sum 'views'
table2 = channel_data.groupby('channel_name')['views'].sum().sort_values(ascending=False)
table2 = pd.DataFrame(table2)

# Set 'channel_name' as the index
table1 = table1.reset_index()
table2 = table2.reset_index()

fig = make_subplots(rows=1, cols=2, subplot_titles=['Subscribers Distribution', 'Views Distribution'])

fig1 = px.bar(table1, x='channel_name', y='subscribers', labels={'subscribers': 'Total Subscribers'})
fig1.update_layout(width=1500, height=500)
fig1.update_yaxes(range=[0, max(table1['subscribers']) * 1.1])  # Adjust 1.1 as needed

fig2 = px.bar(table2, x='channel_name', y='views', labels={'views': 'Total Views'})
fig2.update_layout(width=1500, height=500)
fig2.update_yaxes(range=[0, max(table2['views']) * 1.1])  # Adjust 1.1 as needed

# Update subplots
fig.add_trace(fig1['data'][0], row=1, col=1)
fig.add_trace(fig2['data'][0], row=1, col=2)

# Update layout
fig.update_layout(showlegend=False,
                  xaxis_title="Channel Name",
                  yaxis_title="Total Subscribers",
                  xaxis2_title="Channel Name",
                  yaxis2_title="Total Views",
                    # Set the width to 1000 pixels
                height=500)

# Show the plot
st.plotly_chart(fig,use_container_width=True)

st.divider()

st.header('Get video statistics for all the channels')
st.caption('In the next step, we will obtain the video statistics for all the channels. In total, we obtained 315 videos as seen in below.')

# Create empty lists to store DataFrames temporarily
video_dfs = []

for c in channel_data['channel_name'].unique():
    print("Getting video information from channel: " + c)
    playlist_id = channel_data.loc[channel_data['channel_name'] == c, 'playlistId'].iloc[0]
    video_ids = get_video_ids(youtube, playlist_id)

    # Get video data and comments data
    video_data = get_video_details(youtube, video_ids)
    

    # Append DataFrames to the lists
    video_dfs.append(video_data)
    

# Concatenate DataFrames after the loop
video_df = pd.concat(video_dfs, ignore_index=True)

cols = ['viewCount', 'likeCount', 'favouriteCount', 'commentCount']
video_df[cols] = video_df[cols].apply(pd.to_numeric, errors='coerce', axis=1)

# Create publish day (in the week) column
video_df['publishedAt'] =  video_df['publishedAt'].apply(lambda x: parser.parse(x)) 
video_df['pushblishDayName'] = video_df['publishedAt'].apply(lambda x: x.strftime("%A")) 

# convert duration to seconds
video_df['durationSecs'] = video_df['duration'].apply(lambda x: isodate.parse_duration(x))
video_df['durationSecs'] = video_df['durationSecs'].astype('timedelta64[s]')

# Add number of tags
video_df['tagsCount'] = video_df['tags'].apply(lambda x: 0 if x is None else len(x))

# Comments and likes per 1000 view ratio
video_df['likeRatio'] = video_df['likeCount']/ video_df['viewCount'] * 1000
video_df['commentRatio'] = video_df['commentCount']/ video_df['viewCount'] * 1000

# Title character length
video_df['titleLength'] = video_df['title'].apply(lambda x: len(x))

fig = px.box(video_df, x = "channelTitle", y = "viewCount",  title='Distribution of Views per Channel',
             labels={'channelTitle':'Channel Titles',
                     'viewCount':'Total View'})
st.plotly_chart(fig,use_container_width=True)

st.divider()

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Create subplots with 1 row and 2 columns
fig = make_subplots(rows=1, cols=2, subplot_titles=["Comment Count vs View Count", "Like Count vs View Count"])

# Add scatter plots to the subplots
scatter1 = go.Scatter(x=video_df["commentCount"], y=video_df["viewCount"], mode="markers", name="Comment Count vs View Count")
scatter2 = go.Scatter(x=video_df["likeCount"], y=video_df["viewCount"], mode="markers", name="Like Count vs View Count")

# Add traces to the subplots
fig.add_trace(scatter1, row=1, col=1)
fig.add_trace(scatter2, row=1, col=2)

# Update layout
fig.update_layout(title_text="Subplots of Comment Count and Like Count vs View Count",
                  xaxis_title="Total Comment Count",
                  yaxis_title="Total View Count",
                  xaxis2_title="Total Like Count",
                  yaxis2_title="Total View Count",
                width=1000,  # Set the width to 1000 pixels
                height=500,
                legend=dict(orientation="h", y=-0.2))

# Show the plot
st.plotly_chart(fig,use_container_width=True)

st.divider()

# Filter based on duration in seconds
filtered_df = video_df[video_df['durationSecs'].dt.seconds < 10000]

# Convert timedelta to seconds
filtered_df['durationSecs_numeric'] = filtered_df['durationSecs'].dt.total_seconds()

# Create the histogram with Plotly Express
fig = px.histogram(filtered_df, x="durationSecs_numeric", nbins=100, title="Histogram of Video Durations")
fig.update_layout(title_text="Histogram of Video Durations")

# Show the plot
st.plotly_chart(fig,use_container_width=True)

st.divider()


# Create subplots with 1 row and 2 columns
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(rows=1, cols=2, subplot_titles=["Duration Count vs Comment Count", "Duration Count vs Like Count"])

# Add scatter plots to the subplots
video_df['duration_in_seconds'] = video_df['durationSecs'].dt.seconds
scatter1 = go.Scatter(x=video_df["duration_in_seconds"], y=video_df["commentCount"], mode="markers", 
                      name="Duration Count vs Comment Count")
scatter2 = go.Scatter(x=video_df["duration_in_seconds"], y=video_df["likeCount"], mode="markers", 
                      name="Duration Count vs Like Count")

# Add traces to the subplots
fig.add_trace(scatter1, row=1, col=1)
fig.add_trace(scatter2, row=1, col=2)

# Update layout
fig.update_layout(title_text="Subplots of Comment Count and Like Count vs Duration Count",
                  xaxis_title="Duration in Seconds",
                  yaxis_title="Total Comment Count",
                  xaxis2_title="Duration in Seconds",
                  yaxis2_title="Total Like Count",
                  width=1000,  # Set the width to 1500 pixels
                  height=500,
                  legend=dict(orientation="h", y=-0.2))  # Set the height to 500 pixels

# Show the plot
st.plotly_chart(fig,use_container_width=True)

st.divider()

fig = make_subplots(rows=1, cols=2, subplot_titles=['Does title length matter for views?', 'Number of Tags Vs Views'])

fig1 = px.scatter(video_df, x = "titleLength", y = "viewCount",
                 labels={'titleLength':'Video Title Length',
                     'viewCount':'Total View'})
st.caption('There is no clear relationship between title length and views as seen the scatterplot below, but most-viewed videos tend to have average title length of 40-80 characters.')

fig2 = px.scatter(video_df, x = "tagsCount", y = "viewCount",
                 labels={'tagsCount':'Video Tags Count',
                     'viewCount':'Total View'})

# Update subplots
fig.add_trace(fig1['data'][0], row=1, col=1)
fig.add_trace(fig2['data'][0], row=1, col=2)

# Update layout
fig.update_layout(showlegend=False,
                  xaxis_title="Title Length",
                  yaxis_title="Total View",
                  xaxis2_title="Tags Count",
                  yaxis2_title="Total View",
                  height=500)

# Show the plot
st.plotly_chart(fig,use_container_width=True)

st.divider()

st.header('Which day in the week are most videos uploaded?')

# Assuming 'pushblishDayName' is a categorical variable
weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
tb = video_df['pushblishDayName'].value_counts().reindex(weekdays, fill_value=0)

# Create the bar chart with Plotly Express
fig = px.bar(x=tb.index, y=tb.values, labels={'y': 'Count'}, title="Video Publication Days Count")
fig.update_layout(title_text="Video Publication Days Count", xaxis_title="Day of Week", yaxis_title="Count",height=500)

# Show the plot
st.plotly_chart(fig,use_container_width=True)

st.caption("It's interesting to see that more videos are uploaded on Mondays to Fridays. Fewer videos are uploaded during the weekend.")

st.divider()

st.header('Ethics of data source')
st.caption("According to Youtube API's guide, the usage of Youtube API is free of charge given that your application send requests within a quota limit. The YouTube Data API uses a quota to ensure that developers use the service as intended and do not create applications that unfairly reduce service quality or limit access for others. The default quota allocation for each application is 10,000 units per day, and you could request additional quota by completing a form to YouTube API Services if you reach the quota limit. Since all data requested from Youtube API is public data which everyone on the Internet can see on Youtube, there is no particular privacy issues as far as I am concerned. In addition, the data is obtained only for research purposes in this case and not for any commercial interests.")
