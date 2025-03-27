
import streamlit as st
import math
from fpdf import FPDF
import tempfile
import base64

# --- Constants ---
PILE_COST_2_7_8 = 365
PILE_COST_3_5 = 465
EXTENSION_COST_2_7_8 = 265
EXTENSION_COST_3_5 = 365
EXCAVATOR_RATE = 130
DRIVE_UNIT_RATE = 70
AUGER_RATE = 30
TRAILER_RATE = 1000
PASSENGER_VEHICLE_RATE = 200
HST_RATE = 0.15
DEVIN_RATE = 65
TOM_RATE = 50
THIRD_LABORER_RATE = 50
PILE_INSTALL_TIME_HRS = 0.5

# --- UI: Client Info ---
st.set_page_config(page_title="AKL Helical Estimate Tool")
st.title("🌱 AKL Helical Estimate Tool")
with st.sidebar:
    st.header("📋 Client Info")
    client_name = st.text_input("Client Name")
    job_address = st.text_input("Job Site Address")
    phone = st.text_input("Phone Number")
    email = st.text_input("Email Address")

    st.header("📦 Job Inputs")
    distance = st.number_input("Distance from Belle Cote (km)", min_value=0, value=30)
    pile_287 = st.number_input('2-7/8" Piles', min_value=0, value=0)
    pile_35 = st.number_input('3.5" Piles', min_value=0, value=0)
    ext_287 = st.number_input('2-7/8" Extensions', min_value=0, value=0)
    ext_35 = st.number_input('3.5" Extensions', min_value=0, value=0)
    auger = st.checkbox("Use Auger")
    excavator_hours = st.selectbox("Excavator Hours", options=list(range(1, 13)), index=7)

    st.header("⚙️ Add-Ons")
    travel_mats = st.checkbox("Travel Mats ($250)")
    tool_trailer = st.checkbox("Tool Trailer / Storage ($100)")
    boom_ext = st.checkbox("Boom Extension ($250)")
    admin_hours = st.number_input("Admin Time (hrs)", min_value=0, value=0)
    torque_report = st.checkbox("Torque Report / Stamped Letter ($150)")
    washroom_time = st.checkbox("Washroom Travel Time ($65)")

# --- Cost Calculation ---
total_piles = pile_287 + pile_35
install_time = total_piles * PILE_INSTALL_TIME_HRS
third_helper = total_piles > 10

# Labor
devin_setup = 3 * DEVIN_RATE
devin_travel = 4 * DEVIN_RATE
admin_cost = admin_hours * 10
washroom_cost = 65 if washroom_time else 0
labor_cost = devin_setup + devin_travel + admin_cost + washroom_cost
laborers = [TOM_RATE]
if third_helper:
    laborers.append(THIRD_LABORER_RATE)
labor_cost += sum([rate * install_time for rate in laborers])

# Equipment
excavator_cost = EXCAVATOR_RATE * excavator_hours
drive_unit_cost = DRIVE_UNIT_RATE * install_time
auger_cost = AUGER_RATE * install_time if auger else 0

# Materials
pile_cost = (pile_287 * PILE_COST_2_7_8) + (pile_35 * PILE_COST_3_5)
ext_cost = (ext_287 * EXTENSION_COST_2_7_8) + (ext_35 * EXTENSION_COST_3_5)

# Travel
trailer_cost = TRAILER_RATE if distance >= 90 else 250
passenger_vehicle_cost = PASSENGER_VEHICLE_RATE if third_helper else 0

# Add-ons
addons = 0
addons += 250 if travel_mats else 0
addons += 100 if tool_trailer else 0
addons += 250 if boom_ext else 0
addons += 150 if torque_report else 0

# Totals
subtotal = sum([
    labor_cost, excavator_cost, drive_unit_cost, auger_cost,
    pile_cost, ext_cost, trailer_cost, passenger_vehicle_cost, addons
])
hst = subtotal * HST_RATE
total = subtotal + hst

# --- Display ---
st.header("📊 Estimate Summary")
st.markdown(f"**Install Time:** {install_time:.1f} hours")
st.markdown(f"**Labor Cost:** ${labor_cost:,.2f}")
st.markdown(f"**Excavator Cost:** ${excavator_cost:,.2f}")
st.markdown(f"**Materials (Piles + Extensions):** ${pile_cost + ext_cost:,.2f}")
st.markdown(f"**Add-ons + Travel:** ${addons + trailer_cost + passenger_vehicle_cost:,.2f}")
st.markdown(f"**Subtotal:** ${subtotal:,.2f}")
st.markdown(f"**HST (15%):** ${hst:,.2f}")
st.markdown(f"### 🧾 Total: ${total:,.2f}")

# --- PDF Generation ---
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, "AKL Landscaping - Helical Pile Estimate", ln=1, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", 'I', 8)
        self.cell(0, 10, "www.AKLLandscaping.com | 902-802-4563", align='C')

if st.button("📥 Download Quote as PDF"):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, f"Client: {client_name}", ln=1)
    pdf.cell(0, 10, f"Address: {job_address}", ln=1)
    pdf.cell(0, 10, f"Phone: {phone}  |  Email: {email}", ln=1)
    pdf.ln(10)

    pdf.cell(0, 10, f"Install Time: {install_time:.1f} hrs", ln=1)
    pdf.cell(0, 10, f"Labor: ${labor_cost:,.2f}", ln=1)
    pdf.cell(0, 10, f"Excavator: ${excavator_cost:,.2f}", ln=1)
    pdf.cell(0, 10, f"Piles + Extensions: ${pile_cost + ext_cost:,.2f}", ln=1)
    pdf.cell(0, 10, f"Add-ons/Travel: ${addons + trailer_cost + passenger_vehicle_cost:,.2f}", ln=1)
    pdf.cell(0, 10, f"Subtotal: ${subtotal:,.2f}", ln=1)
    pdf.cell(0, 10, f"HST (15%): ${hst:,.2f}", ln=1)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"TOTAL: ${total:,.2f}", ln=1)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        with open(tmp.name, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        href = f'<a href="data:application/pdf;base64,{base64_pdf}" download="AKL_Quote.pdf">📄 Download PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
