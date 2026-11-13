import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Doet Microsoft het al?", page_icon="🖥️", layout="centered")

# Automatisch verversen elke 30 seconden
st_autorefresh(interval=30000, key="statusrefresh")

# Endpoints gericht op de app-achterkant (Exchange/Outlook app backend)
ENDPOINTS = {
    "Microsoft Login (Entra ID)": "https://login.microsoftonline.com",
    "Outlook App & Exchange Server": "https://outlook.office365.com",
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
            # We gebruiken allow_redirects en timeout
            response = requests.get(url, timeout=5, allow_redirects=True)
            # < 500 betekent dat de server leeft (zelfs een 401 Unauthorized betekent dat de server online is!)
            is_up = response.status_code < 500
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
        "<p style='color: #dcfce7; font-size: 18px; margin-top: 10px;'>De servers voor de Outlook-app en Teams zijn bereikbaar.</p>"
        "</div>",
        unsafe_allow_html=True
    )
elif not endpoints_ok:
    st.markdown(
        "<div style='background-color: #4c1d1d; padding: 40px; border-radius: 15px; text-align: center;'>"
        "<h1 style='color: #f87171; font-size: 80px; margin: 0;'>NEE</h1>"
        "<p style='color: #fee2e2; font-size: 18px; margin-top: 10px;'>De mail- of inlogservers van Microsoft reageren niet.</p>"
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

# Specifieke statuskaarten voor Outlook App en Teams
login_up = endpoint_details["Microsoft Login (Entra ID)"][0]
outlook_app_up = endpoint_details["Outlook App & Exchange Server"][0] and login_up
teams_up = endpoint_details["Microsoft Teams"][0] and login_up

col1, col2 = st.columns(2)

with col1:
    if not outlook_app_up:
        st.error("📧 **Outlook App:** Offline")
    elif outlook_inc:
        st.warning("📧 **Outlook App:** Mogelijke storing")
    else:
        st.success("📧 **Outlook App:** Werkt")

with col2:
    if not teams_up:
        st.error("💬 **Teams:** Offline")
    elif teams_inc:
        st.warning("💬 **Teams:** Mogelijke storing")
    else:
        st.success("💬 **Teams:** Werkt")

st.write("")

# Details uitklapbaar maken
with st.expander("Bekijk technische details & meldingen"):
    st.subheader("Directe server-checks (App Backend)")
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
