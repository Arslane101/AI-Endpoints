# AI-Endpoints

A Streamlit-based web application that provides audio transcription services using multiple AI endpoints. This application allows users to transcribe audio files or audio from URLs using various AI services.

## Features

- Support for multiple transcription services:
  - OpenAI Whisper
  - AssemblyAI
  - Deepgram
  - Gladia
  - Groq
- Flexible input options:
  - File upload (.webm format)
  - URL input for remote audio files
- Caching support for improved performance
- User-friendly interface with Streamlit

## Prerequisites

- Python 3.x
- Required API keys:
  - OpenAI API key
  - AssemblyAI API key
  - Deepgram API key
  - Gladia API key
  - Groq API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/AI-Endpoints.git
cd AI-Endpoints
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your environment variables:
Create a `.streamlit/secrets.toml` file with your API keys:
```toml
OPENAI_API_KEY = "your-openai-key"
ASSEMBLY_API_KEY = "your-assemblyai-key"
secret = "your-deepgram-key"
GLADIA_API_KEY = "your-gladia-key"
GROQ = "your-groq-key"
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run OpenAiWisper.py
```

2. Access the web interface through your browser (typically at http://localhost:8501)

3. Choose your input method:
   - Toggle between file upload and URL input
   - Upload a .webm audio file or provide a URL to an audio file

4. Select your preferred transcription service:
   - For Deepgram, you can specify the model (e.g., "nova-2")
   - Other services use their default models

5. View the transcription results in real-time

## Supported Audio Formats

- Primary support for .webm format
- URL-based audio files must be accessible and in a compatible format

## Contributing

Feel free to submit issues and enhancement requests!

## License

[Add your license information here] 