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


# =========================================================
# ARMES
# =========================================================

WEAPONS = [
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


# =========================================================
# TÉLÉCHARGEMENT
# =========================================================

def get_page(url):

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.text


# =========================================================
# NETTOYAGE
# =========================================================

def clean(text):

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


# =========================================================
# TRADUCTION
# =========================================================

def translate(text):

    replacements = {

        "Damage Range": "Portée des dégâts",
        "Max Damage": "Dégâts maximum",
        "Minimum Damage": "Dégâts minimum",
        "Damage": "Dégâts",

        "Bullet Velocity": "Vitesse des projectiles",

        "Vertical Recoil": "Recul vertical",
        "Horizontal Recoil": "Recul horizontal",
        "Recoil": "Recul",

        "Gunkick": "Recul de visée",
        "Viewkick": "Recul de caméra",

        "Fire Rate": "Cadence de tir",
        "Rate of Fire": "Cadence de tir",

        "Headshot Multiplier": "Multiplicateur de tir à la tête",
        "Headshot": "Tir à la tête",

        "Magazine Size": "Taille du chargeur",

        "Reload Speed": "Vitesse de rechargement",

        "Movement Speed": "Vitesse de déplacement",

        "Sprint Speed": "Vitesse de sprint",

        "ADS Speed": "Vitesse ADS",

        "Benefit": "Bonus",
        "benefit": "bonus",

        "Penalty": "Malus",
        "penalty": "malus",

        "Increased": "augmenté",
        "increased": "augmenté",

        "Reduced": "réduit",
        "reduced": "réduit",

        "Decreased": "diminué",
        "decreased": "diminué",

        "Improved": "amélioré",
        "improved": "amélioré",

        "by": "de",

        "from": "de",

        "to": "à",

        "seconds": "secondes",
        "meters": "mètres"
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


# =========================================================
# DÉTECTION ARME
# =========================================================

def detect_weapon(text, current_weapon):

    upper = text.upper()

    for weapon in WEAPONS:

        if weapon in upper:
            return weapon

    return current_weapon


# =========================================================
# DESCRIPTION À IGNORER
# =========================================================

def is_description(text):

    lower = text.lower()

    forbidden = [
        "heavy metal projectiles",
        "electromagnetic coils",
        "unlockable via",
        "weekly challenge",
        "silently fires",
        "overall handling",
        "mobility",
        "fires two projectiles",
        "this weapon"
    ]

    return any(
        word in lower
        for word in forbidden
    )


# =========================================================
# CLASSIFICATION
# =========================================================

def classify(text):

    lower = text.lower()

    # -----------------------------------------------------
    # MALUS
    # -----------------------------------------------------

    if "penalty" in lower:

        if (
            "reduced" in lower
            or "decreased" in lower
            or "diminué" in lower
        ):
            return "buff"

        if (
            "increased" in lower
            or "augmenté" in lower
        ):
            return "nerf"

    # -----------------------------------------------------
    # BONUS
    # -----------------------------------------------------

    if "benefit" in lower:

        if (
            "increased" in lower
            or "improved" in lower
            or "augmenté" in lower
            or "amélioré" in lower
        ):
            return "buff"

        if (
            "reduced" in lower
            or "decreased" in lower
            or "réduit" in lower
        ):
            return "nerf"

    # -----------------------------------------------------
    # RECUL
    # -----------------------------------------------------

    if "recoil" in lower:

        if (
            "reduced" in lower
            or "decreased" in lower
            or "réduit" in lower
            or "diminué" in lower
        ):
            return "buff"

        if (
            "increased" in lower
            or "augmenté" in lower
        ):
            return "nerf"

    # -----------------------------------------------------
    # DÉGÂTS
    # -----------------------------------------------------

    if "damage" in lower:

        if (
            "increased" in lower
            or "improved" in lower
            or "augmenté" in lower
            or "amélioré" in lower
        ):
            return "buff"

        if (
            "reduced" in lower
            or "decreased" in lower
            or "réduit" in lower
            or "diminué" in lower
        ):
            return "nerf"

    # -----------------------------------------------------
    # PORTÉE
    # -----------------------------------------------------

    if "range" in lower:

        if (
            "increased" in lower
            or "improved" in lower
        ):
            return "buff"

        if (
            "reduced" in lower
            or "decreased" in lower
        ):
            return "nerf"

    # -----------------------------------------------------
    # VITESSE PROJECTILES
    # -----------------------------------------------------

    if "bullet velocity" in lower:

        if (
            "increased" in lower
            or "improved" in lower
        ):
            return "buff"

        if (
            "reduced" in lower
            or "decreased" in lower
        ):
            return "nerf"

    # -----------------------------------------------------
    # FLÈCHES
    # -----------------------------------------------------

    if "⇧" in text or "↑" in text:
        return "buff"

    if "⇩" in text or "↓" in text:
        return "nerf"

    return None


# =========================================================
# EXTRACTION HTML
# =========================================================

def extract_lines(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

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
            [
                "h1",
                "h2",
                "h3",
                "h4",
                "p",
                "li",
                "td",
                "th"
            ]
        )

    else:

        elements = soup.find_all(
            [
                "h1",
                "h2",
                "h3",
                "h4",
                "p",
                "li",
                "td",
                "th"
            ]
        )

    lines = []

    for element in elements:

        text = clean(
            element.get_text(
                " ",
                strip=True
            )
        )

        if text:
            lines.append(text)

    return lines


# =========================================================
# SECTION WEAPONS
# =========================================================

def weapon_section(lines):

    start = None

    for index, line in enumerate(lines):

        if line.upper() == "WEAPONS":
            start = index
            break

    if start is None:
        return []

    result = []

    for line in lines[start:]:

        if line.upper() in [
            "BUG FIXES",
            "BLACK OPS ROYALE",
            "GAMEPLAY",
            "KILLSTREAKS"
        ]:
            break

        result.append(line)

    return result


# =========================================================
# EXTRAIRE UNE MODIFICATION
# =========================================================

def format_change(text):

    text = clean(text)

    # -----------------------------------------------------
    # from X to Y
    # -----------------------------------------------------

    text = re.sub(
        r"(\d+(?:\.\d+)?%?)\s+"
        r"(?:from|de)\s+"
        r"(\d+(?:\.\d+)?%?)\s+"
        r"(?:to|à)\s+"
        r"(\d+(?:\.\d+)?%?)",
        r"\2 → \3",
        text,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # X to Y
    # -----------------------------------------------------

    text = re.sub(
        r"(\d+(?:\.\d+)?%?)\s+"
        r"(?:to|à)\s+"
        r"(\d+(?:\.\d+)?%?)",
        r"\1 → \2",
        text,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # "by 10%"
    # -----------------------------------------------------

    text = re.sub(
        r"\bby\s+(\d+(?:\.\d+)?%)",
        r"de \1",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\bpar\s+(\d+(?:\.\d+)?%)",
        r"de \1",
        text,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # m/s
    # -----------------------------------------------------

    text = text.replace(
        "m/s",
        " m/s"
    )

    text = re.sub(
        r"\s+m/s",
        " m/s",
        text
    )

    # -----------------------------------------------------
    # espaces
    # -----------------------------------------------------

    text = clean(text)

    return translate(text)


# =========================================================
# EXTRACTION DES CHANGEMENTS
# =========================================================

def extract_changes(lines):

    buffs = []
    nerfs = []

    current_weapon = "Arme"

    for line in lines:

        if is_description(line):
            continue

        current_weapon = detect_weapon(
            line,
            current_weapon
        )

        category = classify(line)

        if category is None:
            continue

        text = format_change(line)

        # -------------------------------------------------
        # Retirer le nom de l'arme
        # -------------------------------------------------

        for weapon in WEAPONS:

            if text.upper().startswith(
                weapon
            ):

                text = text[
                    len(weapon):
                ].strip()

                break

        if not text:
            continue

        # -------------------------------------------------
        # Éviter les lignes inutiles
        # -------------------------------------------------

        if re.fullmatch(
            r"[\d\s\-\>\<m%]+",
            text
        ):
            continue

        # -------------------------------------------------
        # Éviter certains doublons de tableau
        # -------------------------------------------------

        if len(text) < 3:
            continue

        entry = (
            f"**{current_weapon}** — "
            f"{text}"
        )

        if category == "buff":
            buffs.append(entry)

        elif category == "nerf":
            nerfs.append(entry)

    return (
        unique(buffs),
        unique(nerfs)
    )


# =========================================================
# SUPPRESSION DOUBLONS
# =========================================================

def unique(items):

    result = []

    seen = set()

    for item in items:

        key = item.lower()

        if key not in seen:

            seen.add(key)

            result.append(item)

    return result


# =========================================================
# DISCORD
# =========================================================

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

        message = message[
            position:
        ].lstrip()

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


# =========================================================
# MÉMOIRE
# =========================================================

def get_last_patch():

    if not os.path.exists(
        STATE_FILE
    ):
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

        file.write(
            PATCH_URL
        )


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "🔎 Lecture des notes Warzone..."
    )

    html = get_page(
        PATCH_URL
    )

    lines = extract_lines(
        html
    )

    lines = weapon_section(
        lines
    )

    print(
        f"🔫 {len(lines)} lignes récupérées."
    )

    # -----------------------------------------------------
    # Pour les tests, on ignore la mémoire si besoin.
    # -----------------------------------------------------

    last_patch = get_last_patch()

    if last_patch == PATCH_URL:

        print(
            "ℹ️ Patch déjà envoyé."
        )

        return

    buffs, nerfs = extract_changes(
        lines
    )

    print(
        f"🟢 {len(buffs)} buffs"
    )

    print(
        f"🔴 {len(nerfs)} nerfs"
    )

    # -----------------------------------------------------
    # MESSAGE
    # -----------------------------------------------------

    message = (
        "🇫🇷 **CALL OF DUTY — WARZONE**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if buffs:

        message += (
            "🟢 **BUFFS**\n\n"
        )

        for item in buffs:

            message += (
                f"• {item}\n"
            )

        message += "\n"

    if nerfs:

        message += (
            "🔴 **NERFS**\n\n"
        )

        for item in nerfs:

            message += (
                f"• {item}\n"
            )

        message += "\n"

    if not buffs and not nerfs:

        message += (
            "⚠️ Aucun changement détecté.\n\n"
        )

    message += (
        "📅 **Saison 05 Reloaded**\n\n"
        "🔗 **Notes officielles :**\n"
        f"{PATCH_URL}"
    )

    send_discord(
        message
    )

    save_last_patch()

    print(
        "✅ Patch envoyé sur Discord."
    )


if __name__ == "__main__":

    main()
