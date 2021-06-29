# Regular Support imports
import os
import regex
import shutil
import numpy as np
import pandas as pd
from collections import Counter
from processor.whatsapp import WhatsAppChatAnalysis

# FAST API Imports
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

tags_metadata = [
    {
        "name": "Demonstration",
        "description": "Try Demo of **Mad Max Fury Road** ",
    },
    {
        "name": "Processor",
        "description": "Upload your whatsapp chat and boom, you have complete analysis.",
    },
]

app = FastAPI(
    title="WhatsApp Chat Processor",
    description="This is DS project for Whatsapp chat analysis, with auto docs for the API and everything",
    version="1.0.0",
    openapi_tags=tags_metadata,
    openapi_url="/api/v1/openapi.json"
)


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

statements = [
    {"heading": "We care for your Privacy and we mean it.",
    "symbol" : "inbox",
    "description": "No. We are not saving any whatsapp chat export. As soon the uploaded file process it get deleted completely from uploaded location."
    },
    {"heading": "How it's working ?",
    "symbol" : "setting",
    "description": "Program script read the content and simply display in statstical format."
    },
    {"heading": "What to avoid and understand ?",
    "symbol" : "stop",
    "description": "Avoid Sensetive information | Avoid to upload Chat with media | No images or Video are consider for processing. | It's text processing techinque only."
}]


@app.get("/", response_class=HTMLResponse, tags=["Processor"])
async def main(request: Request):
    """
    Welcome Screen to upload exported chat
    """
    return templates.TemplateResponse("index.html", {"request": request, "statements": statements})


@app.get("/heartbeat/", response_class=HTMLResponse, tags=["Processor"])
async def heart_beat(request: Request):
    """
    Application Heart Beat
    """
    return templates.TemplateResponse("heartbeat.html", {"request": request})


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    return RedirectResponse("/404_page_not_found/")


@app.get("/404_page_not_found/", response_class=HTMLResponse, tags=["Processor"])
async def page_not_found_404(request: Request):
    """
    404 Page Not Found
    """
    return templates.TemplateResponse("404.html", {"request": request})


async def processing(chat_file):
    if chat_file:
        chat = WhatsAppChatAnalysis()
        # Call Process chat with input as exported file
        data = chat.process_chat(chat_file)

        #----  EDA   -----------------
        df = pd.DataFrame(data, columns=["Date", 'Time', 'Author', 'Message'])
        # Convert Date into panda datetime format
        df['Date'] = pd.to_datetime(df['Date'])

        df['emoji'] = df["Message"].apply(chat.extract_emojis)
        emojis = sum(df['emoji'].str.len())
        # print("Total Emoji's Used : ", emojis)
        
        # print(df.info())
        # print(df.Author.unique())

        total_messages = df.shape[0]
        # print(total_messages)

        image_messages = len(df[df['Message'].str.contains("image omitted")])

        # Link Shared
        URLPATTERN = r'(https?://\S+)'
        df['urlcount'] = df.Message.apply(lambda x: regex.findall(URLPATTERN, x)).str.len()
        links = np.sum(df.urlcount)

        author_list = [author for author in df["Author"].unique() if author is not None ]

        media_messages_df = df[df['Message'].str.contains("image omitted")]
        messages_df = df.drop(media_messages_df.index)
        messages_df['Letter_Count'] = messages_df['Message'].apply(lambda s : len(s))
        messages_df['Word_Count'] = messages_df['Message'].apply(lambda s : len(s.split(' ')))
        messages_df["MessageCount"]=1

        author_list = [author for author in df["Author"].unique() if author is not None ]

        # wordcloud_array = []
        # Generate Word Cloud
        for i in range(len(author_list)):
            dummy_df = messages_df[messages_df['Author'] == author_list[i]]
            text = " ".join(review for review in dummy_df.Message)
            # print('Words by',author_list[i])
            if len(text) > 0:
                wordcloud_return = chat.generate_word_cloud(text)
                # wordcloud_array.append(wordcloud_return)
                # chat.generate_report(user_df, media_messages_df, author)
                user_data = chat.get_user_json_data(i+1, dummy_df, media_messages_df, author_list[i], wordcloud_return)
                result = chat.formation_of_complete_data(user_data)
            else:
                wordcloud_return = chat.generate_word_cloud('Zero')
                #wordcloud_array.append(wordcloud_return)
                # chat.generate_report(user_df, media_messages_df, author)
                user_data = chat.get_user_json_data(i+1, dummy_df, media_messages_df, author_list[i], wordcloud_return)
                result = chat.formation_of_complete_data(user_data)        


        total_emojis_list = list([a for b in messages_df.emoji for a in b])
        emoji_dict = dict(Counter(total_emojis_list))
        emoji_dict = sorted(emoji_dict.items(), key=lambda x: x[1], reverse=True)

        # emoji_df = pd.DataFrame(emoji_dict, columns=['emoji', 'count'])
        # pie_return = chat.emoji_pie_chat(emoji_df)
        
        context = {
            "total_emojis": emojis,
            "total_messages": total_messages,
            "total_images": image_messages,
            "total_link": links,
            "author_list": len(author_list),
            "user_data": result,

        }
        # pie_return.show()
        return context

@app.post("/process_chat/", tags=["Processor"])
async def process_uploaded_chat(request: Request, file: UploadFile = File(...)):
    """
    Function to Process whatsApp Chat v2.21.11.15 standard format
    """
    global upload_folder
    file_object = file.file
    chat_file = "_chat.txt"
    #create empty file to copy the file_object to
    upload_folder = open(os.path.join(file.filename), 'wb+')
    shutil.copyfileobj(file_object, upload_folder)
    shutil.move(file.filename, chat_file)
    upload_folder.close()

    if chat_file:
        context = await processing(chat_file)
        return templates.TemplateResponse("statistics.html", {"request": request, "context": context})
    else:
        return {"error": "Please select upload file"}

    
@app.post("/perform_demo/", tags=["Demonstration"])
async def demo(request: Request):
    """
    Demo Execution Mode
    """
    chat = WhatsAppChatAnalysis()
    chat.generate_dummy_chat_file('processor/dummy_chat.txt' , '_chat.txt')
    chat_file = "_chat.txt"
    if chat_file:
        context = await processing(chat_file)
        return templates.TemplateResponse("statistics.html", {"request": request, "context": context})
    else:
        return {"error": "Please select upload file"}
