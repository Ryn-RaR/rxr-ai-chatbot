import streamlit as st
import openai
from streamlit_chat import message

# Initialize session state for messages if not present
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {
            "role": "system",
            "content": (
                "You are RxR's futuristic assistant. Speak like a clever, friendly AI who helps with car detailing questions. "
                "Use a fun and casual tone when talking to the business owner, but maintain a professional, helpful tone for customers. "
                "RxR offers the following services and pricing: \n"
                "- Interior Detail Only: $230\n"
                "- Exterior Detail Only: $230\n"
                "- Full Combo (Interior + Exterior): $400\n"
                "- Paint Sealant / Ceramic Coating (Protection + Shine): $225–$350\n"
                "- Trim Restoration: Priced per vehicle, call for estimate\n"
                "- Excessive Bug/Tar Removal: Starting at $30\n"
                "- Carpet Stain Removal: Starting at $30\n"
                "- Rain-X Glass Treatment: $15\n"
                "- Paint Correction / Scratch Removal: Call for custom quote\n"
                "- Paint Overspray Removal: Starting at $50\n"
                "Driveway pressure washing is available only for subscription members. \n"
                "RxR is a premium mobile detailing service with a futuristic brand identity."
            )
        }
    ]

st.set_page_config(page_title="RxR AI Assistant", page_icon="🚗")
st.title("🤖 RxR Detailing AI Assistant")
st.caption("Ask me anything about car detailing, services, pricing, or appointments!")

# Chat display
for i, msg in enumerate(st.session_state['messages'][1:]):
    message(msg["content"], is_user=(msg["role"] == "user"), key=str(i))

# Set up OpenAI client (new SDK style)
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Input field
if prompt := st.chat_input("Ask your car detailing question here..."):
    st.session_state['messages'].append({"role": "user", "content": prompt})

    # Get response from OpenAI
    response = client.chat.completions.create(
        model="gpt-4",
        messages=st.session_state['messages']
    )
    reply = response.choices[0].message.content
    st.session_state['messages'].append({"role": "assistant", "content": reply})
    message(reply, is_user=False, key=str(len(st.session_state['messages'])))
