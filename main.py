# Regular Support imports
import os
import shutil
import numpy as np
from library.helpers import openfile
from processor.whatsapp import WhatsAppChatAnalysis

# FAST API Imports

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, File, UploadFile, Request
from starlette.exceptions import HTTPException as StarletteHTTPException


tags_metadata = [
    {
        "name": "Demonstration",
        "description": "Try Demo of **Mad Max Fury Road** ",
    },
    {
        "name": "Processor",
        "description": "Upload your whatsapp chat & See Analysis."
    },
]

app = FastAPI(
    title="WhatsApp Chat Processor",
    description="This is DS project for Whatsapp chat analysis,\
        with auto docs for the API and everything",
    version="1.0.0",
    openapi_tags=tags_metadata,
    openapi_url="/api/v1/openapi.json"
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse, tags=["Processor"])
async def main(request: Request):
    """
    Welcome Screen to upload exported chat
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/page/{page_name}", response_class=HTMLResponse)
async def show_page(request: Request, page_name: str):
    data = openfile(page_name+".md")
    return templates.TemplateResponse(
        "page.html", {"request": request, "data": data})


@app.get("/heartbeat/", response_class=HTMLResponse, tags=["Processor"])
async def heart_beat(request: Request):
    """
    Application Heart Beat
    """
    return templates.TemplateResponse("heartbeat.html", {"request": request})


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    return RedirectResponse("/404_page_not_found/")


@app.get(
    "/404_page_not_found/",
    response_class=HTMLResponse, tags=["Processor"])
async def page_not_found_404(request: Request):
    """
    404 Page Not Found
    """
    return templates.TemplateResponse("404.html", {"request": request})


async def processing(chat_file):
    if chat_file:
        chat = WhatsAppChatAnalysis()
        df = chat.convert_raw_to_dataframe_data(chat_file)
        # Get total message
        total_messages = df.shape[0]
        # Get Total numbr of Emojis
        total_emojis = len(list(set([a for b in df.Emojis for a in b])))
        # total link shared
        total_media = np.sum(df.Media)
        # total links
        total_link = np.sum(df.Urlcount)
        # Total Author
        author_list = df.Author.unique()

        # Generate Word Cloud
        for i in range(len(author_list)):
            dummy_df = df[df['Author'] == author_list[i]]
            text = " ".join(review for review in dummy_df.Message)
            if len(text) > 0:
                wordcloud_return = chat.generate_word_cloud(text)
                user_data = chat.get_user_json_data(
                    i+1, dummy_df, df, author_list[i], wordcloud_return)
                result = chat.formation_of_complete_data(user_data)
            else:
                wordcloud_return = chat.generate_word_cloud('Zero')
                user_data = chat.get_user_json_data(
                    i+1, dummy_df, df, author_list[i], wordcloud_return)
                result = chat.formation_of_complete_data(user_data)
        group_name = chat.group_name
        context = {
            "total_emojis": total_emojis,
            "total_messages": total_messages,
            "total_images": total_media,
            "total_link": total_link,
            "author_list": len(author_list),
            "user_data": result,

        }
        return {"group_name": group_name, "context": context}


@app.post("/process_chat/", tags=["Processor"])
async def process_uploaded_chat(
        request: Request,
        file: UploadFile = File(...)):
    """
    Function to Process whatsApp Chat
        v2.21.11.15 standard format
    """
    global upload_folder
    file_object = file.file
    chat_file = "_chat.txt"
    # create empty file to copy the file_object
    upload_folder = open(os.path.join(file.filename), 'wb+')
    shutil.copyfileobj(file_object, upload_folder)
    shutil.move(file.filename, chat_file)
    upload_folder.close()

    if chat_file:
        process_data = await processing(chat_file)
        return templates.TemplateResponse(
            "statistics.html", {
                "request": request,
                "context": process_data.get('context'),
                "group_name": process_data.get('group_name')
                })
    else:
        return {"error": "Please select upload file"}


@app.post("/perform_demo/", tags=["Demonstration"])
async def demo(request: Request):
    """
    Demo Execution Mode
    """
    chat = WhatsAppChatAnalysis()
    chat.generate_dummy_chat_file('processor/dummy_chat.txt', '_chat.txt')
    chat_file = "_chat.txt"
    if chat_file:
        process_data = await processing(chat_file)
        return templates.TemplateResponse(
            "statistics.html", {
                "request": request,
                "context": process_data.get('context'),
                "group_name": process_data.get('group_name')})
    else:
        return {"error": "Please select upload file"}
