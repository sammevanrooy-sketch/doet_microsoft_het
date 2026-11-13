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
    """Haalt alle HTML-tags weg zodat alleen schone tekst overblijft."""
    cleanr = re.compile('<.*?>')
    cleanned = re.sub(cleanr, '', raw_html)
    # Dubbele spaties of witruimtes opruimen
    return ' '.join(cleanned.split())

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
    live_messages = []
    has_incident = False

    for service, url in RSS_FEEDS.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for item in root.findall(".//item"):
                    title = item.find("title").text if item.find("title") is not None else ""
                    desc = item.find("description").text if item.find("description") is not None else ""
                    
                    clean_title = clean_html(title)
                    clean_desc = clean_html(desc)
                    full_text = (clean_title + " " + clean_desc).lower()
                    
                    if full_text and "resolved" not in full_text and "restored" not in full_text:
                        has_incident = True
                        
                        # Voeg de schoongemaakte melding toe aan de lijst
                        display_text = f"**{clean_title}**: {clean_desc}" if clean_desc else clean_title
                        if display_text not in live_messages:
                            live_messages.append(display_text)
                            
                        if "outlook" in full_text or "exchange" in full_text or "mail" in full_text or "microsoft 365" in full_text:
                            outlook_incident = True
                        if "teams" in full_text:
                            teams_incident = True
        except Exception:
            pass
            
    return live_messages, outlook_incident, teams_incident, has_incident

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
        "<p style='color: #fef3c7; font-size: 18px; margin-top: 10px;'>Microsoft meldt een actieve storing.</p>"
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
        st.warning("📧 **Outlook:** Melding / Storing")
    else:
        st.success("📧 **Outlook:** Werkt")

with col2:
    if not endpoints_ok:
        st.error("💬 **Teams:** Offline")
    elif teams_inc:
        st.warning("💬 **Teams:** Melding / Storing")
    else:
        st.success("💬 **Teams:** Werkt")

st.write("")

# Uitklapmenu met de echte, schoongemaakte meldingen van Microsoft
with st.expander("Bekijk de exacte Microsoft storingsmeldingen"):
    if messages:
        for msg in messages:
            st.info(msg)
    else:
        st.success("Geen actieve storingen gemeld in de feeds.")

    st.subheader("Server-checks")
    for name, (is_up, status_text) in endpoint_details.items():
        icon = "🟢" if is_up else "🔴"
        st.write(f"{icon} **{name}** — `{status_text}`")

    st.caption(f"Laatste check: {datetime.now().strftime('%H:%M:%S')} (servertijd)")
