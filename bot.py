import os
import re
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

PATCH_URL = (
    "https://www.callofduty.com/patchnotes/2026/08/"
    "call-of-duty-bo7-warzone-season-05-reloaded-patch-notes"
)

STATE_FILE = "last_patch.txt"

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


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


def get_content(html):

    soup = BeautifulSoup(html, "html.parser")

    for element in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "nav",
        "footer",
        "header"
    ]):
        element.decompose()

    main = soup.find("main")

    if main:
        elements = main.find_all(
            ["h1", "h2", "h3", "h4", "p", "li", "td", "th"]
        )
    else:
        elements = soup.find_all(
            ["h1", "h2", "h3", "h4", "p", "li", "td", "th"]
        )

    lines = []

    for element in elements:

        text = clean(
            element.get_text(" ", strip=True)
        )

        if text and text not in lines:
            lines.append(text)

    return lines


def find_weapon_section(lines):

    start = None

    for i, line in enumerate(lines):

        if line.strip().upper() == "WEAPONS":
            start = i
            break

    if start is None:
        return []

    result = []

    for line in lines[start:]:

        if line.strip().upper() in [
            "BUG FIXES",
            "BLACK OPS ROYALE"
        ]:
            break

        result.append(line)

    return result


def unique(items):

    result = []
    seen = set()

    for item in items:

        key = item.lower()

        if key not in seen:
            seen.add(key)
            result.append(item)

    return result


# ---------------------------------------------------------
# TRADUCTION
# ---------------------------------------------------------

def translate(text):

    replacements = {

        "Increased": "Augmenté",
        "increased": "augmenté",

        "Reduced": "Réduit",
        "reduced": "réduit",

        "Decreased": "Diminué",
        "decreased": "diminué",

        "Improved": "Amélioré",
        "improved": "amélioré",

        "Damage": "Dégâts",
        "damage": "dégâts",

        "Range": "Portée",
        "range": "portée",

        "Damage Range": "Portée des dégâts",

        "Bullet Velocity": "Vitesse des projectiles",

        "Recoil": "Recul",

        "Vertical Recoil": "Recul vertical",

        "Horizontal Recoil": "Recul horizontal",

        "Headshot": "Tir à la tête",

        "Headshot multiplier": "Multiplicateur de tir à la tête",

        "Magazine Size": "Taille du chargeur",

        "Fire Rate": "Cadence de tir",

        "Sprint to Fire speed": "Vitesse sprint → tir",

        "ADS Speed": "Vitesse ADS",

        "Benefit": "Bonus",

        "Penalty": "Malus",

        "increased from": "augmenté de",

        "decreased from": "réduit de",

        "reduced from": "réduit de",

        "improved from": "amélioré de",

        "to": "à",

        "All Modes": "Tous les modes",

        "BR/RES Only": "Battle Royale / Résurgence uniquement",

        "Max Damage": "Dégâts maximum",

        "Mid 1 Damage": "Dégâts moyens 1",

        "Minimum Damage": "Dégâts minimum",

        "seconds": "secondes",

        "meters": "mètres",

        "m/s": "m/s"
    }

    for english, french in sorted(
        replacements.items(),
        key=lambda x: len(x[0]),
        reverse=True
    ):

        text = text.replace(
            english,
            french
        )

    return text


# ---------------------------------------------------------
# DÉTECTION DES CHANGEMENTS
# ---------------------------------------------------------

def classify_change(line):

    lower = line.lower()

    # -----------------------------------------------------
    # IGNORER LES DESCRIPTIONS D'ARMES
    # -----------------------------------------------------

    description_words = [
        "heavy metal projectiles",
        "unlockable via",
        "silently fires",
        "series of electromagnetic coils",
        "overall handling and mobility",
        "weekly challenge reward",
        "this weapon",
        "fires two projectiles"
    ]

    if any(
        word in lower
        for word in description_words
    ):
        return None

    # -----------------------------------------------------
    # CAS PARTICULIER :
    # UN MALUS QUI DIMINUE = BUFF
    # -----------------------------------------------------

    if (
        "penalty reduced" in lower
        or "penalty decreased" in lower
        or "penalty reduced from" in lower
    ):
        return "buff"

    # -----------------------------------------------------
    # CAS PARTICULIER :
    # UN BONUS QUI AUGMENTE = BUFF
    # -----------------------------------------------------

    if (
        "benefit increased" in lower
        or "benefit improved" in lower
        or "benefit increased from" in lower
    ):
        return "buff"

    # -----------------------------------------------------
    # AUGMENTATIONS
    # -----------------------------------------------------

    buff_words = [
        "increased",
        "increase",
        "improved",
        "improvement",
        "augmenté",
        "augmentée",
        "augmentés",
        "augmentées",
        "amélioré",
        "améliorée",
        "amélioration",
        "⇧",
        "↑"
    ]

    # -----------------------------------------------------
    # DIMINUTIONS
    # -----------------------------------------------------

    nerf_words = [
        "reduced",
        "reduce",
        "decreased",
        "decrease",
        "reduction",
        "réduit",
        "réduite",
        "réduits",
        "réduites",
        "diminué",
        "diminuée",
        "diminution",
        "⇩",
        "↓"
    ]

    # -----------------------------------------------------
    # CORRECTIONS
    # -----------------------------------------------------

    correction_words = [
        "fixed",
        "fix",
        "addressed an issue",
        "correction",
        "corrected",
        "corrigé",
        "corrigée"
    ]

    if any(
        word in lower
        for word in correction_words
    ):
        return "correction"

    if any(
        word in lower
        for word in buff_words
    ):
        return "buff"

    if any(
        word in lower
        for word in nerf_words
    ):
        return "nerf"

    return None


