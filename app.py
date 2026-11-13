import streamlit as st
import requests
import xml.etree.ElementTree as ET
import re
import html
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Doet Microsoft het al?", page_icon="🖥️", layout="centered")

# Automatisch verversen elke 30 seconden
st_autorefresh(interval=30000, key="statusrefresh")

ENDPOINTS = {
    "Microsoft Login (Entra ID)": "https://login.microsoftonline.com",
    "Microsoft 365 Portal": "https://portal.office.com",
}

RSS_FEEDS = {
    "Microsoft 365": "https://status.cloud.microsoft/api/feed/mac",
    "Microsoft Azure": "https://rssfeed.azure.status.microsoft/en-us/status/feed/"
}

# Alleen deze bekende onderdelen tonen we in het overzicht (de rest is IT-ruis)
RELEVANT_SERVICES = (
    "exchange online",
    "outlook",
    "microsoft teams",
    "microsoft 365 apps",
    "onedrive",
    "sharepoint",
    "microsoft copilot"
)

def parse_clean_bullets(raw_html):
    """Zet HTML-blokken om naar losse, overzichtelijke bulletpoints voor relevante apps."""
    if not raw_html:
        return []
    
    # Eerst HTML-entiteiten (zoals &lt;div&gt;) terugzetten naar echte tags
    unescaped = html.unescape(raw_html)
    # Vervang sluitende tags en linebreaks door een duidelijke scheiding
    text_with_breaks = re.sub(r'</div\s*>|<br\s*/?>|</p\s*>', '\n', unescaped, flags=re.IGNORECASE)
    # Verwijder overige HTML-tags
    clean_text = re.sub(r'<.*?>', '', text_with_breaks)
    
    bullets = []
    for line in clean_text.split('\n'):
        line = ' '.join(line.split()).strip(" -•")
        if not line:
            continue
        
        line_lower = line.lower()
        # Filter alleen de diensten die voor gewone gebruikers relevant zijn
        if any(line_lower.startswith(srv) for srv in RELEVANT_SERVICES):
            if ":" in line:
                service_name, details = line.split(":", 1)
                bullets.append(f"**{service_name.strip()}:** {details.strip()}")
            else:
                bullets.append(line)
                
    return bullets

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
    filtered_bullets = []
    fallback_titles = []
    has_incident = False

    for service, url in RSS_FEEDS.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for item in root.findall(".//item"):
                    title = item.find("title").text if item.find("title") is not None else ""
                    desc = item.find("description").text if item.find("description") is not None else ""
                    
                    full_lower = (title + " " + desc).lower()
                    if full_lower and "resolved" not in full_lower and "restored" not in full_lower:
                        has_incident = True
                        
                        bullets = parse_clean_bullets(desc)
                        if bullets:
                            for b in bullets:
                                if b not in filtered_bullets:
                                    filtered_bullets.append(b)
                        elif title:
                            fallback_titles.append(f"**{service}:** {title}")
                            
                        if "outlook" in full_lower or "exchange" in full_lower or "mail" in full_lower:
                            outlook_incident = True
                        if "teams" in full_lower:
                            teams_incident = True
        except Exception:
            pass
            
    display_items = filtered_bullets if filtered_bullets else fallback_titles
    return display_items, outlook_incident, teams_incident, has_incident

# UI Opbouw
st.markdown("<h1 style='text-align: center;'>Doet Microsoft het al?</h1>", unsafe_allow_html=True)

with st.spinner("Status controleren..."):
    endpoints_ok, endpoint_details = check_endpoints()
    incident_items, outlook_inc, teams_inc, has_incident = check_rss_incidents()

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

# Uitklapmenu met overzichtelijke bulletpoints
with st.expander("Bekijk wat er precies speelt"):
    if incident_items:
        for item in incident_items:
            st.markdown(f"- {item}")
    else:
        st.success("Geen actieve storingen gemeld in de feeds.")

    st.divider()
    st.caption("**Server-checks**")
    for name, (is_up, status_text) in endpoint_details.items():
        icon = "🟢" if is_up else "🔴"
        st.write(f"{icon} **{name}** — `{status_text}`")

    st.caption(f"Laatste check: {datetime.now().strftime('%H:%M:%S')} (servertijd)")
