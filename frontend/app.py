import gradio as gr
import requests
import os
import uuid

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
LOCAL_MODEL_LABEL = os.getenv("LOCAL_MODEL_LABEL", "Local (Llama 3.2)")
CLOUD_MODEL_LABEL = os.getenv("CLOUD_MODEL_LABEL", "Cloud (Groq Llama 3.1)")


def format_products(products):
    """
    Takes a list of raw product dictionaries and formats them into a clean, 
    collapsible Markdown block using HTML <details> and <summary> tags.
    Returns the formatted Markdown string.
    """
    if not products:
        return ""
    
    md = "\n\n<details>\n<summary><b>🛍️ View Recommended Products</b></summary>\n\n---\n\n"
    for p in products:
        meta_md = ""
        image_url = ""
        for key, value in p.get("metadata", {}).items():
            if key == "image_url":
                image_url = value
                continue
            formatted_key = key.replace("_", " ").title()
            meta_md += f"- **{formatted_key}:** {value}\n"

        md += f"#### {p.get('name')}\n"
        if image_url:
            md += f"![{p.get('name')}]({image_url})\n\n"
            
        md += f"*{p.get('type')} | {p.get('subtype')}*\n\n"
        md += f"{meta_md}\n---\n\n"
        
    md += "</details>\n"
    return md

def load_chat_history(session_id):
    """
    Fetches the historical chat messages from the FastAPI backend for a given session ID.
    Reconstructs the chat UI state by pairing user messages with agent responses,
    including appending dynamic product Markdown cards to the agent's textual response.
    """
    if not session_id:
        return [], ""
    try:
        response = requests.get(f"{BACKEND_URL}/api/chat/{session_id}", timeout=5)
        response.raise_for_status()
        data = response.json()
        history_api = data.get("history", [])
        
        chat_history = []
        for msg in history_api:
            if msg["role"] == "user":
                chat_history.append({"role": "user", "content": msg["message"]})
            elif msg["role"] == "agent":
                ai_text = msg["message"]
                products = msg.get("products", [])
                product_md = format_products(products)
                
                final_response = f"{ai_text}{product_md}"
                chat_history.append({"role": "assistant", "content": final_response})
        return chat_history, session_id
    except Exception as e:
        return [], session_id

def search(query, history, session_id, llm_provider):
    """
    Handles a new user search query. Issues a request to the FastAPI backend's search endpoint,
    receives the AI response and recommended products, and updates the chat history array 
    with the newly formatted Markdown blocks. Returns the updated UI states.
    """
    if not query:
        return history, "", session_id

    if not session_id:
        session_id = str(uuid.uuid4())

    history.append({"role": "user", "content": query})

    try:
        response = requests.get(
            f"{BACKEND_URL}/api/search",
            params={
                "query": query,
                "session_id": session_id,
                "llm_provider": llm_provider,
            }
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        history.append({"role": "assistant", "content": f"Error: {e}"})
        return history, "", session_id

    ai_response = data.get("ai_response", "")
    products = data.get("products", [])

    product_md = format_products(products)

    final_response = f"{ai_response}\n{product_md}"
    history.append({"role": "assistant", "content": final_response})
    
    return history, "", session_id

with gr.Blocks() as demo:
    gr.Markdown("# E-Commerce AI Assistant")
    
    chatbot = gr.Chatbot(label="Chat History")
    session_id = gr.BrowserState("", storage_key="ecommerce_session_id")
    
    with gr.Row():
        msg = gr.Textbox(label="Type your message...", placeholder="Search for products...", scale=4)
        send = gr.Button("Send", scale=1, variant="primary")
    
    with gr.Row():
        llm_provider = gr.Dropdown(
            label="🧠 LLM Provider",
            choices=[LOCAL_MODEL_LABEL, CLOUD_MODEL_LABEL],
            value=LOCAL_MODEL_LABEL,
            scale=2,
            interactive=True,
        )
        clear = gr.Button("Clear Chat", scale=1)

    msg.submit(search, [msg, chatbot, session_id, llm_provider], [chatbot, msg, session_id])
    send.click(search, [msg, chatbot, session_id, llm_provider], [chatbot, msg, session_id])
    clear.click(lambda: ([], "", str(uuid.uuid4())), None, [chatbot, msg, session_id])
    
    demo.load(load_chat_history, inputs=[session_id], outputs=[chatbot, session_id])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=8001, theme=gr.themes.Default(primary_hue="blue"))
