import os
from time import sleep
import requests
from OpenAiWisper import uploaded_file
import streamlit as st

def make_request(url, headers, method="GET", data=None, files=None):
    if method == "POST":
        response = requests.post(url, headers=headers, json=data, files=files)
    else:
        response = requests.get(url, headers=headers)
    return response.json()



headers = {
    "x-gladia-key": os.getenv("GLADIA_API_KEY", st.secrets["GLADIA_API_KEY"]),  # Replace with your Gladia Token
    "accept": "application/json",
}

files = uploaded_file
print("- Uploading file to Gladia...")
upload_response = make_request(
    "https://api.gladia.io/v2/upload/", headers, "POST", files=files
)

audio_url = upload_response.get("audio_url")

data = {
    "audio_url": audio_url,
    "diarization": True,
}

headers["Content-Type"] = "application/json"

post_response = make_request(
    "https://api.gladia.io/v2/transcription/", headers, "POST", data=data
)

result_url = post_response.get("result_url")

if result_url:
    while True:
        poll_response = make_request(result_url, headers)
        if poll_response.get("status") == "done":
            reply = poll_response.get("result")
            break
        elif poll_response.get("status") == "error":
            
            reply = poll_response
        else:
            reply = poll_response.get("status")
        sleep(1)

