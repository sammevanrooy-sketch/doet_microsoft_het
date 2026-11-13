import streamlit as st
import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Doet Microsoft het al?", page_icon="🖥️", layout="centered")

# Automatisch verversen elke 30 seconden
st_autorefresh(interval=30000, key="statusrefresh")

# Stabiele hoofdportalen pingen
ENDPOINTS = {
    "Microsoft Login (Entra ID)": "https://login.microsoftonline.com",
    "Microsoft 365 Portal": "https://portal.office.com",
}

RSS_FEEDS = {
    "Microsoft 365": "https://status.cloud.microsoft/api/feed/mac",
    "Microsoft Azure": "https://rssfeed.azure.status.microsoft/en-us/status/feed/"
}

def clean_html(raw_html):
    """Haalt alle HTML-tags zoals <div> en <br> weg voor schone tekst."""
    cleanr = re.compile('<.*?>')
    cleanned = re.sub(cleanr, '', raw_html)
    return cleanned.strip()

def translate_to_jip_and_janneke(text):
    """Zet moeilijke Microsoft-termen om naar begrijpelijke Jip-en-Janneke taal."""
    t = text.lower()
    
    # Als het over mail/Outlook gaat
    if "exchange" in t or "outlook" in t or "mailbox" in t or "mail" in t:
        return "📧 **Outlook:** Het kan even duren voordat mailtjes binnenkomen of verstuurd worden."
    
    # Als het over Teams gaat
    if "teams" in t or "chat" in t or "meeting" in t:
        return "💬 **Teams:** Berichten sturen of videobellen kan tijdelijk haperen."
    
    # Als het over inloggen gaat
    if "sign-in" in t or "login" in t or "authentication" in t:
        return "🔑 **Inloggen:** Je kunt misschien moeite hebben met inloggen op je account."
    
    # Als het over bestanden / OneDrive gaat
    if "onedrive" in t or "sharepoint" in t or "files" in t:
        return "📁 **Bestanden:** Documenten openen of opslaan in de cloud lukt misschien niet direct."

    # Standaard heldere vertaling voor overige M365 storingen
    return "⚠️ **Microsoft 365:** Er is een algemene storing waardoor sommige functies haperen."

def check_endpoints():
    results = {}
    all_up = True
    for name, url in ENDPOINTS.items():
        try:
            response = requests.get(url, timeout=5)
            is_up = response.status_code < 500
            results[name] = (is_up, f"HTTP {response.status_code}")
            if not is_up:
                all_up = False
        except requests.RequestException:
            results[name] = (False, "Geen verbinding / Timeout")
            all_up = False
    return all_up, results

def check_rss_incidents():
    outlook_incident = False
    teams_incident = False
    simple_messages = []
    has_incident = False

    for service, url in RSS_FEEDS.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for item in root.findall(".//item"):
                    title = item.find("title").text if item.find("title") is not None else ""
                    desc = item.find("description").text if item.find("description") is not None else ""
                    
                    full_raw = title + " " + desc
                    clean_text = clean_html(full_raw)
                    full_lower = clean_text.lower()
                    
                    if full_lower and "resolved" not in full_lower and "restored" not in full_lower:
                        has_incident = True
                        jip_text = translate_to_jip_and_janneke(full_lower)
                        
                        if jip_text not in simple_messages:
                            simple_messages.append(jip_text)
                            
                        if "outlook" in full_lower or "exchange" in full_lower or "mail" in full_lower:
                            outlook_incident = True
                        if "teams" in full_lower:
                            teams_incident = True
        except Exception:
            pass
            
    return simple_messages, outlook_incident, teams_incident, has_incident

# UI Opbouw
st.markdown("<h1 style='text-align: center;'>Doet Microsoft het al?</h1>", unsafe_allow_html=True)

with st.spinner("Status controleren..."):
    endpoints_ok, endpoint_details = check_endpoints()
    messages, outlook_inc, teams_inc, has_incident = check_rss_incidents()

st.divider()

# Grote JA / DEELS / NEE weergave
if endpoints_ok and not has_incident:
    st.markdown(
        "<div style='background-color: #1e4620; padding: 40px; border-radius: 15px; text-align: center;'>"
        "<h1 style='color: #4ade80; font-size: 80px; margin: 0;'>JA</h1>"
        "<p style='color: #dcfce7; font-size: 18px; margin-top: 10px;'>Alles werkt zoals het hoort!</p>"
        "</div>",
        unsafe_allow_html=True
    )
elif endpoints_ok and has_incident:
    st.markdown(
        "<div style='background-color: #4a3511; padding: 40px; border-radius: 15px; text-align: center;'>"
        "<h1 style='color: #fbbf24; font-size: 65px; margin: 0;'>DEELS</h1>"
        "<p style='color: #fef3c7; font-size: 18px; margin-top: 10px;'>Microsoft meldt een kleine storing.</p>"
        "</div>",
        unsafe_allow_html=True
    )
else:
    st.markdown(
        "<div style='background-color: #4c1d1d; padding: 40px; border-radius: 15px; text-align: center;'>"
        "<h1 style='color: #f87171; font-size: 80px; margin: 0;'>NEE</h1>"
        "<p style='color: #fee2e2; font-size: 18px; margin-top: 10px;'>De inlogservers liggen eruit.</p>"
        "</div>",
        unsafe_allow_html=True
    )

st.write("")

# Schone statuskaarten
col1, col2 = st.columns(2)

with col1:
    if not endpoints_ok:
        st.error("📧 **Outlook:** Offline")
    elif outlook_inc:
        st.warning("📧 **Outlook:** Mogelijke vertraging")
    else:
        st.success("📧 **Outlook:** Werkt")

with col2:
    if not endpoints_ok:
        st.error("💬 **Teams:** Offline")
    elif teams_inc:
        st.warning("💬 **Teams:** Mogelijke vertraging")
    else:
        st.success("💬 **Teams:** Werkt")

st.write("")

# Uitklapmenu met heldere Jip-en-Janneke taal i.p.v. HTML-bende
with st.expander("Bekijk wat er precies aan de hand is"):
    if messages:
        for msg in messages:
            st.write(msg)
    else:
        st.success("Geen actieve storingen gemeld.")

    st.subheader("Server-checks")
    for name, (is_up, status_text) in endpoint_details.items():
        icon = "🟢" if is_up else "🔴"
        st.write(f"{icon} **{name}** — `{status_text}`")

    st.caption(f"Laatste check: {datetime.now().strftime('%H:%M:%S')} (servertijd)")
