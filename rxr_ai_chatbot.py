import streamlit as st
import openai
import os
from streamlit_chat import message
from datetime import datetime
from PIL import Image
import pytesseract
import fitz  # PyMuPDF for PDFs
import re
import json

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
                "Subscription members may add a second vehicle under the same household for a discounted 'Family Plan' if they provide valid mailing information.\n"
                "Accepted forms of proof include any ONE of the following: vehicle registration, insurance card, matching CarFax address, or shared billing address on file. \n"
                "Subscription tiers: \n"
                "• Repeat Basic ($100/month): Exterior rinse + wax + tire shine (1 vehicle)\n"
                "• Repeat Premium ($200/month): Full interior + exterior + rotating add-on (1 vehicle)\n"
                "• Repeat Family Plan ($250/month): 2 vehicles, full service, access to pressure washing, discount on add-ons\n"
                "• Additional vehicle (Family Plan): +$75/month\n"
                "All new subscriptions require an initial full detail at $400 to start the plan.\n"
                "To qualify for the Family Plan, both vehicles must be registered to the same household. RxR reserves the right to verify this information to prevent misuse.\n"
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

# File upload option for proof of address
st.divider()
st.subheader("📎 Family Plan Verification (if applicable)")
with st.expander("Upload proof of shared address"):
    uploaded_file = st.file_uploader("Upload ONE of the following: registration, insurance, CarFax, or billing doc")
    if uploaded_file:
        # Save file to local directory with timestamp
        save_dir = "uploaded_verifications"
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        save_path = os.path.join(save_dir, f"proof_{timestamp}_{uploaded_file.name}")
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("✅ File received and saved for verification.")

        extracted_text = ""
        try:
            if uploaded_file.name.lower().endswith(".pdf"):
                with fitz.open(save_path) as doc:
                    for page in doc:
                        extracted_text += page.get_text()
            else:
                img = Image.open(save_path)
                extracted_text = pytesseract.image_to_string(img)

            # Try to extract name and address
            name_match = re.search(r"(?i)(name[:\s]*)?(\b[A-Z][a-z]+\s[A-Z][a-z]+\b)", extracted_text)
            address_match = re.search(r"\d{3,5}\s+\w+(\s\w+)*\s+(Street|St|Rd|Road|Ave|Avenue|Blvd|Boulevard|Lane|Ln|Drive|Dr)", extracted_text, re.IGNORECASE)

            name_found = name_match.group(2) if name_match else None
            address_found = address_match.group(0) if address_match else None

            if address_found:
                st.success("✅ Sky found address: " + address_found)
                # Save name/address to json log
                log_path = "address_log.json"
                if os.path.exists(log_path):
                    with open(log_path, "r") as log_file:
                        address_log = json.load(log_file)
                else:
                    address_log = []

                match_found = False
                for entry in address_log:
                    if entry.get("address") == address_found:
                        match_found = True
                        break

                if not match_found:
                    address_log.append({"name": name_found or "Unknown", "address": address_found})
                    with open(log_path, "w") as log_file:
                        json.dump(address_log, log_file, indent=2)
                    st.success("✅ New address saved to records. Auto-approved for now.")
                else:
                    st.info("ℹ️ This address matches an existing Family Plan member. Access approved.")
            else:
                st.warning("⚠️ Sky couldn't confidently find a valid address. A human will verify manually.")

        except Exception as e:
            st.warning("❌ Could not process the file. It will be reviewed manually.")

# Checkbox for soft confirmation
agree = st.checkbox("I confirm both vehicles are registered to the same household. RxR may request verification.")
if agree:
    st.success("✅ Confirmation received.")

# Input field
if prompt := st.chat_input("Ask your car detailing question here..."):
    st.session_state['messages'].append({"role": "user", "content": prompt})

    # Get response from OpenAI
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=st.session_state['messages']
    )
    reply = response.choices[0].message.content
    st.session_state['messages'].append({"role": "assistant", "content": reply})
    message(reply, is_user=False, key=str(len(st.session_state['messages'])))
