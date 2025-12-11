import streamlit as st
import requests
from datetime import datetime
import re 
import os
from dotenv import load_dotenv

load_dotenv()


#url = f"https://transcriptchatbot.azurewebsites.net/api/function_app/rag/query?code={os.getenv('AZURE_FUNCTION_KEY')}"

#url = f"https://transcriptchatbot.azurewebsites.net/rag/query?code={os.getenv('AZURE_FUNCTION_KEY')}"
url = "http://localhost:7071/rag/query"



st.image("assets/logo.png", width=600)
st.title("YouTube Transcript Assistant")


# Session memory
if "history" not in st.session_state:
    st.session_state.history = []


user_input = st.text_input("Ask something about the videos:")


def clean_text(text: str) -> str:
    text = re.sub(r"\[\d{2}:\d{2}:\d{2}\]", "", text)  # Remove timestamps
    text = re.sub(r"\*\*.*?-\d+\*\*:", "", text) # removes YouTube name
    text = re.sub(r"\b(hello|hi|welcome|hey|ok|bye)\b", "", text, flags=re.IGNORECASE)  # Remove common greetings
    text = text.replace("~~", "")
    text = text.replace("#", "")
    text = re.sub(r"\s+", " ", text)                 
    text = text.strip()
    return text


if st.button("Send") and user_input.strip():
    timestamp = datetime.now().strftime("%H:%M")
    st.session_state.history.append(f"{timestamp}: {user_input}")

    conversation_context = "\n".join(st.session_state.history)
    full_prompt = f"""
Conversation so far:
{conversation_context}

User question:
{user_input}

""" #Endpoint access: streamlit calls url + endpoints
    # LLM: only part that interacts with an LLM is when you send a prompt to your RAG API:
    try:
        response = requests.post(
            url,
            json={"prompt": full_prompt},
            timeout=20
        )
        response.raise_for_status()
        data = response.json()

        # Clean summary and keywords
        answer = clean_text(data['answer'])
        summary = clean_text(data.get('summary', 'No summary available.'))
        keywords = clean_text(data.get('keywords', 'No keywords available.'))

        # Add formatted messages to history
        st.session_state.history.append(f"Keywords:\n{keywords}")
        st.session_state.history.append(f"Summary:\n{summary}")
        st.session_state.history.append(f"Answer:\n{answer}")




    except requests.exceptions.RequestException as e:
        st.session_state.history.append(f"Error: {e}")
    except ValueError:
        st.session_state.history.append("Invalid response from server")

# Display chat history with simple formatting
for message in reversed(st.session_state.history):
    st.write(message)
