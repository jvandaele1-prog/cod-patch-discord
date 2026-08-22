import os
import re
import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURATION
# ============================================================

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

PATCH_URL = (
    "https://www.callofduty.com/patchnotes/2026/08/"
    "call-of-duty-bo7-warzone-season-05-reloaded-patch-notes"
)

STATE_FILE = "last_patch.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ============================================================
# ARMES RECONNUES
# ============================================================

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


# ============================================================
# TRADUCTIONS
# ============================================================

TRANSLATIONS = {

    "Bullet Velocity": "Vitesse des projectiles",
    "bullet velocity": "Vitesse des projectiles",

    "Vertical Recoil": "Recul vertical",
    "Horizontal Recoil": "Recul horizontal",
    "Recoil Control": "Contrôle du recul",
    "Recoil": "Recul",

    "Gunkick": "Recul de visée",
    "Gunkick and Viewkick": "Recul de visée et de caméra",
    "Viewkick": "Recul de caméra",

    "ADS Speed": "Vitesse ADS",
    "Aim Down Sight Speed": "Vitesse ADS",

    "Damage Range": "Portée des dégâts",
    "Max Damage": "Dégâts maximum",
    "Minimum Damage": "Dégâts minimum",
    "Damage": "Dégâts",

    "Headshot Multiplier": "Multiplicateur de dégâts à la tête",
    "Headshot multiplier": "Multiplicateur de dégâts à la tête",
    "Headshot": "Tir à la tête",
    "headshot": "Tir à la tête",

    "Upper Torso": "Haut du torse",
    "upper torso": "haut du torse",
    "Upper Body": "Haut du corps",
    "upper body": "haut du corps",

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

    "Now improves": "Améliore désormais",
    "now improves": "améliore désormais",

    "from": "de",
    "From": "de",

    "to": "à",
    "To": "à",

    "and": "et",
    "And": "et",

    "by": "de",

    "meters": "m",
    "meter": "m"
}


# ============================================================
# TÉLÉCHARGEMENT DE LA PAGE
# ============================================================

