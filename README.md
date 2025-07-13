# 🗪 Multimodal Web Chatbot for Ollama
A web based AI Chatbot for Ollama made on Gradio (Python) which supports Voice input to interact with ollama LLM models. If you have a vision capable LLM like `llava`, you can even upload an image with your query. This is offline and private AI chatbot. This does not require an active Internet connection except for the first time (to download the voice to text model)

## 📽️ Demo
Coming soon...

## 🧑‍💻 Quickstart Guide

### 🐋 Run on Docker
Pull & simply Run. You need to provide your `Ollama Endpoint`, do not provide `localhost` as it will look into container's localhost. Check the latest version on [docker hub](https://hub.docker.com/r/sdas92/ai-ollama-chatbot)
```bash
docker pull sdas92/ai-ollama-chatbot:v0.2.0
docker run -d -p 7860:7860 --name ollama-chatbot sdas92/ai-ollama-chatbot:v0.2.0
```

### 🐍 Run on Python
```bash
git clone https://github.com/daslearning-org/AI-Web-Chatbot-Ollama.git
cd ./AI-Web-Chatbot-Ollama/chatbot/
python -m venv .venv
source .venv/bin/activate # use .\venv\Scripts\activate on windows
pip install -r requirements.txt

# run the app
python app.py # you can open the web ui at port 7860
```

## 🐋 Build Docker Image
Build your own image, you need to change your repo details
```bash
git clone https://github.com/daslearning-org/AI-Web-Chatbot-Ollama.git
cd ./AI-Web-Chatbot-Ollama/chatbot/
VERSION_FILE="VERSION"
APP_VERSION=$(< "$VERSION_FILE" tr -d '\n\r' | xargs)
IMAGE_URI="sdas92/ai-ollama-chatbot:${APP_VERSION}" # your repo details
docker build -t ${IMAGE_URI} .
docker push "${IMAGE_URI}"
```
