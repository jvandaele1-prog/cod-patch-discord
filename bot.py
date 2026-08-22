import os
import json
import re
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

PATCH_URL = "https://www.callofduty.com/fr/patchnotes"


def get_page():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        PATCH_URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()
    return response.text


def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(["script", "style", "noscript"]):
        element.decompose()

    text = soup.get_text("\n")

    lines = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        if line:
            lines.append(line)

    return lines


def find_latest_patch(lines):
    keywords = [
        "Warzone",
        "Notes de correctif",
        "Notes de mise à jour",
        "Armes",
        "ARMES",
        "BUFF",
        "NERF"
    ]

    matches = []

    for i, line in enumerate(lines):
        if any(keyword.lower() in line.lower() for keyword in keywords):
            start = max(0, i - 3)
            end = min(len(lines), i + 25)

            block = lines[start:end]

            for item in block:
                if item not in matches:
                    matches.append(item)

            if len(matches) >= 80:
                break

    return matches[:80]


def send_to_discord(message):
    if not WEBHOOK_URL:
        raise RuntimeError(
            "Le secret DISCORD_WEBHOOK n'est pas configuré."
        )

    payload = {
        "username": "COD Patch Bot",
        "content": message
    }

    response = requests.post(
        WEBHOOK_URL,
        json=payload,
        timeout=30
    )

    response.raise_for_status()


def main():
    print("Recherche des notes Call of Duty...")

    html = get_page()
    lines = extract_text(html)

    patch = find_latest_patch(lines)

    if not patch:
        print("Aucune note trouvée.")
        return

    message = "🇫🇷 **CALL OF DUTY — NOTES DE CORRECTIF**\n\n"

    message += "\n".join(
        f"• {line}"
        for line in patch
    )

    message += (
        "\n\n🔗 **Notes officielles :**\n"
        + PATCH_URL
    )

    # Discord limite les messages à 2000 caractères.
    if len(message) > 1900:
        message = message[:1900] + "\n\n…"

    send_to_discord(message)

    print("Message envoyé sur Discord.")


if __name__ == "__main__":
    main()
