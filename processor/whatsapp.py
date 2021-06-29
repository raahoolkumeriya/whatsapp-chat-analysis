import io
import re
import emoji
import urllib
import base64
import shutil
import numpy as np
# from random import choice
import matplotlib.pyplot as plt
plt.rcParams.update({'figure.max_open_warning': 0})
from wordcloud import WordCloud, STOPWORDS


class WhatsAppChatAnalysis:
    """
    To dip dive into analysis of WhatApp Chat
    """
    def __init__(self):
        # Regex pattern for WhatsApp version 2.21.11.15
        self.pattern = '^\[([0-9]+)(\/)([0-9]+)(\/)([0-9]+), ([0-9]+):([0-9]+):([0-9]+)[ ]?(AM|PM|am|pm)?\]'
        self.result = []

    def parse_date_time(self,string):
        """Parse the Date and Time with regex match"""
        if re.match(self.pattern, string):
            return True
        return False
    
    def find_author(self,string):
        """Find the Author in String"""
        if len(string.split(":",1)) == 2:
            return True
        else:
            return False
        
    def parse_message(self,line):
        """ Parse the raw message into chunks"""
        splitline, split_message = line.split(']', 1)
        splitdate, splittime = splitline.split(",",1)
        date = splitdate.strip('[')
        time = splittime.strip()
        message = split_message.strip()
        if self.find_author(message):
            splitmessage = message.split(":",1)
            author = splitmessage[0]
            message = " ".join(splitmessage[1:])
        else:
            author= None
        return date, time, author, message
    
    def process_chat(self,exported_chat_file):
        """ Process the export file from whatsapp"""
        data = []
        with open(exported_chat_file, encoding="utf-8") as fp:
            fp.readline()
            messageBuffer = []
            date, time, author = None, None, None
            while True:
                line = fp.readline()
                if not line:
                    break
                line = line.strip()
                if self.parse_date_time(line):
                    if len(messageBuffer) > 0:
                        data.append([date, time, author, ''.join(messageBuffer)])
                    messageBuffer.clear()
                    date, time, author,message = self.parse_message(line)
                    messageBuffer.append(message)
                else:
                    messageBuffer.append(line)
        return data


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
        
    def generate_word_cloud(self,text):
        """Generate Word Cloud"""
        # print ("There are {} words in all the messages.".format(len(text)))
        stopwords = set(STOPWORDS)
        # Generate a word cloud image
        wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(text)
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
        subdict["emojis_sent"] = sum(dataframe['emoji'].str.len())
        subdict["link_share"] = sum(dataframe["urlcount"])
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
