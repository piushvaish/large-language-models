import os
from openai import OpenAI
import gradio as gr
SECRET_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=SECRET_KEY)

# https://www.gradio.app/guides/deploying-gradio-with-docker

system_prompt = """As a movie lover, I watch a lot of films. 
If you have any queries, feel free to ask, and I can also translate the information into a language other than English if needed.
You will ensure to talk only about movies/ films."""

def generate_response(message, history):
    formatted_history = []
    for user, assistant in history:
        formatted_history.append({"role": "system", "content": system_prompt })
        formatted_history.append({"role": "user", "content": user })
        formatted_history.append({"role": "assistant", "content":assistant})

    formatted_history.append({"role": "user", "content": message})
  
    response = client.chat.completions.create(
    model='gpt-4o',
    messages= formatted_history,
    temperature=0.6, 
    max_tokens = 256
    )

    return response.choices[0].message.content

gr.ChatInterface(fn = generate_response,
    chatbot=gr.Chatbot(height=300, placeholder="<strong>Name a film.</strong><br>Language of your choice.</br>"),
    textbox=gr.Textbox(placeholder="Go ahead and ask away!", container=False, scale=7),
    title="Movie Lovers Pub Crawl",
    description="Model can make mistakes. Please double-check responses.",
    retry_btn=None,
    undo_btn="Delete Previous",
    clear_btn="Clear",
    theme="monochrome",
    analytics_enabled = False
    ).launch()
