import os
import re
import requests
from bs4 import BeautifulSoup


# =========================================================
# CONFIGURATION
# =========================================================

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
# TRADUCTIONS
# =========================================================

TRANSLATIONS = {

    "Bullet Velocity": "Vitesse des projectiles",
    "bullet velocity": "Vitesse des projectiles",

    "Vertical Recoil": "Recul vertical",
    "Horizontal Recoil": "Recul horizontal",
    "Recoil Control": "Contrôle du recul",
    "Recoil": "Recul",

    "Gunkick": "Recul de visée",
    "Viewkick": "Recul de caméra",

    "ADS Speed": "Vitesse ADS",
    "Aim Down Sight Speed": "Vitesse ADS",

    "Damage Range": "Portée des dégâts",
    "Max Damage": "Dégâts maximum",
    "Minimum Damage": "Dégâts minimum",
    "Damage": "Dégâts",

    "Fire Rate": "Cadence de tir",
    "Rate of Fire": "Cadence de tir",

    "Movement Speed": "Vitesse de déplacement",
    "Sprint Speed": "Vitesse de sprint",

    "Magazine Size": "Taille du chargeur",
    "Reload Speed": "Vitesse de rechargement",

    "Headshot": "Tir à la tête",
    "headshot": "Tir à la tête",

    "upper torso": "haut du torse",
    "upper body": "haut du corps",

    "Benefit": "Bonus",
    "benefit": "bonus",

    "Penalty": "malus",
    "penalty": "malus",

    "Increased": "augmenté",
    "increased": "augmenté",

    "Reduced": "réduit",
    "reduced": "réduit",

    "Decreased": "diminué",
    "decreased": "diminué",

    "Improved": "amélioré",
    "improved": "amélioré",

    "Now improves": "Améliore désormais",
    "now improves": "améliore désormais",

    "and": "et",
    "by": "de",

    "meters": "m",
    "meter": "m"
}


# =========================================================
# TÉLÉCHARGEMENT
# =========================================================

