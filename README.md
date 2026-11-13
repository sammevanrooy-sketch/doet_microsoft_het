# Doet Microsoft het al? 🖥️

Een snelle en real-time statuschecker voor Microsoft-diensten, gebouwd met Python en Streamlit. De app controleert direct of essentiële Microsoft-servers reageren en of er actieve incidenten zijn (zoals bij Outlook of Teams).

## 🚀 Functionaliteiten
* **Directe Server Pings:** Controleert of de hoofdinfrastructuur (zoals Entra ID/Login, M365 Portal, Outlook en Teams) bereikbaar is.
* **Live RSS Statusfeeds:** Leest actieve storingen uit de officiële statusfeeds van Microsoft.
* **Visuele Statusindicatoren:** Toont direct een duidelijke **JA**, **NEE** of **DEELS / STORING** indicator.
* **Specifieke Dienst-checks:** Handige statuskaarten voor onder andere Outlook Web en Microsoft Teams.
* **Automatische Verversing:** Ververst de status automatisch elke 30 seconden.

## 🛠️ Technische Stack
* **Python**
* **Streamlit** (voor de webinterface)
* **Requests** (voor netwerkrequests en pings)
* **Streamlit-Autofresh** (voor de automatische pagina-verversing)

## 📦 Installatie & Lokaal Draaien
Wil je de app lokaal op je eigen computer testen? Volg dan deze stappen:

1. Clone of download deze repository.
2. Installeer de benodigde pakketten via de terminal:
   ```bash
   pip install -r requirements.txt