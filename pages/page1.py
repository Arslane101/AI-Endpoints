from io import BytesIO
import re
from time import sleep
import google.generativeai as genai
from groq import Groq as GROQ
import assemblyai as aai
import requests
import streamlit as st
from openai import OpenAI
from deepgram import DeepgramClient, FileSource, PrerecordedOptions
from together import Together
from page2 import library,prompts

@st.cache_data
def score_prd(prd_text):
    """Score PRD based on key metrics with simplified scoring."""
    scores = {}
    
    # Scoring criteria with their keywords and weights
    criteria = {
        "Clarity": (["maybe", "might", "possibly", "should", "consider", "could"], 0.20),
        "Completeness": (["product overview", "objectives", "mvp", "technical", "user roles", "metrics"], 0.25),
        "Feasibility": (["mvp", "minimum viable", "first release", "initial version"], 0.15),
        "Alignment": (["vision", "business goal", "strategy", "impact", "market"], 0.15),
        "Usability": (["user flow", "onboarding", "interaction", "metadata", "description", "tags"], 0.10),
        "Consistency": ([], 0.05),  # Special case - handled separately
        "Testability": (["success metric", "kpi", "quantitative", "qualitative", "goal", "conversion", "engagement"], 0.10)
    }
    
    # Calculate scores for each criterion
    for criterion, (keywords, weight) in criteria.items():
        if criterion == "Consistency":
            # Special handling for consistency - count section headers
            headings = len(re.findall(r"^[0-9]+\.\s", prd_text, re.MULTILINE))
            scores[criterion] = min(headings, 10)
        else:
            # Standard keyword-based scoring
            matches = sum(1 for word in keywords if word in prd_text.lower())
            scores[criterion] = min(matches * 2, 10)
    
    # Calculate weighted total score
    total_score = sum(scores[criterion] * weight for criterion, (_, weight) in criteria.items())
    scores["Total Score"] = round(total_score, 2)
    
    return scores

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
        

@st.cache_data
def process_with_gemini(transcript,prompt):
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('models/gemini-1.5-flash')
    response = model.generate_content(prompt["content"].format(transcript=transcript))
    return response.text

@st.cache_data
def process_with_together(transcript,prompt):
    client = Together(api_key=st.secrets["TG_API_TOKEN"])
    response = client.chat.completions.create(
    model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
    messages=[{"role": "user", "content": prompt["content"].format(transcript=transcript)}],
    )
    return response.choices[0].message.content

st.title("PRD Generation")

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
if response.strip() != " ":  # Only show if there's a transcript
    ai_model = st.selectbox(
        "Select AI Model for Processing",
        ["TogetherAI","Gemini"],
        placeholder="Select an AI model",
        index=None    )
    if prompts:
        prompt_options = [p["name"] for p in prompts]
        selected_prompt = st.selectbox(
            f"Select Prompt ({len(prompts)} available)",
            options=prompt_options,
            key="main_prompt_select",
            format_func=lambda x: f"📄 {x}",
            help="Choose a prompt template to use"
        )
        if selected_prompt:
            prompt = library.get_prompt(selected_prompt)
    else:
        st.info("No prompts available in library")
    if ai_model == "Gemini" and prompts:
                analysis = process_with_gemini(response,prompt)
                with st.chat_message("assistant"):
                    response = analysis
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                scores = score_prd(analysis)
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown("### Quality Metrics")
                with col2:
                    st.metric("Total", f"{scores['Total Score']}")
                
                # Create three columns for metrics display
                cols = st.columns(3)
                metrics = list(scores.items())[:-1]  # Exclude Total Score
                for i, (metric, score) in enumerate(metrics):
                    with cols[i % 3]:
                        st.metric(metric, f"{score}/10", label_visibility="visible")
    elif ai_model == "TogetherAI" and prompts:
                analysis = process_with_together(response,prompt)
                with st.chat_message("assistant"):
                    response = analysis
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                scores = score_prd(analysis)
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown("### Quality Metrics")
                with col2:
                    st.metric("Total", f"{scores['Total Score']}")
                
                # Create three columns for metrics display
                cols = st.columns(3)
                metrics = list(scores.items())[:-1]  # Exclude Total Score
                for i, (metric, score) in enumerate(metrics):
                    with cols[i % 3]:
                        st.metric(metric, f"{score}/10", label_visibility="visible")
    
