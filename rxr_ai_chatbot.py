import streamlit as st
from openai import OpenAI
from streamlit_chat import message

# Initialize session state for messages if not present
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {
            "role": "system",
            "content": (
                "You are RxR's futuristic assistant. Speak like a clever, friendly AI who helps with car detailing questions. "
                "Use a fun and casual tone when talking to the business owner, but maintain a professional, helpful tone for customers. "
                "RxR offers the following services and pricing: Interior Detail Only - $230, Exterior Detail Only - $230, Combined Interior & Exterior Detail - $400. "
                "Driveway pressure washing is only available for subscription members. RxR is a premium mobile detailing service with a futuristic brand identity."
            )
        }
    ]

st.set_page_config(page_title="RxR AI Assistant", page_icon="🚗")
st.title("🤖 RxR Detailing AI Assistant")
st.caption("Ask me anything about car detailing, services, pricing, or appointments!")

# Chat display
for i, msg in enumerate(st.session_state['messages'][1:]):
    message(msg["content"], is_user=(msg["role"] == "user"), key=str(i))

# Input field
if prompt := st.chat_input("Ask your car detailing question here..."):
    st.session_state['messages'].append({"role": "user", "content": prompt})

    # Get response from ChatGPT (via OpenAI)
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=st.session_state['messages']
    )
    reply = response.choices[0].message.content
    st.session_state['messages'].append({"role": "assistant", "content": reply})
    message(reply, is_user=False, key=str(len(st.session_state['messages'])))
