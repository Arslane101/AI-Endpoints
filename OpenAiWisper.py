from io import BytesIO
from time import sleep
from groq import Groq as GROQ
import assemblyai as aai
import requests
import streamlit as st
from openai import OpenAI
from deepgram import DeepgramClient, FileSource, PrerecordedOptions
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
    if not toggle: 
       uploaded_file = BytesIO(requests.get(uploaded_file).content)
       uploaded_file.name = "audio.webm"
       print(uploaded_file)
    files = {
        "audio": (uploaded_file.name, uploaded_file, "audio/webm")
    }
    print("- Uploading file to Gladia...")
    upload_response = make_request(
    "https://api.gladia.io/v2/upload/", headers, "POST", files=files
    )
    print("Upload response with File ID:", upload_response)
    audio_url = upload_response.get("audio_url")

    data = {
    "audio_url": audio_url }

    headers["Content-Type"] = "application/json"

    print("- Sending request to Gladia API...")
    post_response = make_request(
    "https://api.gladia.io/v2/transcription/", headers, "POST", data=data
    )

    print("Post response with Transcription ID:", post_response)
    result_url = post_response.get("result_url")

    if result_url:
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
    return reply["transcription"]["full_transcript"]
@st.cache_data
def Deepgram(uploaded_file,input):
   deepgram = DeepgramClient(st.secrets["secret"])  
   # STEP 2 Call the transcribe_file method on the rest class
   if not toggle: 
       uploaded_file = BytesIO(requests.get(uploaded_file).content)
       uploaded_file.name = "audio.webm"
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
def Assembly(uploaded_file):

    aai.settings.api_key = st.secrets["ASSEMBLY_API_KEY"]
    transcriber = aai.Transcriber()
    if not toggle: 
       uploaded_file = BytesIO(requests.get(uploaded_file).content)
       uploaded_file.name = "audio.webm"
    audio_file = uploaded_file
    config = aai.TranscriptionConfig(language_detection=True)

    transcript = transcriber.transcribe(audio_file, config)

    if transcript.status == aai.TranscriptStatus.error:
        print(f"Transcription failed: {transcript.error}")
        exit(1)

    return transcript.text
@st.cache_data
def Whisper(uploaded_file): 
    client = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])
    if  toggle:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=uploaded_file,
            )
    else:
        audio = BytesIO(requests.get(uploaded_file).content)
        audio.name = "audio.webm"
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio,
            )
    return transcription.text

@st.cache_data
def Groq(uploaded_file):
    client = GROQ(api_key= st.secrets["GROQ"])
    chat_completion = client.audio.transcriptions.create(
        file=uploaded_file,
        model="whisper-large-v3-turbo")
    return chat_completion.text
        

st.title("Transcription Testing")



# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


# Accept user input
toggle = st.toggle(label="📁")
response = " "
if toggle:
    uploaded_file = st.file_uploader("Insert Recording", type="webm")
else: 
    uploaded_file = st.text_input("Insert Link",placeholder="eg: https://www.example.com/recording.webm",value=None)
model = st.selectbox("Select the service to use for transcription", ["Assembly", "Deepgram", "Gladia","Groq","Whisper"],
    placeholder="eg : Whisper",index=None)
if(model=="Deepgram"):
    input = st.text_input("Type the name of the model you want to use : ",value="nova-2",placeholder="eg : nova-2")
if(uploaded_file is not None):
 st.session_state.messages.append({"role": "user", "content": uploaded_file})
 if toggle : 
     with st.chat_message("user"):
        st.markdown("File Uploaded with Success !")
 else:
     with st.chat_message("user"):
        st.markdown("Link Successfully Added ! ")
 with st.chat_message("assistant"):
     if (model=="Deepgram" ):
            response = Deepgram(uploaded_file,input)
     else:
           if(model is not None):
               response = eval(model)(uploaded_file)
st.write(response)
st.session_state.messages.append({"role": "assistant", "content": response})