def extract_weapon_name(line, previous_name):

    # Si la ligne contient déjà un nom connu,
    # on le conserve.

    weapon_names = [
        "AN-94",
        "EGRT-17",
        "FG-42",
        "M15 MOD 0",
        "MK35 ISR",
        "MXR-17",
        "VX COMPACT",
        "CBRS-3",
        "GREMLIN",
        "MPC-25",
        "RYDEN 45K",
        "STRUMWOLF 45",
        "MAMMOTH",
        "M10 BREACHER",
        "SG-12",
        "STRIDER 300",
        "PEACEKEEPER MK1"
    ]

    upper = line.upper()

    for weapon in weapon_names:

        if weapon in upper:
            return weapon

    return previous_name


def clean_change_line(line):

    # Retire les flèches inutiles
    line = line.replace("⇧", "")
    line = line.replace("↑", "")
    line = line.replace("⇩", "")
    line = line.replace("↓", "")

    # Nettoyage
    line = clean(line)

    return line


def extract_changes(lines):

    buffs = []
    nerfs = []
    corrections = []

    current_weapon = "Arme"

    for line in lines:

        # Mise à jour du nom de l'arme
        current_weapon = extract_weapon_name(
            line,
            current_weapon
        )

        category = classify_change(line)

        if category is None:
            continue

        line = clean_change_line(line)

        # Évite les lignes trop longues/descriptions
        if len(line) > 250:
            continue

        # On retire le nom d'arme répété
        for weapon in [
            "AN-94",
            "EGRT-17",
            "FG-42",
            "M15 MOD 0",
            "MK35 ISR",
            "MXR-17",
            "VX COMPACT",
            "CBRS-3",
            "GREMLIN",
            "MPC-25",
            "RYDEN 45K",
            "STRUMWOLF 45",
            "MAMMOTH",
            "M10 BREACHER",
            "SG-12",
            "STRIDER 300",
            "PEACEKEEPER MK1"
        ]:

            if line.upper().startswith(
                weapon
            ):

                line = line[len(weapon):].strip()

                break

        entry = (
            f"**{current_weapon}** — "
            f"{translate(line)}"
        )

        if category == "buff":
            buffs.append(entry)

        elif category == "nerf":
            nerfs.append(entry)

        elif category == "correction":
            corrections.append(entry)

    return (
        unique(buffs),
        unique(nerfs),
        unique(corrections)
    )


# ---------------------------------------------------------
# DISCORD
# ---------------------------------------------------------

def format_section(
    title,
    emoji,
    lines,
    maximum=700
):

    if not lines:
        return ""

    message = f"{emoji} **{title}**\n"

    total = len(message)

    for line in lines:

        item = f"• {line}\n"

        if total + len(item) > maximum:

            message += "• ...\n"
            break

        message += item
        total += len(item)

    return message + "\n"


def send_discord(message):

    if not WEBHOOK_URL:

        raise RuntimeError(
            "Le secret DISCORD_WEBHOOK est absent."
        )

    chunks = []

    while len(message) > 1900:

        position = message.rfind(
            "\n",
            0,
            1900
        )

        if position <= 0:
            position = 1900

        chunks.append(
            message[:position]
        )

        message = message[position:].lstrip()

    if message:
        chunks.append(message)

    for chunk in chunks:

        response = requests.post(
            WEBHOOK_URL,
            json={
                "username": "COD Patch Bot",
                "content": chunk
            },
            timeout=30
        )

        response.raise_for_status()


def get_last_patch():

    if not os.path.exists(STATE_FILE):
        return ""

    with open(
        STATE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return file.read().strip()


def save_last_patch():

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(PATCH_URL)


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print("🔎 Lecture des notes Warzone...")

    html = get_page(PATCH_URL)

    lines = get_content(html)

    weapon_section = find_weapon_section(
        lines
    )

    print(
        f"🔫 {len(weapon_section)} éléments trouvés."
    )

    last_patch = get_last_patch()

    if last_patch == PATCH_URL:

        print(
            "ℹ️ Patch déjà envoyé."
        )

        return

    buffs, nerfs, corrections = extract_changes(
        weapon_section
    )

    print(
        f"🟢 Buffs : {len(buffs)}"
    )

    print(
        f"🔴 Nerfs : {len(nerfs)}"
    )

    print(
        f"🛠️ Corrections : {len(corrections)}"
    )

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

    message += (
        "📅 **Saison 05 Reloaded**\n\n"
        "🔗 **Notes officielles :**\n"
        f"{PATCH_URL}"
    )

    send_discord(message)

    save_last_patch()

    print(
        "✅ Message envoyé sur Discord."
    )


if __name__ == "__main__":
    main()
