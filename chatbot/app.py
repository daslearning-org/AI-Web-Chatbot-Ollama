import gradio as gr
import numpy as np
import json
import os
import base64

# Import VOSK components
from vosk import KaldiRecognizer, Model

# Import local AI components
from ollamaApi import get_llm_models, model_capabilities, chat_with_llm

# Global variables
## Define the audio recognization model. More at: https://alphacephei.com/vosk/models
lang_model = os.environ.get("AUDIO_MODEL", "en-in")
ollama_url = "http://localhost:11434"
llm_list = []
selected_llm = None

# Load the speach recognization model
try:
    model = Model(lang=lang_model) # You might need to specify model_path= if not in default location
    print("Vosk model loaded successfully.")
except Exception as e:
    print(f"Error loading Vosk model: {e}")
    model = None

# set ollama url
def set_ollama_url(url):
    """Sets the Ollama URL and hides the URL input screen, shows the chatbot."""
    global ollama_url
    global llm_list
    global selected_llm
    if len(url) >= 8:
        ollama_url = url
    print(f"Ollama URL set to: {ollama_url}")
    api_llm_list = get_llm_models(url=ollama_url)
    llm_capabilities = []
    if len(api_llm_list) >= 1:
        llm_list = api_llm_list
        selected_llm = llm_list[0] # selects the first llm from the list
        llm_capabilities = model_capabilities(url=ollama_url, model=selected_llm)
        print(llm_list)
    # Return updates to hide the URL input and show the chatbot
    if "vision" in llm_capabilities:
        return gr.update(visible=False), gr.update(visible=True), gr.update(choices=llm_list, value=selected_llm), gr.update(sources="upload")
    else:
        return gr.update(visible=False), gr.update(visible=True), gr.update(choices=llm_list, value=selected_llm), gr.update(sources=[])

def change_llm(llm_select):
    global selected_llm 
    selected_llm = llm_select
    print(f"Selected llm: {selected_llm}")
    llm_capabilities = model_capabilities(url=ollama_url, model=selected_llm)
    if "vision" in llm_capabilities:
        return gr.update(value=llm_select), gr.update(sources="upload")
    else:
        return gr.update(value=llm_select), gr.update(sources=[])

def image_to_base64(image_path):
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return None
    try:
        with open(image_path, "rb") as image_file:
            # Read the entire image file in binary mode
            binary_data = image_file.read()
            # Encode the binary data to Base64
            base64_encoded_data = base64.b64encode(binary_data)
            # Convert bytes to string (important for many web contexts)
            base64_string = base64_encoded_data.decode('utf-8')
            return base64_string
    except Exception as e:
        print(f"Error converting image to Base64: {e}")
        return None

# Handles the Text Inputs
def process_text_input(message, history):
    """
    Processes the text input from UI & passes to the backend AI Agent
    """

    if message["text"] is not None:
        history.append({"role": "user", "content": message["text"]})
    elif len(message["files"]) >= 1:
        history.append({"role": "user", "content": "explain this"})
    message_history = []
    img_list = []
    for single_msg in history:
        if type(single_msg["content"]) is not tuple: # ignoring the path in message_history for ollama
            message_history.append({
                "role": single_msg["role"],
                "content": single_msg["content"]
            })
    for file in message["files"]:
        history.append({"role": "user", "content": {"path": file}})
        img_b64 = image_to_base64(file)
        img_list.append(f"{img_b64}")
        message_history[-1]["images"] = img_list
    llm_resp = chat_with_llm(url=ollama_url, model=selected_llm, messages=message_history)
    history.append(llm_resp)
    return history, gr.update(value={"text": "", "files": []}, interactive=True) # also clears the text input

