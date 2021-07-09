import io
import os
import re
import emoji
import urllib
import base64
import shutil
import numpy as np
import pandas as pd
# from random import choice
import matplotlib.pyplot as plt
plt.rcParams.update({'figure.max_open_warning': 0})
from wordcloud import WordCloud, STOPWORDS


class WhatsAppChatAnalysis:
    """
    To dip dive into analysis of WhatApp Chat
    """
    def __init__(self):
        self.group_name = ""
        self.URLPATTERN = r'(https?://\S+)'
        self.result = []

    def extract_emojis(self, s):
        """Extract emojis from message string"""
        return ''.join(c for c in s if c in emoji.UNICODE_EMOJI['en'])
    
    def fig_to_base64(self, img):
        img = io.BytesIO()
        plt.savefig(img, format='png',
                    bbox_inches='tight')
        img.seek(0)
        string = base64.b64encode(img.read())
        image_64 = 'data:image/png;base64,' + urllib.parse.quote(string)
        return image_64
        
    def add_multilingual_stopwords(self):
        multilingul_list = []
        for file in os.listdir('stopwords'):
            stopword = open('stopwords/' + file, "r")
            for word in stopword:
                word = re.sub('[\n]', '', word)
                multilingul_list.append(word)
        return multilingul_list


    def generate_word_cloud(self,text):
        """Generate Word Cloud"""
        # print ("There are {} words in all the messages.".format(len(text)))
        stopwords = set(STOPWORDS).union(set(self.add_multilingual_stopwords()))
        # Generate a word cloud image
        wordcloud = WordCloud(
                stopwords=stopwords, 
                random_state=1,
                collocations=False,
                font_path='Laila-Regular.ttf',
                background_color="white").generate(text)
        # Display the generated image:
        # the matplotlib way:
        plt.figure( figsize=(10,5))
        plt.imshow(wordcloud, interpolation='bilinear')
        image = plt.axis("off")
        return self.fig_to_base64(image)
        
    # def emoji_pie_chat(self, emoji_df):
    #     """Generate Pie chat for Emojis Dataframe"""
    #     fig = px.pie(emoji_df, values='count', names='emoji')
    #     image = fig.update_traces(textposition='inside', textinfo='percent+label')
    #     return image

    def get_user_json_data(self, user_number, dataframe, media_messages_df, author, wordcloud_string):
        subdict = dict()
        subdict["user_number"] = user_number
        subdict["color"] = "black" 
        # choice(['red','orange','yellow','olive','green','teal','blue','violet','purple','pink','brown','grey','black'])
        subdict["author"] = author
        subdict["message_sent"] = dataframe.shape[0]
        subdict["avg_words_per_msg"] = '{:.2f}'.format((np.sum(dataframe['Word_Count']))/dataframe.shape[0])
        subdict["media_msg"] = media_messages_df[media_messages_df['Author'] == author].shape[0]
        subdict["emojis_sent"] = sum(dataframe['Emojis'].str.len())
        subdict["link_share"] = sum(dataframe["Urlcount"])
        subdict["word_cloud"] = wordcloud_string
        return subdict

    def formation_of_complete_data(self, dictonary_value):
        self.result.append(dictonary_value)
        return self.result

    def generate_dummy_chat_file(self, source_file, dest_file):
        try:
            shutil.copyfile(source_file, dest_file)
            return "File copied successfully."
        except shutil.SameFileError:
            return "Source and destination represents the same file."
        except IsADirectoryError:
            return "Destination is a directory."
        except PermissionError:
            return "Permission denied."
        except:
            return "Error occurred while copying file."

    def convert_raw_to_dataframe_data(self,exported_chat_file):
        """ Process the export file from whatsapp"""
        with open(exported_chat_file,'r', encoding = 'utf-8') as file:
            data = file.read()
        regex_iphone = re.findall('(\[\d+/\d+/\d+, \d+:\d+:\d+ [A-Z]*\]) (.*?): (.*)', data)
        if regex_iphone:
            regex_string = regex_iphone
        regex_android = re.findall('(\d+/\d+/\d+, \d+:\d+\d+ [a-zA-Z]*) - (.*?): (.*)', data)
        if regex_android:
            regex_string = regex_android
        # Convert list to dataframe and name teh columns
        raw_df = pd.DataFrame(regex_string,columns=['DateTime','Author','Message'])
        # Convert to dataframe date
        if regex_iphone:
            raw_df['DateTime'] = pd.to_datetime(raw_df['DateTime'],format="[%d/%m/%y, %H:%M:%S %p]")
        if regex_android:
            raw_df['DateTime'] = pd.to_datetime(raw_df['DateTime'],format="%d/%m/%y, %H:%M %p")
        # Splitting Date and Time 
        raw_df['Date'] = pd.to_datetime(raw_df['DateTime']).dt.date
        raw_df['Time'] = pd.to_datetime(raw_df['DateTime']).dt.time
        # Drop DateTime Column
        raw_df.drop('DateTime',axis='columns', inplace=True)
        # Drop NAN Values 
        raw_df = raw_df.dropna()
        raw_df = raw_df.reset_index(drop=True)
        # Handling *Messages and calls are end-to-end encrypted* 
        self.group_name = raw_df.iloc[0:1]['Author'][0]
        new_df = raw_df.iloc[1: , :]
        # Handle EMojis
        new_df = new_df.assign(Emojis=new_df["Message"].apply(self.extract_emojis))
        # Handle Links
        new_df = new_df.assign(Urlcount=new_df["Message"].apply(lambda x: re.findall(self.URLPATTERN, x)).str.len())
        # Handle Image ommited
        new_df = new_df.assign(Media=new_df['Message'].apply(lambda x: re.findall("image omitted", x)).str.len())
        
        # Handling wordCount         
        media_messages_df = new_df[new_df['Message'].str.contains("image omitted")]
        messages_df = new_df.drop(media_messages_df.index)
        messages_df['Letter_Count'] = messages_df['Message'].apply(lambda s : len(s))
        messages_df['Word_Count'] = messages_df['Message'].apply(lambda s : len(s.split(' ')))
        cloud_df = messages_df[messages_df["Message"].str.contains\
                ("<Media omitted>|This message was deleted|You deleted this message|Missed voice call|Missed video call")==False]

        return cloud_df

    
