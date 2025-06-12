from pathlib import Path

# Combined Streamlit app code with tabs for Chat, Family Plan Upload, and Auto-Reply
combined_app_code = '''
import streamlit as st
import openai
from streamlit_chat import message
from datetime import datetime
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import re
import json
from twilio.rest import Client
import os

st.set_page_config(page_title="RxR Dashboard", page_icon="🚗")

# Secrets for Twilio and OpenAI
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
TWILIO_SID = st.secrets["TWILIO_SID"]
TWILIO_AUTH = st.secrets["TWILIO_AUTH"]
TWILIO_NUMBER = st.secrets["TWILIO_NUMBER"]

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

# Tabs for each feature
tab1, tab2, tab3 = st.tabs(["🤖 RxR Chatbot", "📎 Family Plan Upload", "📩 Auto-Reply Messenger"])

# Tab 1: Chatbot
with tab1:
    st.title("🤖 RxR Detailing AI Assistant")
    st.caption("Ask about detailing, services, pricing, or appointments!")

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
                    "- Paint Sealant / Ceramic Coating: $225–$350\n"
                    "- Trim Restoration: Call for estimate\n"
                    "- Bug/Tar Removal: Starting at $30\n"
                    "- Carpet Stain Removal: Starting at $30\n"
                    "- Rain-X Glass Treatment: $15\n"
                    "- Paint Correction: Custom quote\n"
                    "- Overspray Removal: Starting at $50\n"
                    "Subscription plans:\n"
                    "• Basic: $100/mo\n• Premium: $200/mo\n• Family Plan: $250/mo\n"
                    "New subs must get full $400 detail to start. Proof of address required for Family Plan."
                )
            }
        ]

    for i, msg in enumerate(st.session_state['messages'][1:]):
        message(msg["content"], is_user=(msg["role"] == "user"), key=str(i))

    if prompt := st.chat_input("Ask your car detailing question here..."):
        st.session_state['messages'].append({"role": "user", "content": prompt})
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state['messages']
        )
        reply = response.choices[0].message.content
        st.session_state['messages'].append({"role": "assistant", "content": reply})
        message(reply, is_user=False, key=str(len(st.session_state['messages'])))

# Tab 2: Family Plan Upload
with tab2:
    st.header("📎 Upload Proof of Shared Address")
    uploaded_file = st.file_uploader("Upload registration, insurance, CarFax, or billing doc")
    if uploaded_file:
        save_dir = "uploaded_verifications"
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        save_path = os.path.join(save_dir, f"proof_{timestamp}_{uploaded_file.name}")
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("✅ File received and saved.")

        extracted_text = ""
        try:
            if uploaded_file.name.lower().endswith(".pdf"):
                with fitz.open(save_path) as doc:
                    for page in doc:
                        extracted_text += page.get_text()
            else:
                img = Image.open(save_path)
                extracted_text = pytesseract.image_to_string(img)

            name_match = re.search(r"(?i)(name[:\\s]*)?(\\b[A-Z][a-z]+\\s[A-Z][a-z]+\\b)", extracted_text)
            address_match = re.search(r"\\d{3,5}\\s+\\w+(\\s\\w+)*\\s+(Street|St|Rd|Road|Ave|Avenue|Blvd|Boulevard|Lane|Ln|Drive|Dr)", extracted_text, re.IGNORECASE)

            name_found = name_match.group(2) if name_match else None
            address_found = address_match.group(0) if address_match else None

            if address_found:
                st.success("✅ Sky found address: " + address_found)
                log_path = "address_log.json"
                if os.path.exists(log_path):
                    with open(log_path, "r") as log_file:
                        address_log = json.load(log_file)
                else:
                    address_log = []

                match_found = any(entry.get("address") == address_found for entry in address_log)

                if not match_found:
                    address_log.append({"name": name_found or "Unknown", "address": address_found})
                    with open(log_path, "w") as log_file:
                        json.dump(address_log, log_file, indent=2)
                    st.success("✅ New address saved to records.")
                else:
                    st.info("ℹ️ This address matches an existing Family Plan member. Access approved.")
            else:
                st.warning("⚠️ Could not confidently find a valid address.")

        except Exception:
            st.warning("❌ Could not process the file. It will be reviewed manually.")

    if st.checkbox("I confirm both vehicles are registered to the same household. RxR may request verification."):
        st.success("✅ Confirmation received.")

# Tab 3: Auto-Reply Messenger
with tab3:
    st.header("📩 Auto-Reply Text Message")
    name = st.text_input("Customer Name")
    phone = st.text_input("Phone Number", help="Format: +1XXXXXXXXXX")
    vehicle = st.text_input("Vehicle (Make/Model)")
    service = st.selectbox("Service Type", ["Interior", "Exterior", "Interior + Exterior", "Ceramic", "Subscription"])

    def generate_reply(name, vehicle, service):
        return f"""
Hey {name},

Thanks for booking with RxR – Rinse and Repeat!
We’ve received your request and are getting ready to work our detailing magic.

✅ Booking Summary:
- Vehicle: {vehicle}
- Service: {service}

We’ll send a confirmation and ETA shortly. If you have questions or need to reschedule, just reply to this message.

Until then — keep it clean,

Ram Mejia
Owner | RxR Mobile Detailing, LLC
"""

    if st.button("Send Message"):
        try:
            message_body = generate_reply(name, vehicle, service)
            message = twilio_client.messages.create(
                body=message_body,
                from_=TWILIO_NUMBER,
                to=phone
            )
            st.success(f"✅ Message sent to {name}")
        except Exception as e:
            st.error(f"❌ Failed to send message: {e}")
'''

# Save the combined app
combined_app_path = Path("/mnt/data/rxr_combined_dashboard.py")
combined_app_path.write_text(combined_app_code)

combined_app_path.name
