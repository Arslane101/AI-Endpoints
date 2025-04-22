from io import BytesIO
import re
from time import sleep
import google.generativeai as genai
from groq import Groq as GROQ
import assemblyai as aai
import requests
import streamlit as st
from openai import OpenAI
from huggingface_hub import InferenceClient
from deepgram import DeepgramClient, FileSource, PrerecordedOptions
from together import Together
@st.cache_data
def score_prd(prd_text: str) -> dict:
    scores = {
        "Clarity": 0,
        "Completeness": 0,
        "Feasibility": 0,
        "Alignment": 0,
        "Usability": 0,
        "Consistency": 0,
        "Testability": 0,
    }

    # Normalize the text
    prd_text = prd_text.lower()

    # 1. Clarity (detect vague or overly complex language)
    vague_words = ["maybe", "might", "possibly", "should", "consider", "could"]
    vague_score = sum(1 for word in vague_words if word in prd_text)
    scores["Clarity"] = max(0, 10 - vague_score)

    # 2. Completeness (check if all major sections exist)
    required_sections = ["product overview", "objectives", "mvp", "technical", "user roles", "metrics"]
    found_sections = sum(1 for section in required_sections if section in prd_text)
    scores["Completeness"] = int((found_sections / len(required_sections)) * 10)

    # 3. Feasibility (check if MVP goals are listed and not too ambitious)
    mvp_keywords = ["mvp", "minimum viable", "first release", "initial version"]
    long_term_keywords = ["future", "premium", "iteration", "scaling", "next phase"]
    mvp_mentions = sum(1 for word in mvp_keywords if word in prd_text)
    long_term_mentions = sum(1 for word in long_term_keywords if word in prd_text)
    scores["Feasibility"] = min(10, mvp_mentions * 2 + long_term_mentions)

    # 4. Alignment (detect strategic keywords)
    alignment_terms = ["vision", "business goal", "strategy", "impact", "market"]
    matches = sum(1 for word in alignment_terms if word in prd_text)
    scores["Alignment"] = min(matches * 2, 10)

    # 5. Usability (check if user flow and metadata are described)
    usability_terms = ["user flow", "onboarding", "interaction", "metadata", "description", "tags"]
    matches = sum(1 for word in usability_terms if word in prd_text)
    scores["Usability"] = min(matches * 2, 10)

    # 6. Consistency (simple rule: number of sections and formatting indicators)
    headings = re.findall(r"^[0-9]+\.\s", prd_text, re.MULTILINE)
    scores["Consistency"] = min(len(headings), 10)

    # 7. Testability (look for clear metrics or KPIs)
    testability_terms = ["success metric", "kpi", "quantitative", "qualitative", "goal", "conversion", "engagement"]
    matches = sum(1 for word in testability_terms if word in prd_text)
    scores["Testability"] = min(matches * 2, 10)

    # Weighted score
    weighted_score = (
        scores["Clarity"] * 0.2 +
        scores["Completeness"] * 0.25 +
        scores["Feasibility"] * 0.15 +
        scores["Alignment"] * 0.15 +
        scores["Usability"] * 0.10 +
        scores["Consistency"] * 0.05 +
        scores["Testability"] * 0.10
    )

    scores["Total Score"] = round(weighted_score, 2)
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
def process_with_gemini(transcript):
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('models/gemini-1.5-flash')

    prompt = """You are a Product Manager assistant. You will receive a transcript of a product meeting instead of a raw product idea.
Your task is to extract all relevant information from the transcript and generate a complete, 
clear, and structured Product Requirements Document (PRD) using the following format:

1. Product Overview  
• Product Name (infer if not explicitly given):  
• Vision (summarize team vision):  
• Core Problem (what user pain point or need is being solved):  

2. Objectives & Goals  
• Short-term Goals / MVP:  
• Long-term Goals (future iterations):  

3. MVP Scope & Features  
3.1 MVP Focus (main features planned for launch):  
3.2 User Flow & Experience (summarize how the product will be used):  
3.3 Excluded from MVP (features explicitly excluded):  

4. Technical Requirements  
4.1 Frontend (framework, design system):  
4.2 Backend / Cloud (API, infra choices):  
4.3 Authentication (method & tools):  
4.4 Data Storage (local/cloud, DB type):  

5. User Roles & Access  
• List of different user types and permissions in the system  

6. Future Roadmap Considerations  
• What will come post-MVP  

7. Success Metrics (MVP)  
• Qualitative:  
• Quantitative:  
Make sure to infer details logically when they are implied in the transcript, and clearly indicate [ASSUMED] 
when you’re making intelligent guesses based on context. Keep the PRD readable, professional, 
and well-structured.
Here is the transcript: 
    {transcript}
    """
    response = model.generate_content(prompt.format(transcript=transcript))
    return response.text

@st.cache_data
def process_with_together(transcript):
    client = Together(api_key=st.secrets["TG_API_TOKEN"])
    
    prompt =  """You are a Product Manager assistant. You will receive a transcript of a product meeting instead of a raw product idea.
Your task is to extract all relevant information from the transcript and generate a complete, 
clear, and structured Product Requirements Document (PRD) using the following format:

1. Product Overview  
• Product Name (infer if not explicitly given):  
• Vision (summarize team vision):  
• Core Problem (what user pain point or need is being solved):  

2. Objectives & Goals  
• Short-term Goals / MVP:  
• Long-term Goals (future iterations):  

3. MVP Scope & Features  
3.1 MVP Focus (main features planned for launch):  
3.2 User Flow & Experience (summarize how the product will be used):  
3.3 Excluded from MVP (features explicitly excluded):  

4. Technical Requirements  
4.1 Frontend (framework, design system):  
4.2 Backend / Cloud (API, infra choices):  
4.3 Authentication (method & tools):  
4.4 Data Storage (local/cloud, DB type):  

5. User Roles & Access  
• List of different user types and permissions in the system  

6. Future Roadmap Considerations  
• What will come post-MVP  

7. Success Metrics (MVP)  
• Qualitative:  
• Quantitative:  
Make sure to infer details logically when they are implied in the transcript, and clearly indicate [ASSUMED] 
when you’re making intelligent guesses based on context. Keep the PRD readable, professional, 
and well-structured.
Here is the transcript: 
    {transcript}
    """
    response = client.chat.completions.create(
    model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
    messages=[{"role": "user", "content": prompt.format(transcript=transcript)}],
    )
    return response.choices[0].message.content

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
if response.strip() != " ":  # Only show if there's a transcript
    ai_model = st.selectbox(
        "Select AI Model for Processing",
        ["TogetherAI","Gemini"],
        placeholder="Select an AI model",
        index=None    )
    if ai_model == "Gemini":
                analysis = process_with_gemini(response)
                with st.chat_message("assistant"):
                    response = analysis
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.messages.append({"role": "assistant", "content": str(score_prd(response))})
    elif ai_model == "TogetherAI":
                analysis = process_with_together(response)
                with st.chat_message("assistant"):
                    response = analysis+"\n"+str(score_prd(analysis))
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                