# if __name__ == "__main__":
#     chat = WhatsAppChatAnalysis()
#     chat_file = 'dummy_chat.txt'
#     if chat_file:
#         df = chat.convert_raw_to_dataframe_data(chat_file)
#         # Get total message
        
#         total_messages = df.shape[0]
#         # Get Total numbr of Emojis
#         total_emojis = len(list(set([a for b in df.Emojis for a in b])))
#         # total link shared
#         total_media = np.sum(df.Media)
#         # total links
#         total_link = np.sum(df.Urlcount)
#         # Total Author
#         author_list = df.Author.unique() 

#         # Generate Word Cloud
#     chat = WhatsAppChatAnalysis()
#     chat_file = 'dummy_chat.txt'
#     if chat_file:
#         df = chat.convert_raw_to_dataframe_data(chat_file)
#         # Get total message
        
#         total_messages = df.shape[0]
#         # Get Total numbr of Emojis
#         total_emojis = len(list(set([a for b in df.Emojis for a in b])))
#         # total link shared
#         total_media = np.sum(df.Media)
#         # total links
#         total_link = np.sum(df.Urlcount)
#         # Total Author
#         author_list = df.Author.unique() 

#         # Generate Word Cloud
#         for i in range(len(author_list)):
#             dummy_df = df[df['Author'] == author_list[i]]
#             text = " ".join(review for review in dummy_df.Message)
#             if len(text) > 0:
#                 wordcloud_return = chat.generate_word_cloud(text)
#                 user_data = chat.get_user_json_data(i+1, dummy_df, df, author_list[i], wordcloud_return)
#                 result = chat.formation_of_complete_data(user_data)
#             else:
#                 wordcloud_return = chat.generate_word_cloud('Zero')
#                 user_data = chat.get_user_json_data(i+1, dummy_df, df, author_list[i], wordcloud_return)
#                 result = chat.formation_of_complete_data(user_data)        
        
#         context = {
#             "total_emojis": total_emojis,
#             "total_messages": total_messages,
#             "total_images": total_media,
#             "total_link": total_link,
#             "author_list": len(author_list),
#             "user_data": result,

#         }
#         print(context)
#         for i in range(len(author_list)):
#             dummy_df = df[df['Author'] == author_list[i]]
#             text = " ".join(review for review in dummy_df.Message)
#             if len(text) > 0:
#                 wordcloud_return = chat.generate_word_cloud(text)
#                 user_data = chat.get_user_json_data(i+1, dummy_df, df, author_list[i], wordcloud_return)
#                 result = chat.formation_of_complete_data(user_data)
#             else:
#                 wordcloud_return = chat.generate_word_cloud('Zero')
#                 user_data = chat.get_user_json_data(i+1, dummy_df, df, author_list[i], wordcloud_return)
#                 result = chat.formation_of_complete_data(user_data)        
        
#         context = {
#             "total_emojis": total_emojis,
#             "total_messages": total_messages,
#             "total_images": total_media,
#             "total_link": total_link,
#             "author_list": len(author_list),
#             "user_data": result,

#         }
#         print(context)