# Handles the Audio using VOSK module
def process_audio_input(audio_data_tuple, history):
    # audio_data_tuple will be (sample_rate, numpy_array) from gr.Audio(type="numpy")
    if audio_data_tuple is None or audio_data_tuple[1].size == 0:
        history.append({"role": "assistant", "content": "I'm sorry, It seems that audio is empty!"})
        print("No audio data received.")
        return history # Return current history for both chatbot and state

    if model is None:
        history.append({"role": "assistant", "content": "No voice transcribing model found!"})
        return history

    sample_rate, audio_np = audio_data_tuple
    transcribed_text = ""
    fail_flag = False
    user_message = ""
    bot_response = ""

    try:
        # Convert NumPy array to bytes for Vosk
        # Ensure it's 16-bit PCM for Vosk, and mono if stereo
        if audio_np.ndim > 1:
            audio_np = audio_np[:, 0] # Take the first channel for mono
        audio_bytes = audio_np.astype(np.int16).tobytes()

        rec = KaldiRecognizer(model, sample_rate)

        # Process the entire audio waveform
        if rec.AcceptWaveform(audio_bytes):
            result_json = json.loads(rec.Result())
            transcribed_text = result_json.get("text", "")
        else:
            # If AcceptWaveform doesn't immediately give a final result (e.g., if audio is too short)
            # you might get a partial result here, or an empty string.
            # For non-streaming, we expect a final result, but this handles edge cases.
            partial_json = json.loads(rec.PartialResult())
            transcribed_text = partial_json.get("partial", "")
            if not transcribed_text: # Fallback if partial is also empty
                bot_response = f"Cannot process the audio as transcription failed"
                fail_flag = True
    except Exception as e:
        print(f"Error during VOSK transcription: {e}")
        bot_response = f"Transcription failed: {e}"
        fail_flag = True

    if not transcribed_text.strip():
        bot_response = "Audio input (no clear speech detected)."
        fail_flag = True
    else: # all went well
        # Simulate bot response based on transcribed text
        user_message = f"{transcribed_text}"
        history.append({"role": "user", "content": user_message})
        message_history = []
        for single_msg in history:
            if type(single_msg["content"]) is not tuple: # ignoring the path in message_history for ollama
                message_history.append({
                    "role": single_msg["role"],
                    "content": single_msg["content"]
                })
        llm_resp = chat_with_llm(url=ollama_url, model=selected_llm, messages=message_history)
        history.append(llm_resp)

    if(fail_flag): # If we get any error during the process
        history.append({"role": "assistant", "content": bot_response})
    # Return history for chatbot, history for state
    return history

# UI using gradio
with gr.Blocks(title="DasLearning Ollama Chat") as demo:
    with gr.Group(visible=True) as url_input_screen:
        gr.Markdown("# Welcome to the Ollama Chatbot!")
        gr.Markdown("Please enter the URL of your running Ollama instance.")
        ollama_url_textbox = gr.Textbox(
            label="Ollama Server URL (defaults to http://localhost:11434)",
            placeholder="http://localhost:11434"
        )
        set_url_button = gr.Button("Connect to Ollama")

    with gr.Group(visible=False) as chatbot_screen:
        #state = gr.State([])
        with gr.Row():
            llm_dropdown = gr.Dropdown(
                choices=[],
                show_label=False,
                interactive=True,
                allow_custom_value=False
            )
        chatbot = gr.Chatbot(height=450, type="messages")
        # inputs
        img_n_txt = gr.MultimodalTextbox(
            interactive=True,
            max_lines=5,
            file_count="single",
            file_types=['image'],
            placeholder="Ask anything and you can upload image file",
            show_label=False,
            sources=[] #"upload",
        )
        audio_in = gr.Audio(sources=["microphone"], type="numpy", show_label=False)

    set_url_button.click(
        fn=set_ollama_url,
        inputs=ollama_url_textbox,
        outputs=[url_input_screen, chatbot_screen, llm_dropdown, img_n_txt] # Hide URL screen, show chatbot screen
    )

    # change llm model
    llm_dropdown.select(
        fn = change_llm,
        inputs = llm_dropdown,
        outputs = [llm_dropdown, img_n_txt]
    )

    # For text input:
    img_n_txt.submit(
        process_text_input,
        inputs=[img_n_txt, chatbot],
        outputs=[chatbot, img_n_txt],
        api_name="text_input"
    )

    # For audio input:
    # We use .stop_recording to get the full audio chunk after the user stops speaking.
    audio_in.stop_recording(
        process_audio_input,
        inputs=[audio_in, chatbot],
        outputs=[chatbot],
        api_name="audio_input"
    )

demo.launch(
    server_name="0.0.0.0",
) # server_name="0.0.0.0" can be used as an argument to make this accessible from other devices