def get_page():

    response = requests.get(
        PATCH_URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.text


# =========================================================
# NETTOYAGE
# =========================================================

def clean(text):

    text = text.replace("àrse", "torse")
    text = text.replace("àrso", "torse")
    text = text.replace("Compensaàr", "Compensator")
    text = text.replace("Promonàry", "Promontory")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# TRADUCTION
# =========================================================

def translate(text):

    for english, french in sorted(
        TRANSLATIONS.items(),
        key=lambda x: len(x[0]),
        reverse=True
    ):

        text = text.replace(
            english,
            french
        )

    return clean(text)


# =========================================================
# DÉTECTION ARME
# =========================================================

def detect_weapon(
    text,
    current_weapon
):

    upper = text.upper()

    for weapon in WEAPONS:

        if weapon in upper:

            return weapon

    return current_weapon


# =========================================================
# IGNORER DESCRIPTION NOUVELLE ARME
# =========================================================

def is_description(text):

    lower = text.lower()

    words = [
        "heavy metal projectiles",
        "electromagnetic coils",
        "unlockable via",
        "weekly challenge",
        "silently fires",
        "overall handling",
        "mobility",
        "fires two projectiles"
    ]

    return any(
        word in lower
        for word in words
    )


# =========================================================
# IGNORER VALEURS DES TABLEAUX
# =========================================================

def is_table_value(text):

    text = text.strip()

    # Exemples :
    # 41⇧
    # 0 - 45m⇧
    # 45m⇧ - 60m
    # >60m⇧
    # 46⇩

    if not any(
        x in text
        for x in ["⇧", "⇩", "↑", "↓"]
    ):
        return False

    cleaned = re.sub(
        r"[⇧⇩↑↓]",
        "",
        text
    )

    cleaned = cleaned.strip()

    pattern = (
        r"^[\d\s\-\>\<\.m]+$"
    )

    return bool(
        re.fullmatch(
            pattern,
            cleaned,
            re.IGNORECASE
        )
    )


# =========================================================
# DÉTERMINER BUFF / NERF
# =========================================================

def classify(text):

    lower = text.lower()

    # Recul
    if any(
        x in lower
        for x in [
            "recoil",
            "recul",
            "gunkick",
            "viewkick"
        ]
    ):

        if any(
            x in lower
            for x in [
                "reduced",
                "reduced by",
                "réduit",
                "diminué"
            ]
        ):
            return "buff"

        if any(
            x in lower
            for x in [
                "increased",
                "augmenté"
            ]
        ):
            return "nerf"

    # Dégâts
    if any(
        x in lower
        for x in [
            "damage",
            "dégâts"
        ]
    ):

        if any(
            x in lower
            for x in [
                "increased",
                "improved",
                "augmenté",
                "amélioré"
            ]
        ):
            return "buff"

        if any(
            x in lower
            for x in [
                "reduced",
                "decreased",
                "réduit",
                "diminué"
            ]
        ):
            return "nerf"

    # Vitesse projectiles
    if any(
        x in lower
        for x in [
            "bullet velocity",
            "vitesse des projectiles"
        ]
    ):

        if any(
            x in lower
            for x in [
                "increased",
                "improved",
                "augmenté",
                "amélioré"
            ]
        ):
            return "buff"

        if any(
            x in lower
            for x in [
                "reduced",
                "decreased",
                "réduit",
                "diminué"
            ]
        ):
            return "nerf"

    # Portée
    if any(
        x in lower
        for x in [
            "damage range",
            "portée des dégâts"
        ]
    ):

        if any(
            x in lower
            for x in [
                "increased",
                "improved",
                "augmenté",
                "amélioré"
            ]
        ):
            return "buff"

        if any(
            x in lower
            for x in [
                "reduced",
                "decreased",
                "réduit",
                "diminué"
            ]
        ):
            return "nerf"

    # ADS
    if "ads" in lower:

        if any(
            x in lower
            for x in [
                "reduced",
                "diminué",
                "réduit"
            ]
        ):
            return "buff"

        if any(
            x in lower
            for x in [
                "increased",
                "augmenté"
            ]
        ):
            return "nerf"

    return None


# =========================================================
# FORMATER LES CHANGEMENTS
# =========================================================

def format_change(text):

    text = translate(text)

    # from X to Y
    text = re.sub(
        r"(?:de|from)\s+"
        r"(\d+(?:\.\d+)?)\s*"
        r"(m/s|%)\s+"
        r"(?:à|to)\s+"
        r"(\d+(?:\.\d+)?)\s*"
        r"(m/s|%)",
        r"\1 \2 → \3 \4",
        text,
        flags=re.IGNORECASE
    )

    # nombres simples
    text = re.sub(
        r"(?:de|from)\s+"
        r"(\d+(?:\.\d+)?)\s+"
        r"(?:à|to)\s+"
        r"(\d+(?:\.\d+)?)",
        r"\1 → \2",
        text,
        flags=re.IGNORECASE
    )

    # by X %
    text = re.sub(
        r"(augmenté|réduit|diminué)\s+by\s+"
        r"(\d+(?:\.\d+)?)%",
        r"\1 de \2 %",
        text,
        flags=re.IGNORECASE
    )

    # nettoyer espaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# SUPPRIMER LE NOM DE L'ARME
# =========================================================

def remove_weapon(text):

    for weapon in WEAPONS:

        if text.upper().startswith(
            weapon.upper()
        ):

            return text[
                len(weapon):
            ].strip()

    return text


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

    for i, line in enumerate(lines):

        if line.strip().upper() == "WEAPONS":

            start = i

            break

    if start is None:

        return lines

    result = []

    for line in lines[start:]:

        if line.upper() in [
            "BUG FIXES",
            "GAMEPLAY",
            "KILLSTREAKS",
            "EQUIPMENT",
            "PERKS"
        ]:

            break

        result.append(line)

    return result


# =========================================================
# SUPPRESSION DOUBLONS
# =========================================================

def remove_duplicates(items):

    result = []

    seen = set()

    for item in items:

        key = re.sub(
            r"\s+",
            " ",
            item.lower()
        ).strip()

        if key in seen:
            continue

        seen.add(key)

        result.append(item)

    return result


# =========================================================
# EXTRACTION
# =========================================================

def extract_changes(lines):

    buffs = []
    nerfs = []

    current_weapon = "Arme"

    for line in lines:

        if not line:
            continue

        if is_description(line):
            continue

        current_weapon = detect_weapon(
            line,
            current_weapon
        )

        # IMPORTANT :
        # Ignore complètement les valeurs
        # du tableau de dégâts.

        if is_table_value(line):
            continue

        category = classify(line)

        if category is None:
            continue

        text = format_change(line)

        text = remove_weapon(text)

        if not text:
            continue

        # Supprimer les flèches isolées
        if re.fullmatch(
            r"[\d\s\-\>\<\.m⇧⇩↑↓]+",
            text
        ):
            continue

        # Ne pas garder les descriptions
        if is_description(text):
            continue

        entry = (
            f"{current_weapon}|||{text}"
        )

        if category == "buff":
            buffs.append(entry)

        else:
            nerfs.append(entry)

    buffs = remove_duplicates(buffs)
    nerfs = remove_duplicates(nerfs)

    return buffs, nerfs


# =========================================================
# REGROUPER PAR ARME
# =========================================================

def group(items):

    result = {}

    for item in items:

        weapon, change = item.split(
            "|||",
            1
        )

        if weapon not in result:

            result[weapon] = []

        # -------------------------------------------------
        # Si la ligne est un résumé d'accessoire ET
        # qu'une version détaillée existe, on garde
        # les détails.
        # -------------------------------------------------

        if change not in result[weapon]:

            result[weapon].append(
                change
            )

    return result


# =========================================================
# NETTOYAGE DES DOUBLONS ACCESSOIRES
# =========================================================

def clean_groups(groups):

    final = {}

    for weapon, changes in groups.items():

        cleaned = []

        for change in changes:

            # ignorer valeurs isolées
            if re.fullmatch(
                r"[\d\s\-\>\<\.m⇧⇩↑↓]+",
                change
            ):
                continue

            # ignorer doublons exacts
            if change in cleaned:
                continue

            cleaned.append(change)

        if cleaned:

            final[weapon] = cleaned

    return final


# =========================================================
# MESSAGE DISCORD
# =========================================================

def build_message(
    buffs,
    nerfs
):

    buff_groups = clean_groups(
        group(buffs)
    )

    nerf_groups = clean_groups(
        group(nerfs)
    )

    message = (
        "🇫🇷 **CALL OF DUTY — WARZONE**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    # BUFFS

    if buff_groups:

        message += (
            "🟢 **BUFFS**\n\n"
        )

        for weapon, changes in buff_groups.items():

            message += (
                f"🔫 **{weapon}**\n"
            )

            for change in changes:

                message += (
                    f"• {change}\n"
                )

            message += "\n"

    # NERFS

    if nerf_groups:

        message += (
            "🔴 **NERFS**\n\n"
        )

        for weapon, changes in nerf_groups.items():

            message += (
                f"🔫 **{weapon}**\n"
            )

            for change in changes:

                message += (
                    f"• {change}\n"
                )

            message += "\n"

    message += (
        "📅 **Saison 05 Reloaded**\n\n"
        "🔗 **Notes officielles :**\n"
        f"{PATCH_URL}"
    )

    return message


# =========================================================
# DISCORD
# =========================================================

def send_discord(message):

    if not WEBHOOK_URL:

        raise RuntimeError(
            "DISCORD_WEBHOOK est introuvable."
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


def save_patch():

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
        "🔎 Recherche du patch..."
    )

    html = get_page()

    print(
        "✅ Page récupérée"
    )

    lines = extract_lines(
        html
    )

    print(
        f"📄 {len(lines)} lignes trouvées"
    )

    lines = get_weapon_section(
        lines
    )

    buffs, nerfs = extract_changes(
        lines
    )

    print(
        f"🟢 Buffs : {len(buffs)}"
    )

    print(
        f"🔴 Nerfs : {len(nerfs)}"
    )

    if get_last_patch() == PATCH_URL:

        print(
            "ℹ️ Patch déjà envoyé."
        )

        return

    message = build_message(
        buffs,
        nerfs
    )

    print(
        "\n========== MESSAGE ==========\n"
    )

    print(message)

    print(
        "\n==============================\n"
    )

    send_discord(
        message
    )

    save_patch()

    print(
        "✅ Message envoyé sur Discord."
    )


# =========================================================
# LANCEMENT
# =========================================================

if __name__ == "__main__":

    main()
