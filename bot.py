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
# INTERNET
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

        "Damage": "Dégâts",
        "damage": "dégâts",

        "Max Damage": "Dégâts max.",

        "Minimum Damage": "Dégâts minimum",

        "Damage Range": "Portée des dégâts",

        "Range": "Portée",
        "range": "portée",

        "Bullet Velocity": "Vitesse des projectiles",

        "Recoil": "Recul",

        "Vertical Recoil": "Recul vertical",

        "Horizontal Recoil": "Recul horizontal",

        "Fire Rate": "Cadence de tir",

        "Rate of Fire": "Cadence de tir",

        "Headshot": "Tir à la tête",

        "Headshot Multiplier": "Multiplicateur de tir à la tête",

        "Magazine Size": "Taille du chargeur",

        "Reload Speed": "Vitesse de rechargement",

        "Movement Speed": "Vitesse de déplacement",

        "Sprint Speed": "Vitesse de sprint",

        "ADS Speed": "Vitesse ADS",

        "Gunkick": "Recul de visée",

        "Viewkick": "Recul de caméra",

        "Penalty": "Malus",

        "Benefit": "Bonus",

        "Increased": "Augmenté",
        "increased": "augmenté",

        "Reduced": "Réduit",
        "reduced": "réduit",

        "Decreased": "Diminué",
        "decreased": "diminué",

        "Improved": "Amélioré",
        "improved": "amélioré",

        "seconds": "secondes",
        "meters": "mètres",

        "to": "à"
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
# ARMES CONNUES
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
# DÉTECTION DE L'ARME
# =========================================================

def detect_weapon(text, current):

    upper = text.upper()

    for weapon in WEAPONS:

        if weapon in upper:

            return weapon

    return current


# =========================================================
# CLASSIFICATION INTELLIGENTE
# =========================================================

def classify(text):

    lower = text.lower()

    # -----------------------------------------------------
    # MALUS
    # -----------------------------------------------------

    if (
        "penalty reduced" in lower
        or "penalty decreased" in lower
    ):

        return "buff"

    if (
        "penalty increased" in lower
        or "penalty increased" in lower
    ):

        return "nerf"

    # -----------------------------------------------------
    # BONUS
    # -----------------------------------------------------

    if (
        "benefit increased" in lower
        or "benefit improved" in lower
    ):

        return "buff"

    if (
        "benefit reduced" in lower
        or "benefit decreased" in lower
    ):

        return "nerf"

    # -----------------------------------------------------
    # RECUL
    # -----------------------------------------------------

    if "recoil" in lower:

        if (
            "reduced" in lower
            or "decreased" in lower
        ):

            return "buff"

        if (
            "increased" in lower
            or "increased" in lower
        ):

            return "nerf"

    # -----------------------------------------------------
    # DÉGÂTS
    # -----------------------------------------------------

    if "damage" in lower:

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
    # CADENCE
    # -----------------------------------------------------

    if (
        "fire rate" in lower
        or "rate of fire" in lower
    ):

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
    # FLÈCHES DU TABLEAU
    # -----------------------------------------------------

    if "⇧" in text or "↑" in text:

        return "buff"

    if "⇩" in text or "↓" in text:

        return "nerf"

    return None


# =========================================================
# IGNORER LES DESCRIPTIONS
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
        "this weapon fires"
    ]

    for word in forbidden:

        if word in lower:

            return True

    return False


# =========================================================
# EXTRACTION
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

    result = []

    for element in elements:

        text = clean(
            element.get_text(
                " ",
                strip=True
            )
        )

        if text:

            result.append(text)

    return result


# =========================================================
# SECTION ARMES
# =========================================================

def get_weapon_section(lines):

    start = None

    for index, line in enumerate(lines):

        if line.upper() == "WEAPONS":

            start = index
            break

    if start is None:

        return []

    result = []

    for line in lines[start:]:

        upper = line.upper()

        if upper in [
            "BUG FIXES",
            "BLACK OPS ROYALE",
            "GAMEPLAY",
            "KILLSTREAKS"
        ]:

            break

        result.append(line)

    return result


# =========================================================
# CONVERSION DES TABLEAUX
# =========================================================

def normalize_value(value):

    value = clean(value)

    value = value.replace(
        "⇧",
        ""
    )

    value = value.replace(
        "⇩",
        ""
    )

    value = value.replace(
        "↑",
        ""
    )

    value = value.replace(
        "↓",
        ""
    )

    return value.strip()


def extract_numeric_change(text):

    # Recherche :
    #
    # 38 → 41
    # 38 -> 41
    # 38 to 41
    #
    match = re.search(
        r"(\d+(?:\.\d+)?%?)\s*"
        r"(?:→|->|to)\s*"
        r"(\d+(?:\.\d+)?%?)",
        text,
        re.IGNORECASE
    )

    if match:

        return (
            match.group(1),
            match.group(2)
        )

    return None


# =========================================================
# EXTRACTION DES MODIFICATIONS
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

        text = normalize_value(
            line
        )

        # -------------------------------------------------
        # Valeur numérique
        # -------------------------------------------------

        numeric = extract_numeric_change(
            text
        )

        if numeric:

            before, after = numeric

            # On reconstruit la ligne proprement
            text = re.sub(
                r"(\d+(?:\.\d+)?%?)\s*"
                r"(?:→|->|to)\s*"
                r"(\d+(?:\.\d+)?%?)",
                f"{before} → {after}",
                text,
                flags=re.IGNORECASE
            )

        # -------------------------------------------------
        # Nettoyage
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

        # On ignore les simples chiffres seuls
        if re.fullmatch(
            r"[\d\s\-\>\<m%]+",
            text
        ):

            continue

        entry = (
            f"**{current_weapon}** — "
            f"{translate(text)}"
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
# UNIQUE
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
            "DISCORD_WEBHOOK absent."
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

        chunks.append(
            message
        )

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
# PROGRAMME
# =========================================================

def main():

    print(
        "🔎 Lecture du patch Warzone..."
    )

    html = get_page(
        PATCH_URL
    )

    lines = extract_lines(
        html
    )

    weapon_lines = get_weapon_section(
        lines
    )

    print(
        f"🔫 {len(weapon_lines)} lignes armes."
    )

    last_patch = get_last_patch()

    if last_patch == PATCH_URL:

        print(
            "ℹ️ Patch déjà envoyé."
        )

        return

    buffs, nerfs = extract_changes(
        weapon_lines
    )

    print(
        f"🟢 Buffs : {len(buffs)}"
    )

    print(
        f"🔴 Nerfs : {len(nerfs)}"
    )

    message = (
        "🇫🇷 **CALL OF DUTY — WARZONE**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if buffs:

        message += (
            "🟢 **BUFFS**\n"
        )

        for item in buffs[:15]:

            message += (
                f"• {item}\n"
            )

        message += "\n"

    if nerfs:

        message += (
            "🔴 **NERFS**\n"
        )

        for item in nerfs[:15]:

            message += (
                f"• {item}\n"
            )

        message += "\n"

    if not buffs and not nerfs:

        message += (
            "⚠️ Aucun changement d'arme "
            "détecté.\n\n"
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
        "✅ Message Discord envoyé."
    )


if __name__ == "__main__":

    main()
