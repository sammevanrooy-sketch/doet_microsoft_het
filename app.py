import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Doet Microsoft het al?", page_icon="🖥️", layout="centered")

# Automatisch verversen elke 30 seconden (stabiel zonder loops)
st_autorefresh(interval=30000, key="statusrefresh")

# Endpoints om direct te pingen (inclusief Outlook en Teams)
ENDPOINTS = {
    "Microsoft Login (Entra ID)": "https://login.microsoftonline.com",
    "Microsoft 365 Portal": "https://portal.office.com",
    "Outlook Web": "https://outlook.office.com",
    "Microsoft Teams": "https://teams.microsoft.com",
    "Microsoft Statuspagina": "https://status.cloud.microsoft"
}

# Publieke RSS-feeds van Microsoft
RSS_FEEDS = {
    "Microsoft 365": "https://status.cloud.microsoft/api/feed/mac",
    "Microsoft Azure": "https://rssfeed.azure.status.microsoft/en-us/status/feed/"
}

def check_endpoints():
    results = {}
    all_up = True
    for name, url in ENDPOINTS.items():
        try:
            response = requests.get(url, timeout=5)
            is_up = response.status_code < 400
            results[name] = (is_up, f"HTTP {response.status_code}")
            if not is_up:
                all_up = False
        except requests.RequestException:
            results[name] = (False, "Geen verbinding / Timeout")
            all_up = False
    return all_up, results

def check_rss_incidents():
    active_incidents = []
    outlook_incident = False
    teams_incident = False

    for service, url in RSS_FEEDS.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for item in root.findall(".//item"):
                    title = item.find("title").text if item.find("title") is not None else ""
                    title_lower = title.lower()
                    if title and "resolved" not in title_lower and "restored" not in title_lower:
                        active_incidents.append(f"**{service}:** {title}")
                        if "outlook" in title_lower or "exchange" in title_lower:
                            outlook_incident = True
                        if "teams" in title_lower:
                            teams_incident = True
        except Exception:
            pass
    return active_incidents, outlook_incident, teams_incident

# UI Opbouw
st.markdown("<h1 style='text-align: center;'>Doet Microsoft het al?</h1>", unsafe_allow_html=True)

with st.spinner("Status controleren..."):
    endpoints_ok, endpoint_details = check_endpoints()
    incidents, outlook_inc, teams_inc = check_rss_incidents()

st.divider()

# Grote JA / NEE weergave
if endpoints_ok and not incidents:
    st.markdown(
        "<div style='background-color: #1e4620; padding: 40px; border-radius: 15px; text-align: center;'>"
        "<h1 style='color: #4ade80; font-size: 80px; margin: 0;'>JA</h1>"
        "<p style='color: #dcfce7; font-size: 18px; margin-top: 10px;'>Alle gecontroleerde services zijn bereikbaar en er zijn geen actieve meldingen.</p>"
        "</div>",
        unsafe_allow_html=True
    )
elif not endpoints_ok:
    st.markdown(
        "<div style='background-color: #4c1d1d; padding: 40px; border-radius: 15px; text-align: center;'>"
        "<h1 style='color: #f87171; font-size: 80px; margin: 0;'>NEE</h1>"
        "<p style='color: #fee2e2; font-size: 18px; margin-top: 10px;'>Een of meer essentiële Microsoft-servers reageren niet.</p>"
        "</div>",
        unsafe_allow_html=True
    )
else:
    st.markdown(
        "<div style='background-color: #4a3511; padding: 40px; border-radius: 15px; text-align: center;'>"
        "<h1 style='color: #fbbf24; font-size: 65px; margin: 0;'>DEELS / STORING</h1>"
        "<p style='color: #fef3c7; font-size: 18px; margin-top: 10px;'>De servers zijn bereikbaar, maar Microsoft meldt actieve incidenten.</p>"
        "</div>",
        unsafe_allow_html=True
    )

st.write("")

# Specifieke statuskaarten voor Outlook en Teams
login_up = endpoint_details["Microsoft Login (Entra ID)"][0]
outlook_up = endpoint_details["Outlook Web"][0] and login_up
teams_
