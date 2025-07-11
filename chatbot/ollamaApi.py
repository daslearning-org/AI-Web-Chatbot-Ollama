import requests
import json

def get_llm_models(url):
    if url.endswith('/'):
        url = url[:-1]
    llm_models_url = f"{url}/api/tags"
    got_llm_models = []
    try:
        response = requests.get(llm_models_url)
        response.raise_for_status()
        models_data = response.json()
        for model in models_data.get("models", []):
            model_name = model['name']
            if model_name.find("embed") == -1: # it is not an embedding model
                got_llm_models.append(model_name)
        return got_llm_models
    except Exception as e:
        print(f"Error with Ollama: {e}")
        return got_llm_models

def model_capabilities(url, model):
    if url.endswith('/'):
        url = url[:-1]
    llm_details_url = f"{url}/api/show"
    msg_body = {
        "model": f"{model}"
    }
    try:
        response = requests.post(llm_details_url, json=msg_body)
        response.raise_for_status()
        model_data = response.json()
        if "capabilities" in model_data:
            return model_data["capabilities"]
    except Exception as e:
        print(f"Error with Ollama: {e}")
        return []

def chat_with_llm(url, model, messages):
    if url.endswith('/'):
        url = url[:-1]
    chat_url = f"{url}/api/chat"
    msg_body = {
        "model": model,
        "messages": messages,
        "stream": False
    }
    try:
        response = requests.post(chat_url, json=msg_body)
        respDict = response.json()
        if "message" in respDict:
            return respDict["message"]
        else:
            return_resp = {
                "role": "error",
                "content": "**Error** in LLM response!"
            }
            return return_resp
    except Exception as e:
        print(f"Error with Ollama: {e}")
        return_resp = {
            "role": "error",
            "content": f"**Error** with Ollama: {e}"
        }
        return return_resp

# End