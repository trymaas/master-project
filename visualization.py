import pandas as pd
import json
import streamlit as st
import os
import plotly_express as px
import numpy as np
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from pathlib import Path
import re


def json_reader_content(json_file):
    bytes_data = json_file.read()
    string_data = bytes_data.decode("utf-8")
    data = json.loads(string_data)
    #df = pd.DataFrame()

    """if (len(data) == 1):
        return"""
    if json_file.name == 'ads_viewed.json':
        df = pd.json_normalize(data["impressions_history_ads_seen"])
        return df, "ads"
    elif json_file.name == 'posts_viewed.json':
        df = pd.json_normalize(data["impressions_history_posts_seen"]) 
        return df, "posts"
    else:
        df = pd.json_normalize(data["impressions_history_videos_watched"])
        return df, "videos"
    #st.write(df)
    """df = df.drop(labels=['title', 'string_map_data.Search.href',  
                        'string_map_data.Search.timestamp', 'string_map_data.Time.href',
                        'string_map_data.Time.value'], axis=1)"""

def json_reader_searches(json_file):

    bytes_data = json_file.read()
    string_data = bytes_data.decode("utf-8")
    data = json.loads(string_data)
    df = pd.json_normalize(data["searches_user"])
    df = df.drop(labels=['title', 'string_map_data.Search.href',  
                        'string_map_data.Search.timestamp', 'string_map_data.Time.href'], axis=1)
    #st.write(df)

    return df

def visualize_searches(json_files):
    st.title("All your searches on instagram")
    searches = []
    for item in json_files:
        df = json_reader_searches(item)
        searches.append(df)
    try:
        searches = pd.concat(searches)
    except ValueError:
        st.error("Not correct file, please choose another")
        return
    start_time, end_time = get_times(searches)
    st.write("This data was collected between ", start_time, " and ", end_time)
    total_searches = searches["string_map_data.Search.value"].value_counts()
    #st.write(type(total_searches))
    st.write(total_searches)
    fig = px.pie(total_searches, names=total_searches.index, values="string_map_data.Search.value",
                width=800, height=800)
    st.plotly_chart(fig)

def visualize_seen_content(json_files):
    ads, posts, videos = [], [], []
    for item in json_files:
        df, option = json_reader_content(item)
        if option == "ads":
            ads.append(df)
        elif option == "posts":
            posts.append(df)
        elif option == "videos":
            videos.append(df)
    try:
        ads = pd.concat(ads)
        posts = pd.concat(posts)
        videos = pd.concat(videos)
    except ValueError:
        st.error("Not correct file, please choose another")
        return

    if st.sidebar.checkbox("Show all ads seen"):
        show_content(ads, True)
    elif st.sidebar.checkbox("Show all posts seen"):
        show_content(posts)
    elif st.sidebar.checkbox("Show all videos seen"):
        show_content(videos)

def get_times(content):
    content = content[content["string_map_data.Time.timestamp"] != 0]
    times = pd.to_datetime(content["string_map_data.Time.timestamp"].dropna(), unit='s')
    return times.min(), times.max()

def show_content(content, ads=False):
    start_time, end_time = get_times(content)
    st.write("This data was collected between ", start_time, " and ", end_time)
    all_content = content["string_map_data.Author.value"].value_counts()
    #st.write(all_content)
    st.write("All entries seen only 1 time in this period is NOT included in the chart.")
    all_content = all_content[all_content > 1]
    st.set_option('deprecation.showPyplotGlobalUse', False) #TODO: REMOVE 
    if ads:
        fig = px.bar(all_content, x=all_content.index, y='string_map_data.Author.value',
                    labels={'string_map_data.Author.value': 'Number of seen ads',
                            'index': 'Account'},
                    width=1000, height=800)
    else:
        fig = px.pie(all_content, names=all_content.index, values='string_map_data.Author.value',
                    width=800, height=800)
    st.plotly_chart(fig)
    word_cloud = st.checkbox("Make a word cloud!")
    if word_cloud:
        make_cloud(all_content)

def make_cloud(content):
    text = ' '.join(content['author'])
    st.spinner(text="in progress")
    wordcloud = WordCloud(width=1500, height=1200, random_state=1,
                        background_color='salmon', colormap='Pastel1', collocations=False,
                        stopwords=STOPWORDS).generate(text)
    
    plt.figure(figsize=(40,30))
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.show()
    st.pyplot()

def get_user_data(files):
    data_list = []
    option = st.sidebar.selectbox('What data would like to have displayed?',
                    ('', 'Ads, posts and videos seen', 'Your searches'))
    if option == 'Ads, posts and videos seen':
        for fil in files:
            if fil.name == "ads_viewed.json" or fil.name == 'posts_viewed.json' or fil.name == "videos_watched.json":
                data_list.append(fil)
    elif option == 'Your searches':
        for fil in files:
            if fil.name == 'account_searches.json':
                data_list.append(fil)

    return data_list, option

def select_files():
    files = st.file_uploader("Upload instagram files", accept_multiple_files=True)
    return files

def inbox_statistics(files):
    dm_dict = {}
    for fil in files:
        if fil.name == 'message_1.json':
            bytes_data = fil.read()
            string_data = bytes_data.decode("utf-8")
            data = json.loads(string_data)
            df = pd.json_normalize(data["participants"])
            if (len(df.index) == 2):
                navn = df["name"].iloc[0]
                if len(navn) > 30:
                    navn = "unknown"
                dm_dict.update({navn: fil.size})
    sorted_df = pd.DataFrame.from_dict(dm_dict, orient='index')
    st.write("This chart shows the size of your inbox with each person.")
    fig = px.bar(sorted_df, width=1000, height=800,
                labels={'value': 'Filesize of each inbox',
                        'index': 'Account'})
    st.plotly_chart(fig)     

def show_interests(files):
    for fil in files:
        if fil.name == 'your_topics.json':
            bytes_data = fil.read()
            string_data = bytes_data.decode("utf-8")
            data = json.loads(string_data)
            df = pd.json_normalize(data["topics_your_topics"])
            df = df['string_map_data.Name.value']
            st.write("Instagram has a map of personalized 'interests you might have', which is based on the activity on your account. Here is a list of interests you have according to Instagram.")
            st.write(df)

if __name__ == "__main__":

    st.title("An Instagram data dump inspection")
    st.write("All uploaded data is ONLY stored in RAM. It is not saved anywhere. That means that it is cleared whenever the app re-runs, you remove the uploaded files or the application is closed.")
    try:
        files = select_files()
    except FileNotFoundError:
        st.error("Not correct file, please choose another")
    st.write("If you have a folder with Instagram files, drag and drop the whole folder to upload all the files.")
    st.write("If you have multiple folders, please move those into one folder and then upload that folder.")
    st.write("See sidebar to the left for options")
    st.write("Your plots will appear below.")
    data_list, option = get_user_data(files)
    if st.sidebar.checkbox("Inferred interests"):
        show_interests(files)
    if st.sidebar.checkbox("See inbox statistics"):
        inbox_statistics(files)

    if option == 'Ads, posts and videos seen':
        visualize_seen_content(data_list)
    elif option == 'Your searches':
        visualize_searches(data_list)
