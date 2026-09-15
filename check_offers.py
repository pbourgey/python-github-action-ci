import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests

API_URL = "https://civiweb-api-prd.azurewebsites.net/api/Offers/search"
API_KEY = os.environ.get(
    "API_KEY", "l+KwpoLPiXlsjxNT/NQ2iOFz8+iuygxAODs9FeAEWYM="
)

# Configuration E-mail (depuis les secrets d'environnement)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
EMAIL_TO = os.environ.get("EMAIL_TO", SMTP_USER)

SEEN_FILE = "seen_ids.txt"

PAYLOAD = {
    "limit": 50,
    "skip": 0,
    "query": None,
    "specializationsIds": ["212"],
    "missionsTypesIds": ["VIA", "VIE"],
    "missionsDurations": [
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "20",
        "21",
        "22",
        "23",
        "24",
    ],
    "geographicZones": ["7", "1", "2", "3", "4", "6"],
    "studiesLevelId": ["3", "4"],
    "teletravail": ["0"],
    "porteEnv": ["0"],
    "activitySectorId": [],
    "countriesIds": [],
    "companiesSizes": [],
    "entreprisesIds": [0],
    "missionStartDate": None,
}

HEADERS = {"Content-Type": "application/json", "x-api-key": API_KEY}


def send_email(new_offers):
  subject = f"🚨 {len(new_offers)} nouvelle(s) offre(s) V.I.E détectée(s) !"

  lines = []
  for o in new_offers:
    link = f"https://mon-vie-via.businessfrance.fr/offres/{o['id']}"
    lines.append(
        f"• {o.get('organizationName')} — {o.get('missionTitle')}\n"
        f"  Lieu : {o.get('cityName')}, {o.get('countryName')} | Indemnité :"
        f" {o.get('indemnite')} €/mois\n"
        f"  Lien : {link}\n"
    )

  body = (
      f"Bonjour,\n\nVoici les nouvelles offres correspondant à tes critères"
      f" :\n\n"
      + "\n".join(lines)
  )

  msg = MIMEMultipart()
  msg["From"] = SMTP_USER
  msg["To"] = EMAIL_TO
  msg["Subject"] = subject
  msg.attach(MIMEText(body, "plain", "utf-8"))

  with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
    server.starttls()
    server.login(SMTP_USER, SMTP_PASS)
    server.send_message(msg)


def main():
  # 1. Charger les IDs déjà vus
  seen_ids = set()
  if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
      seen_ids = set(f.read().splitlines())

  # 2. Récupérer les offres
  resp = requests.post(API_URL, json=PAYLOAD, headers=HEADERS, timeout=20)
  resp.raise_for_status()
  data = resp.json()
  offers = data.get("result", [])

  # 3. Identifier les nouvelles offres
  new_offers = [o for o in offers if str(o["id"]) not in seen_ids]

  # 4. Notifier si nécessaire
  if new_offers and seen_ids:
    print(f"{len(new_offers)} nouvelle(s) offre(s) trouvée(s). Envoi du mail...")
    send_email(new_offers)
  elif not seen_ids:
    print(
        f"Initialisation : {len(offers)} offres enregistrées sans notification."
    )
  else:
    print("Aucune nouvelle offre détectée.")

  # 5. Mettre à jour le fichier des IDs
  current_ids = {str(o["id"]) for o in offers}
  updated_ids = seen_ids.union(current_ids)
  with open(SEEN_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(sorted(updated_ids)))


if __name__ == "__main__":
  main()
