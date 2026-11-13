import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Doet Microsoft het al?", page_icon="🖥️", layout="centered")

# Automatisch verversen elke 30 seconden (30000 milliseconden)
st_autorefresh(interval=30000, key="statusrefresh")

# Endpoints om direct te pingen
ENDPOINTS = {
    "Microsoft Login (Entra ID)": "https://login.microsoftonline.com",
    "Microsoft 365 Portal": "https://portal.office.com",
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
            # 200-399 (inclusief redirects naar login) betekent dat de server reageert
            is_up = response.status_code < 400
            results[name] = (is_up, f"HTTP {response.status_code}")
            if not is_up:
                all_up = False
        except requests.RequestException as e:
            results[name] = (False, "Geen verbinding / Timeout")
            all_up = False
    return all_up, results

def check_rss_incidents():
    active_incidents = []
    for service, url in RSS_FEEDS.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for item in root.findall(".//item"):
                    title = item.find("title").text if item.find("title") is not None else ""
                    # Filter op items die niet als opgelost zijn gemarkeerd
                    if title and "resolved" not in title.lower() and "restored" not in title.lower():
                        active_incidents.append(f"**{service}:** {title}")
        except Exception:
            pass
    return active_incidents

# UI Opbouw
st.markdown("<h1 style='text-align: center;'>Doet Microsoft het al?</h1>", unsafe_allow_html=True)

if st.button("🔄 Nu verversen", use_container_width=True):
    st.rerun()

with st.spinner("Status controleren..."):
    endpoints_ok, endpoint_details = check_endpoints()
    incidents = check_rss_incidents()

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

# Details uitklapbaar maken zodat de pagina clean blijft
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
