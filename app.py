import streamlit as st
import requests
import xml.etree.ElementTree as ET
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
            is_up = response.status_code < 500
            results[name] = (is_up, f"HTTP {response.status_code}")
            if not is_up:
                all_up = False
        except requests.RequestException:
            results[name] = (False, "Geen verbinding / Timeout")
            all_up = False
    return all_up, results

def check_rss_incidents():
    outlook_msg = ""
    teams_msg = ""
    all_incidents = []
    has_incident = False

    for service, url in RSS_FEEDS.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for item in root.findall(".//item"):
                    title = item.find("title").text if item.find("title") is not None else ""
                    desc = item.find("description").text if item.find("description") is not None else ""
                    full_text = (title + " " + desc).lower()
                    
                    if full_text and "resolved" not in full_text and "restored" not in full_text:
                        all_incidents.append(f"**{service}:** {title}")
                        has_incident = True
                        
                        # Koppel specifieke storingen aan Outlook of Teams
                        if "outlook" in full_text or "exchange" in full_text or "microsoft 365" in full_text:
                            outlook_msg = title
                        if "teams" in full_text:
                            teams_msg = title
        except Exception:
            pass
            
    return all_incidents, outlook_msg, teams_msg, has_incident

# UI Opbouw
st.markdown("<h1 style='text-align: center;'>Doet Microsoft het al?</h1>", unsafe_allow_html=True)

with st.spinner("Status controleren..."):
    endpoints_ok, endpoint_details = check_endpoints()
    incidents, outlook_msg, teams_msg, has_incident = check_rss_incidents()

st.divider()

# Grote JA / DEELS / NEE weergave
if endpoints_ok and not has_incident:
    st.markdown(
        "<div style='background-color: #1e4620; padding: 40px; border-radius: 15px; text-align: center;'>"
        "<h1 style='color: #4ade80; font-size: 80px; margin: 0;'>JA</h1>"
        "<p style='color: #dcfce7; font-size: 18px; margin-top: 10px;'>Alle Microsoft-diensten zijn operationeel.</p>"
        "</div>",
        unsafe_allow_html=True
    )
elif endpoints_ok and has_incident:
    st.markdown(
        "<div style='background-color: #4a3511; padding: 40px; border-radius: 15px; text-align: center;'>"
        "<h1 style='color: #fbbf24; font-size: 65px; margin: 0;'>DEELS</h1>"
        "<p style='color: #fef3c7; font-size: 18px; margin-top: 10px;'>Servers bereikbaar, maar Microsoft meldt actieve incidenten.</p>"
        "</div>",
        unsafe_allow_html=True
    )
else:
    st.markdown(
        "<div style='background-color: #4c1d1d; padding: 40px; border-radius: 15px; text-align: center;'>"
        "<h1 style='color: #f87171; font-size: 80px; margin: 0;'>NEE</h1>"
        "<p style='color: #fee2e2; font-size: 18px; margin-top: 10px;'>De inlogservers van Microsoft reageren niet.</p>"
        "</div>",
        unsafe_allow_html=True
    )

st.write("")

# Specifieke statuskaarten met eventuele storingsmelding erin verwerkt
col1, col2 = st.columns(2)

with col1:
    if not endpoints_ok:
        st.error("📧 **Outlook:** Offline")
    elif outlook_msg:
        st.warning(f"📧 **Outlook Melding:**\n\n{outlook_msg}")
    else:
        st.success("📧 **Outlook:** Werkt")

with col2:
    if not endpoints_ok:
        st.error("💬 **Teams:** Offline")
    elif teams_msg:
        st.warning(f"💬 **Teams Melding:**\n\n{teams_msg}")
    else:
        st.success("💬 **Teams:** Werkt")

st.write("")

# Details uitklapbaar maken
with st.expander("Bekijk technische details & meldingen"):
    st.subheader("Directe server-checks")
    for name, (is_up, status_text) in endpoint_details.items():
        icon = "🟢" if is_up else "🔴"
        st.write(f"{icon} **{name}** — `{status_text}`")

    st.subheader("Officiële Microsoft Status-feed")
    if incidents:
        for inc in incidents:
            st.warning(inc)
    else:
        st.success("Geen openstaande incidenten in de RSS-feeds gevonden.")

    st.caption(f"Laatste check: {datetime.now().strftime('%H:%M:%S')} (servertijd)")
