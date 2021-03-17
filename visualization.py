import pandas as pd
import json
import streamlit as st
import os
import plotly_express as px
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re


def json_reader_content(json_file):
    bytes_data = json_file.read()
    string_data = bytes_data.decode("utf-8")
    data = json.loads(string_data)
    if json_file.name == 'ads_viewed.json':
        df = pd.json_normalize(data["impressions_history_ads_seen"])
        return df, "ads"
    elif json_file.name == 'posts_viewed.json':
        df = pd.json_normalize(data["impressions_history_posts_seen"]) 
        return df, "posts"
    else:
        df = pd.json_normalize(data["impressions_history_videos_watched"])
        return df, "videos"

def json_reader_searches(json_file):

    bytes_data = json_file.read()
    string_data = bytes_data.decode("utf-8")
    data = json.loads(string_data)
    #st.write(data)
    df = pd.json_normalize(data["searches_user"])
    return df

def visualize_searches(json_files):
    st.title("Your searches on instagram")
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
    try:
        total_searches = searches["string_map_data.Search.value"].value_counts()
        total_searches = total_searches.to_frame()
        total_searches = total_searches.rename(columns={'string_map_data.Search.value': 'Number of searches'})
    except KeyError:
        total_searches = searches["string_map_data.S\u00c3\u00b8k.value"].value_counts()
        total_searches = total_searches.to_frame()
        total_searches = total_searches.rename(columns={'string_map_data.S\u00c3\u00b8k.value': 'Number of searches'})

    st.write(total_searches)
    fig = px.pie(total_searches, names=total_searches.index, values="Number of searches",
                 width=800, height=800)
    st.plotly_chart(fig)

def visualize_seen_content(json_files):
    for item in json_files:
        df, option = json_reader_content(item)
        if option == "ads":
            ads = []
            ads.append(df)
            ads = pd.concat(ads)
            show_content(ads, True)
        elif option == "posts":
            posts = []
            posts.append(df)
            posts = pd.concat(posts)
            show_content(posts)
        elif option == "videos":
            videos = []
            videos.append(df)
            videos = pd.concat(videos)
            show_content(videos)

def get_times(content):
    try:
        content = content[content["string_map_data.Time.timestamp"] != 0]
        times = pd.to_datetime(content["string_map_data.Time.timestamp"].dropna(), unit='s')
    except KeyError:
        content = content[content["string_map_data.Tidspunkt.timestamp"] != 0]
        times = pd.to_datetime(content["string_map_data.Tidspunkt.timestamp"].dropna(), unit='s')
    return times.min(), times.max()

def show_content(content, ads=False):
    start_time, end_time = get_times(content)
    st.write("This data was collected between ", start_time, " and ", end_time)
    try:
        all_content = content["string_map_data.Author.value"].value_counts()
    except KeyError:
        all_content = content["string_map_data.Forfatter.value"].value_counts()

    st.write("All entries seen only 1 time in this period is NOT included in the chart.")
    all_content = all_content[all_content > 1]
    st.set_option('deprecation.showPyplotGlobalUse', False) #TODO: REMOVE 
    if ads:
        try:
            fig = px.bar(all_content, x=all_content.index, y='string_map_data.Author.value',
                        labels={'string_map_data.Author.value': 'Number of seen ads',
                                'index': 'Account'},
                        width=1000, height=800, color='string_map_data.Author.value')
        except (KeyError, ValueError):
            fig = px.bar(all_content, x=all_content.index, y='string_map_data.Forfatter.value',
                        labels={'string_map_data.Forfatter.value': 'Number of seen ads',
                                'index': 'Account'},
                        width=1000, height=800, color='string_map_data.Forfatter.value')
    else:
        try:
            fig = px.pie(all_content, names=all_content.index, values='string_map_data.Author.value',
                     width=800, height=800)
        except (KeyError, ValueError):
            fig = px.pie(all_content, names=all_content.index, values='string_map_data.Forfatter.value',
                     width=800, height=800)
    st.plotly_chart(fig)

def get_user_data(files):
    data_list = []
    option = st.sidebar.radio("What data would you like to see?",
                    ("Seen ads", "Seen posts", "Seen videos", "Your searches"))
    if option == 'Seen ads':
        for fil in files:
            if fil.name == "ads_viewed.json":
                data_list.append(fil)
                option = 'Ads, posts and videos seen'
    if option == 'Seen posts':
        for fil in files:
            if fil.name == "posts_viewed.json":
                data_list.append(fil)
                option = 'Ads, posts and videos seen'
    if option == 'Seen videos':
        for fil in files:
            if fil.name == "videos_watched.json":
                data_list.append(fil)
                option = 'Ads, posts and videos seen'
    if option == 'Your searches':
        for fil in files:
            if fil.name == "account_searches.json":
                data_list.append(fil)
                option = 'Your searches'

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
    st.write("This chart shows the size of your inbox with each person. It will therefore give you an idea of who you have conversed most with.")
    fig = px.bar(sorted_df, width=1000, height=800,
                labels={'value': 'Filesize of each inbox (KB)',
                        'index': 'Account'},
                color="value").update_xaxes(categoryorder='total descending')
    st.plotly_chart(fig)     

def show_interests(files):
    for fil in files:
        if fil.name == 'your_topics.json':
            bytes_data = fil.read()
            string_data = bytes_data.decode("utf-8")
            data = json.loads(string_data)
            df = pd.json_normalize(data["topics_your_topics"])
            try:
                df = df['string_map_data.Name.value']
                df = df.to_frame()
                df = df.rename(columns={'string_map_data.Name.value': 'Interests'})
            except KeyError:
                df = df['string_map_data.Navn.value']
                df = df.to_frame()
                df = df.rename(columns={'string_map_data.Navn.value': 'Interests'})
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
    choice = st.sidebar.radio("Maybe these are more interesting?",
                        ('Inferred interests', 'See inbox statistics'))

    if option == 'Ads, posts and videos seen':
        visualize_seen_content(data_list)
    if option == 'Your searches':
        visualize_searches(data_list)

    if choice == 'Inferred interests':
        show_interests(files)
    if choice == 'See inbox statistics':
        inbox_statistics(files)

