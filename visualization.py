import pandas as pd
import json
import streamlit as st
import os
import plotly_express as px
import numpy as np
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from pathlib import Path


def json_reader_content(json_file):
    bytes_data = json_file.read()
    string_data = bytes_data.decode("utf-8")
    data = json.loads(string_data)

    if (len(data) == 1):
        return
    df1 = pd.json_normalize(data["ads_seen"])
    df2 = pd.json_normalize(data["posts_seen"]) 
    df3 = pd.json_normalize(data["videos_watched"])
    return df1, df2, df3

def json_reader_searches(json_file):

    bytes_data = json_file.read()
    string_data = bytes_data.decode("utf-8")
    data = json.loads(string_data)
    df = pd.json_normalize(data["main_search_history"])

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
        st.error("Not correct file(s), please choose another")
        return

    total_searches = searches["search_click"].value_counts()
    st.write(total_searches)
    fig = px.pie(total_searches, names=total_searches.index, values="search_click",
                width=800, height=800)
    st.plotly_chart(fig)

def visualize_seen_content(json_files):
    ads, posts, videos = [], [], []
    for item in json_files:
        df1, df2, df3 = json_reader_content(item)
        ads.append(df1)
        posts.append(df2)
        videos.append(df3)
    try:
        ads = pd.concat(ads)
        posts = pd.concat(posts)
        videos = pd.concat(videos)
    except ValueError:
        st.error("Not correct file(s), please choose another")
        return
    
    if st.sidebar.checkbox("Show all ads seen"):
        show_content(ads, True)
    elif st.sidebar.checkbox("Show all posts seen"):
        show_content(posts)
    elif st.sidebar.checkbox("Show all videos seen"):
        show_content(videos)

def show_content(content, ads=False):
    all_content = content["author"].value_counts()
    all_content = all_content[all_content > 1]
    st.write(all_content)
    st.set_option('deprecation.showPyplotGlobalUse', False) #TODO: REMOVE 
    if ads:
        fig = px.bar(all_content, x=all_content.index, y='author',
                    width=1000, height=800)
    else:
        fig = px.pie(all_content, names=all_content.index, values='author',
                    width=800, height=800)
    st.plotly_chart(fig)
    word_cloud = st.checkbox("Make a word cloud!")
    if word_cloud:
        make_cloud(content)

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
                    ('', 'Ads, posts and videos seen', 'Your searches',
                    'Location data'))
    for fil in files:
        if option == 'Ads, posts and videos seen':
            if fil.name == 'seen_content.json':
                data_list.append(fil)
        elif option == 'Your searches':
            if fil.name == 'searches.json':
                data_list.append(fil)

    return data_list, option

def select_files():
    files = st.file_uploader("Upload instagram files", accept_multiple_files=True)
    return files

def visualize_location():
    st.write("This is just a test for now!")
    df = pd.DataFrame(
        np.random.randn(1000, 2)/[50, 50] + [59.91, 10.75],
        columns=['lat', 'lon'])
    st.map(df)

if __name__ == "__main__":

    st.title("An Instagram data dump inspection")
    try:
        files = select_files()
    except FileNotFoundError:
        st.error("Not correct file, please choose another")
    st.write("If you have a folder with Instagram files, drag and drop the whole folder to upload all the files")
    st.write("See sidebar to the left for options")
    st.write("Your plots will appear below.")
    data_list, option = get_user_data(files)

    if option == 'Ads, posts and videos seen':
        visualize_seen_content(data_list)
    elif option == 'Your searches':
        visualize_searches(data_list)
    elif option == 'Location data':
        visualize_location()
