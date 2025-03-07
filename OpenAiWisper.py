from io import StringIO
from time import sleep
import assemblyai as aai

import requests
import streamlit as st
from openai import OpenAI
from deepgram import DeepgramClient, FileSource, PrerecordedOptions
@st.cache_data
def make_request(url, headers, method="GET", data=None, files=None):
    if method == "POST":
        response = requests.post(url, headers=headers, json=data, files=files)
    else:
        response = requests.get(url, headers=headers)
    return response.json()
@st.cache_data
def Gladia(uploaded_file):

    
    headers = {
    "x-gladia-key": st.secrets["GLADIA_API_KEY"],  # Replace with your Gladia Token
    "accept": "application/json",
    }

    files = {
        "audio": (uploaded_file.name, uploaded_file, uploaded_file.type)
    }
    print("- Uploading file to Gladia...")
    upload_response = make_request(
    "https://api.gladia.io/v2/upload/", headers, "POST", files=files
    )
    print("Upload response with File ID:", upload_response)
    audio_url = upload_response.get("audio_url")

    data = {
    "audio_url": audio_url,
    "diarization": True,
    }
# You can also send an URL directly without uploading it. Make sure it's the direct link and publicly accessible.
# For any parameters, please see: https://docs.gladia.io/api-reference/pre-recorded-flow

    headers["Content-Type"] = "application/json"

    print("- Sending request to Gladia API...")
    post_response = make_request(
    "https://api.gladia.io/v2/transcription/", headers, "POST", data=data
    )

    print("Post response with Transcription ID:", post_response)
    result_url = post_response.get("result_url")

    if result_url:
     print("True")
     while True:
        poll_response = make_request(result_url, headers)
        if poll_response.get("status") == "done":
            reply = poll_response.get("result")
            break
        elif poll_response.get("status") == "error":
            reply = poll_response.get("error")
        else:
            reply = poll_response.get("status")
        sleep(1)
    return reply
@st.cache_data
def Deepgram(uploaded_file,input):
   deepgram = DeepgramClient(st.secrets["secret"])  
   # STEP 2 Call the transcribe_file method on the rest class
 
   payload: FileSource = {
            "buffer": uploaded_file,
            "mimetype": "video/webm"
        }
    
   options = PrerecordedOptions(
        detect_language=True,
        model = input
   )
   file_response = deepgram.listen.rest.v("1").transcribe_file(payload, options,timeout = 300)
   return file_response['results']['channels'][0]['alternatives'][0]['transcript']
@st.cache_data
def AssemblyAI(uploaded_file):

    aai.settings.api_key = st.secrets["ASSEMBLY_API_KEY"]
    transcriber = aai.Transcriber()

    audio_file = uploaded_file.getvalue()

    config = aai.TranscriptionConfig(language_detection=True)

    transcript = transcriber.transcribe(audio_file, config)

    if transcript.status == aai.TranscriptStatus.error:
        print(f"Transcription failed: {transcript.error}")
        exit(1)

    return transcript.text

st.title("Transcription Testing")

model = st.selectbox("Select the service to use for transcription", ["Assembly", "Deepgram", "Gladia","Whisper"], 
             key="model",index=None,
    placeholder="eg : Whisper")
if(model=="Deepgram"):
    input = st.text_input("Type the name of the model you want to use : ",placeholder="eg : nova-2")
# Set Model
client = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []



# Accept user input
uploaded_file = st.file_uploader("Insert Recording", type="webm")
if uploaded_file is not None:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": uploaded_file})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown("File Uploaded with Success ! ")

    # Transcribe the audio file
    with st.chat_message("assistant"):
       if(model=="Whisper") :
            transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=uploaded_file,
            )
            response = transcription.text
       elif (model=="Gladia"):
            response = Gladia(uploaded_file)
       elif (model=="Deepgram"):
            
            response = Deepgram(uploaded_file,input)
       else:
           response = AssemblyAI(uploaded_file)
       st.write(response)
       st.session_state.messages.append({"role": "assistant", "content": response})