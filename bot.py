import os
import re
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

PATCH_URL = "https://www.callofduty.com/patchnotes/2025/12/call-of-duty-bo7-warzone-season-01-patch-notes"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_page(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )
    response.raise_for_status()
    return response.text


def extract_content(html):
    soup = BeautifulSoup(html, "html.parser")

    for element in soup([
        "script",
        "style",
        "noscript",
        "nav",
        "footer",
        "header",
        "svg"
    ]):
        element.decompose()

    main = soup.find("main")

    if main:
        text = main.get_text("\n", strip=True)
    else:
        text = soup.get_text("\n", strip=True)

    lines = []

    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        if line:
            lines.append(line)

    return lines


def find_weapon_changes(lines):

    keywords = [
        "WEAPONS",
        "WEAPON",
        "ARMES",
        "ARME",
        "DÉGÂTS",
        "DEGATS",
        "DAMAGE",
        "RANGE",
        "PORTÉE",
        "RECOIL",
        "RECUL",
        "FIRE RATE",
        "CADENCE"
    ]

    result = []

    for i, line in enumerate(lines):

        if any(keyword.lower() in line.lower()
               for keyword in keywords):

            start = max(0, i - 2)
            end = min(len(lines), i + 10)

            for item in lines[start:end]:

                if item not in result:
                    result.append(item)

    return result


def classify(lines):

    buffs = []
    nerfs = []
    corrections = []

    for line in lines:

        lower = line.lower()

        if any(word in lower for word in [
            "increased",
            "increase",
            "improved",
            "augmenté",
            "augmentée",
            "augmentés",
            "augmentées",
            "amélioré",
            "améliorée",
            "amélioration"
        ]):
            buffs.append(line)

        elif any(word in lower for word in [
            "reduced",
            "reduce",
            "decreased",
            "decrease",
            "réduit",
            "réduite",
            "réduits",
            "réduites",
            "diminué",
            "diminuée",
            "diminution"
        ]):
            nerfs.append(line)

        elif any(word in lower for word in [
            "fixed",
            "fix",
            "correction",
            "corrected",
            "corrigé",
            "corrigée",
            "problème"
        ]):
            corrections.append(line)

    return buffs, nerfs, corrections


def unique(lines):

    result = []
    seen = set()

    for line in lines:

        key = line.lower()

        if key not in seen:
            seen.add(key)
            result.append(line)

    return result


def format_section(title, emoji, lines):

    lines = unique(lines)

    if not lines:
        return ""

    message = f"{emoji} **{title}**\n"

    for line in lines[:20]:

        message += f"• {line}\n"

    return message + "\n"


def send_discord(message):

    if not WEBHOOK_URL:
        raise RuntimeError(
            "Le secret DISCORD_WEBHOOK est absent."
        )

    response = requests.post(
        WEBHOOK_URL,
        json={
            "username": "COD Patch Bot",
            "content": message
        },
        timeout=30
    )

    response.raise_for_status()


def main():

    print("🔎 Ouverture des notes Warzone...")

    html = get_page(PATCH_URL)

    lines = extract_content(html)

    print("📄 Contenu récupéré :", len(lines), "lignes")

    changes = find_weapon_changes(lines)

    print("🔫 Éléments trouvés :", len(changes))

    buffs, nerfs, corrections = classify(changes)

    message = (
        "🇫🇷 **CALL OF DUTY — WARZONE**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    message += format_section(
        "BUFFS",
        "🟢",
        buffs
    )

    message += format_section(
        "NERFS",
        "🔴",
        nerfs
    )

    message += format_section(
        "CORRECTIONS",
        "🛠️",
        corrections
    )

    if not buffs and not nerfs and not corrections:

        message += (
            "⚠️ Aucun changement d'arme détecté automatiquement.\n\n"
        )

    message += (
        "🔗 **Notes officielles :**\n"
        + PATCH_URL
    )

    if len(message) > 1900:
        message = message[:1800]
        message += "\n\n🔗 **Notes officielles :**\n"
        message += PATCH_URL

    send_discord(message)

    print("✅ Message envoyé sur Discord.")


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