def get_page():

    response = requests.get(
        PATCH_URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.text


# ============================================================
# NETTOYAGE DU TEXTE
# ============================================================

def clean(text):

    replacements = {
        "àrse": "torse",
        "àrso": "torse",
        "Compensaàr": "Compensator",
        "Promonàry": "Promontory",
        "amélioré": "amélioré",
        "Améliore": "Améliore",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# TRADUCTION
# ============================================================

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


# ============================================================
# DÉTECTION DE L'ARME
# ============================================================

def detect_weapon(text, current_weapon):

    upper = text.upper()

    for weapon in WEAPONS:

        if weapon in upper:
            return weapon

    return current_weapon


# ============================================================
# IGNORER LES DESCRIPTIONS D'ARMES
# ============================================================

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


# ============================================================
# IGNORER LES VALEURS DE TABLEAUX
# ============================================================

def is_table_value(text):

    text = text.strip()

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

    pattern = r"^[\d\s\-\>\<\.m]+$"

    return bool(
        re.fullmatch(
            pattern,
            cleaned,
            re.IGNORECASE
        )
    )


# ============================================================
# CLASSIFICATION BUFF / NERF
# ============================================================

def classify(text):

    lower = text.lower()

    # --------------------------------------------------------
    # MALUS DIMINUÉ = BUFF
    # --------------------------------------------------------

    if "malus" in lower:

        if any(x in lower for x in [
            "diminué",
            "réduit",
            "decreased",
            "reduced"
        ]):
            return "buff"

        if any(x in lower for x in [
            "augmenté",
            "increased"
        ]):
            return "nerf"

    # --------------------------------------------------------
    # BONUS AUGMENTÉ / AMÉLIORÉ = BUFF
    # --------------------------------------------------------

    if any(x in lower for x in [
        "bonus augmenté",
        "bonus amélioré",
        "benefit augmenté",
        "benefit amélioré"
    ]):
        return "buff"

    # --------------------------------------------------------
    # BONUS DIMINUÉ = NERF
    # --------------------------------------------------------

    if any(x in lower for x in [
        "bonus diminué",
        "bonus réduit",
        "benefit reduced",
        "benefit decreased"
    ]):
        return "nerf"

    # --------------------------------------------------------
    # RECUL
    # --------------------------------------------------------

    if any(x in lower for x in [
        "recoil",
        "recul",
        "gunkick",
        "viewkick"
    ]):

        if any(x in lower for x in [
            "reduced",
            "réduit",
            "diminué"
        ]):
            return "buff"

        if any(x in lower for x in [
            "increased",
            "augmenté"
        ]):
            return "nerf"

    # --------------------------------------------------------
    # DÉGÂTS
    # --------------------------------------------------------

    if any(x in lower for x in [
        "damage",
        "dégâts",
        "multiplicateur"
    ]):

        if any(x in lower for x in [
            "increased",
            "improved",
            "augmenté",
            "amélioré"
        ]):
            return "buff"

        if any(x in lower for x in [
            "reduced",
            "decreased",
            "réduit",
            "diminué"
        ]):
            return "nerf"

    # --------------------------------------------------------
    # VITESSE DES PROJECTILES
    # --------------------------------------------------------

    if any(x in lower for x in [
        "bullet velocity",
        "vitesse des projectiles"
    ]):

        if any(x in lower for x in [
            "increased",
            "improved",
            "augmenté",
            "amélioré"
        ]):
            return "buff"

        if any(x in lower for x in [
            "reduced",
            "decreased",
            "réduit",
            "diminué"
        ]):
            return "nerf"

    # --------------------------------------------------------
    # PORTÉE DES DÉGÂTS
    # --------------------------------------------------------

    if any(x in lower for x in [
        "damage range",
        "portée des dégâts"
    ]):

        if any(x in lower for x in [
            "increased",
            "improved",
            "augmenté",
            "amélioré"
        ]):
            return "buff"

        if any(x in lower for x in [
            "reduced",
            "decreased",
            "réduit",
            "diminué"
        ]):
            return "nerf"

    # --------------------------------------------------------
    # ADS
    # --------------------------------------------------------

    if "ads" in lower:

        if any(x in lower for x in [
            "reduced",
            "diminué",
            "réduit"
        ]):
            return "buff"

        if any(x in lower for x in [
            "increased",
            "augmenté"
        ]):
            return "nerf"

    return None


# ============================================================
# FORMATAGE DES NOMBRES
# ============================================================

def format_numbers(text):

    # from 910m/s to 920m/s
    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*(m/s|%)\s+"
        r"(?:to|à)\s+"
        r"(\d+(?:\.\d+)?)\s*(m/s|%)",
        r"\1 \2 → \3 \4",
        text,
        flags=re.IGNORECASE
    )

    # de 910 m/s à 920 m/s
    text = re.sub(
        r"de\s+"
        r"(\d+(?:\.\d+)?)\s*(m/s|%)\s+"
        r"à\s+"
        r"(\d+(?:\.\d+)?)\s*(m/s|%)",
        r"\1 \2 → \3 \4",
        text,
        flags=re.IGNORECASE
    )

    # from 2m to 2.5m
    text = re.sub(
        r"(?:from|de)\s+"
        r"(\d+(?:\.\d+)?)\s*m\s+"
        r"(?:to|à)\s+"
        r"(\d+(?:\.\d+)?)\s*m",
        r"\1 m → \2 m",
        text,
        flags=re.IGNORECASE
    )

    # from 1.1x to 1.2x
    text = re.sub(
        r"(?:from|de)\s+"
        r"(\d+(?:\.\d+)?)x\s+"
        r"(?:to|à)\s+"
        r"(\d+(?:\.\d+)?)x",
        r"\1× → \2×",
        text,
        flags=re.IGNORECASE
    )

    # from 32 to 34
    text = re.sub(
        r"(?:from|de)\s+"
        r"(\d+(?:\.\d+)?)\s+"
        r"(?:to|à)\s+"
        r"(\d+(?:\.\d+)?)",
        r"\1 → \2",
        text,
        flags=re.IGNORECASE
    )

    return text


# ============================================================
# FORMATAGE FINAL
# ============================================================

def format_change(text):

    text = translate(text)

    text = format_numbers(text)

    # Correction de formulations
    replacements = {

        "Tir à la tête multiplier": (
            "Multiplicateur de dégâts à la tête"
        ),

        "Tir à la tête Multiplicateur": (
            "Multiplicateur de dégâts à la tête"
        ),

        "Tir à la tête damage": (
            "Dégâts aux tirs à la tête"
        ),

        "haut du torse damage": (
            "dégâts au haut du torse"
        ),

        "ADS Dégâts Dégâts maximum": (
            "Dégâts maximum en ADS"
        ),

        "Mid 1 Dégâts": (
            "Dégâts intermédiaires"
        ),

        "Max Portée des dégâts": (
            "Portée maximale des dégâts"
        ),

        "Mid 1 Portée des dégâts": (
            "Portée intermédiaire des dégâts"
        ),

        "bonus augmenté": (
            "bonus augmenté"
        ),

        "bonus amélioré": (
            "bonus amélioré"
        ),

        "malus diminué": (
            "malus diminué"
        ),

        "malus réduit": (
            "malus réduit"
        ),

        "Augmenté by": (
            "Augmenté de"
        ),

        "augmenté by": (
            "augmenté de"
        ),

        "from ": (
            "de "
        ),

        " to ": (
            " → "
        )
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Nettoyage des doubles espaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    # Nettoyage des espaces avant %
    text = re.sub(
        r"\s+%",
        " %",
        text
    )

    return text.strip()


# ============================================================
# RETIRER LE NOM DE L'ARME
# ============================================================

def remove_weapon(text):

    for weapon in WEAPONS:

        if text.upper().startswith(
            weapon.upper()
        ):

            return text[
                len(weapon):
            ].strip()

    return text


# ============================================================
# EXTRACTION HTML
# ============================================================

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


# ============================================================
# EXTRACTION DE LA SECTION ARMES
# ============================================================

def get_weapon_section(lines):

    start = None

    for i, line in enumerate(lines):

        if line.strip().upper() == "WEAPONS":

            start = i
            break

    if start is None:
        return lines

    result = []

    stop_words = [
        "BUG FIXES",
        "GAMEPLAY",
        "KILLSTREAKS",
        "EQUIPMENT",
        "PERKS",
        "OPERATORS"
    ]

    for line in lines[start:]:

        if line.upper() in stop_words:
            break

        result.append(line)

    return result


# ============================================================
# SUPPRESSION DES DOUBLONS
# ============================================================

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


# ============================================================
# SUPPRESSION DES LIGNES REDONDANTES
# ============================================================

def remove_redundant_details(items):

    result = []

    for item in items:

        weapon, change = item.split(
            "|||",
            1
        )

        duplicate = False

        for existing in result:

            existing_weapon, existing_change = existing.split(
                "|||",
                1
            )

            if existing_weapon != weapon:
                continue

            # Même modification déjà présente
            if change.lower() == existing_change.lower():
                duplicate = True
                break

            # Si la nouvelle ligne est un résumé
            # de la ligne précédente
            if existing_change.lower() in change.lower():
                duplicate = True
                break

        if not duplicate:
            result.append(item)

    return result


# ============================================================
# EXTRACTION DES BUFFS / NERFS
# ============================================================

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

        # Ignore les tableaux de dégâts
        if is_table_value(line):
            continue

        category = classify(line)

        if category is None:
            continue

        text = format_change(line)

        text = remove_weapon(text)

        if not text:
            continue

        # Ignorer les lignes qui ne sont que des chiffres
        if re.fullmatch(
            r"[\d\s\-\>\<\.m⇧⇩↑↓]+",
            text
        ):
            continue

        if category == "buff":

            buffs.append(
                f"{current_weapon}|||{text}"
            )

        elif category == "nerf":

            nerfs.append(
                f"{current_weapon}|||{text}"
            )

    buffs = remove_duplicates(buffs)
    nerfs = remove_duplicates(nerfs)

    buffs = remove_redundant_details(buffs)
    nerfs = remove_redundant_details(nerfs)

    return buffs, nerfs


# ============================================================
# REGROUPEMENT PAR ARME
# ============================================================

def group(items):

    result = {}

    for item in items:

        weapon, change = item.split(
            "|||",
            1
        )

        if weapon not in result:
            result[weapon] = []

        if change not in result[weapon]:
            result[weapon].append(change)

    return result


# ============================================================
# NETTOYAGE FINAL DES GROUPES
# ============================================================

def clean_groups(groups):

    final = {}

    for weapon, changes in groups.items():

        cleaned = []

        for change in changes:

            if not change:
                continue

            if re.fullmatch(
                r"[\d\s\-\>\<\.m⇧⇩↑↓]+",
                change
            ):
                continue

            if change in cleaned:
                continue

            cleaned.append(change)

        if cleaned:
            final[weapon] = cleaned

    return final


# ============================================================
# CONSTRUCTION DU MESSAGE DISCORD
# ============================================================

def build_message(buffs, nerfs):

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

    # --------------------------------------------------------
    # BUFFS
    # --------------------------------------------------------

    if buff_groups:

        message += "🟢 **BUFFS**\n\n"

        for weapon, changes in buff_groups.items():

            message += (
                f"🔫 **{weapon}**\n"
            )

            for change in changes:

                message += (
                    f"• {change}\n"
                )

            message += "\n"

    # --------------------------------------------------------
    # NERFS
    # --------------------------------------------------------

    if nerf_groups:

        message += "🔴 **NERFS**\n\n"

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


# ============================================================
# ENVOI DISCORD
# ============================================================

def send_discord(message):

    if not WEBHOOK_URL:

        raise RuntimeError(
            "La variable DISCORD_WEBHOOK est introuvable."
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


# ============================================================
# MÉMOIRE DU PATCH
# ============================================================

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


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():

    print(
        "🔎 Recherche du patch Call of Duty..."
    )

    html = get_page()

    print(
        "✅ Page récupérée."
    )

    lines = extract_lines(
        html
    )

    print(
        f"📄 {len(lines)} lignes trouvées."
    )

    lines = get_weapon_section(
        lines
    )

    buffs, nerfs = extract_changes(
        lines
    )

    print(
        f"🟢 Buffs détectés : {len(buffs)}"
    )

    print(
        f"🔴 Nerfs détectés : {len(nerfs)}"
    )

    # --------------------------------------------------------
    # ÉVITER LES DOUBLONS
    # --------------------------------------------------------

    if get_last_patch() == PATCH_URL:

        print(
            "ℹ️ Ce patch a déjà été envoyé."
        )

        return

    # --------------------------------------------------------
    # CONSTRUCTION
    # --------------------------------------------------------

    message = build_message(
        buffs,
        nerfs
    )

    print(
        "\n"
        "================ MESSAGE ================\n"
    )

    print(message)

    print(
        "\n"
        "==========================================\n"
    )

    # --------------------------------------------------------
    # ENVOI
    # --------------------------------------------------------

    send_discord(
        message
    )

    save_patch()

    print(
        "✅ Patch envoyé sur Discord !"
    )


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":
    main()
