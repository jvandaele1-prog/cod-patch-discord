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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


# ============================================================
# ARMES
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
    "Viewkick": "Recul de caméra",

    "ADS Speed": "Vitesse ADS",
    "Aim Down Sight Speed": "Vitesse ADS",

    "Damage Range": "Portée des dégâts",
    "Max Damage": "Dégâts maximum",
    "Minimum Damage": "Dégâts minimum",
    "Damage": "Dégâts",

    "Headshot Multiplier": "Multiplicateur de dégâts à la tête",
    "Headshot multiplier": "Multiplicateur de dégâts à la tête",

    "Upper Torso": "Haut du torse",
    "Upper Body": "Haut du corps",

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

    "by": "de"
}


# ============================================================
# NETTOYAGE
# ============================================================

def clean(text):

    replacements = {
        "àrse": "torse",
        "àrso": "torse",
        "Compensaàr": "Compensator",
        "Promonàry": "Promontory",
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
        text = text.replace(english, french)

    return clean(text)


# ============================================================
# FORMATAGE DES VALEURS
# ============================================================

def format_numbers(text):

    # 910m/s to 920m/s
    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*(m/s|%)\s*"
        r"(?:to|à)\s*"
        r"(\d+(?:\.\d+)?)\s*(m/s|%)",
        r"\1 \2 → \3 \4",
        text,
        flags=re.I
    )

    # de 910 m/s à 920 m/s
    text = re.sub(
        r"de\s+(\d+(?:\.\d+)?)\s*(m/s|%)\s+"
        r"à\s+(\d+(?:\.\d+)?)\s*(m/s|%)",
        r"\1 \2 → \3 \4",
        text,
        flags=re.I
    )

    # 2m to 2.5m
    text = re.sub(
        r"(?:from|de)\s+"
        r"(\d+(?:\.\d+)?)\s*m\s+"
        r"(?:to|à)\s+"
        r"(\d+(?:\.\d+)?)\s*m",
        r"\1 m → \2 m",
        text,
        flags=re.I
    )

    # 1.1x to 1.2x
    text = re.sub(
        r"(?:from|de)\s+"
        r"(\d+(?:\.\d+)?)x\s+"
        r"(?:to|à)\s+"
        r"(\d+(?:\.\d+)?)x",
        r"\1× → \2×",
        text,
        flags=re.I
    )

    # 32 to 34
    text = re.sub(
        r"(?:from|de)\s+"
        r"(\d+(?:\.\d+)?)\s+"
        r"(?:to|à)\s+"
        r"(\d+(?:\.\d+)?)",
        r"\1 → \2",
        text,
        flags=re.I
    )

    return text


# ============================================================
# FORMATAGE FINAL D'UNE MODIFICATION
# ============================================================

def format_change(text):

    text = translate(text)
    text = format_numbers(text)

    replacements = {

        "Tir à la tête multiplier":
            "Multiplicateur de dégâts à la tête",

        "Tir à la tête Multiplicateur":
            "Multiplicateur de dégâts à la tête",

        "headshot multiplier":
            "Multiplicateur de dégâts à la tête",

        "ADS Dégâts Dégâts maximum":
            "Dégâts maximum en ADS",

        "Mid 1 Dégâts":
            "Dégâts intermédiaires",

        "Max Portée des dégâts":
            "Portée maximale des dégâts",

        "Mid 1 Portée des dégâts":
            "Portée intermédiaire des dégâts",

        "damage":
            "dégâts",

        "from":
            "de",

        " to ":
            " → "
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# DÉTECTION ARME
# ============================================================

def detect_weapon(text):

    upper = text.upper()

    for weapon in sorted(
        WEAPONS,
        key=len,
        reverse=True
    ):
        if weapon in upper:
            return weapon

    return None


# ============================================================
# DESCRIPTION À IGNORER
# ============================================================

def is_description(text):

    lower = text.lower()

    ignored = [
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
        x in lower
        for x in ignored
    )


# ============================================================
# LIGNE DE TABLEAU À IGNORER
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
    ).strip()

    return bool(
        re.fullmatch(
            r"[\d\s\-\>\<\.m]+",
            cleaned,
            re.I
        )
    )


# ============================================================
# CLASSIFICATION
#
# IMPORTANT :
# Une modification ne peut être que BUFF OU NERF.
# ============================================================

def classify(text):

    lower = text.lower()

    # --------------------------------------------------------
    # 1. MALUS
    # --------------------------------------------------------

    if "malus" in lower:

        # Diminuer un malus = BUFF
        if any(x in lower for x in [
            "diminué",
            "réduit",
            "decreased",
            "reduced"
        ]):
            return "buff"

        # Augmenter un malus = NERF
        if any(x in lower for x in [
            "augmenté",
            "increased"
        ]):
            return "nerf"

    # --------------------------------------------------------
    # 2. BONUS
    # --------------------------------------------------------

    if any(x in lower for x in [
        "bonus augmenté",
        "bonus amélioré",
        "benefit augmenté",
        "benefit amélioré"
    ]):
        return "buff"

    if any(x in lower for x in [
        "bonus diminué",
        "bonus réduit",
        "benefit reduced",
        "benefit decreased"
    ]):
        return "nerf"

    # --------------------------------------------------------
    # 3. RECUL
    # --------------------------------------------------------

    if any(x in lower for x in [
        "recoil",
        "recul",
        "gunkick",
        "viewkick"
    ]):

        if any(x in lower for x in [
            "réduit",
            "diminué",
            "reduced",
            "decreased"
        ]):
            return "buff"

        if any(x in lower for x in [
            "augmenté",
            "increased"
        ]):
            return "nerf"

    # --------------------------------------------------------
    # 4. DÉGÂTS
    # --------------------------------------------------------

    if any(x in lower for x in [
        "damage",
        "dégâts",
        "multiplicateur"
    ]):

        if any(x in lower for x in [
            "augmenté",
            "amélioré",
            "increased",
            "improved"
        ]):
            return "buff"

        if any(x in lower for x in [
            "réduit",
            "diminué",
            "reduced",
            "decreased"
        ]):
            return "nerf"

    # --------------------------------------------------------
    # 5. VITESSE PROJECTILES
    # --------------------------------------------------------

    if any(x in lower for x in [
        "bullet velocity",
        "vitesse des projectiles"
    ]):

        if any(x in lower for x in [
            "augmenté",
            "amélioré",
            "increased",
            "improved"
        ]):
            return "buff"

        if any(x in lower for x in [
            "réduit",
            "diminué",
            "reduced",
            "decreased"
        ]):
            return "nerf"

    # --------------------------------------------------------
    # 6. PORTÉE
    # --------------------------------------------------------

    if any(x in lower for x in [
        "damage range",
        "portée des dégâts"
    ]):

        if any(x in lower for x in [
            "augmenté",
            "amélioré",
            "increased",
            "improved"
        ]):
            return "buff"

        if any(x in lower for x in [
            "réduit",
            "diminué",
            "reduced",
            "decreased"
        ]):
            return "nerf"

    # --------------------------------------------------------
    # 7. ADS
    # --------------------------------------------------------

    if "ads" in lower:

        if any(x in lower for x in [
            "réduit",
            "diminué",
            "reduced",
            "decreased"
        ]):
            return "buff"

        if any(x in lower for x in [
            "augmenté",
            "increased"
        ]):
            return "nerf"

    return None


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
# EXTRACTION DES MODIFICATIONS
# ============================================================

def extract_changes(lines):

    buffs = []
    nerfs = []

    current_weapon = None

    for line in lines:

        if not line:
            continue

        if is_description(line):
            continue

        if is_table_value(line):
            continue

        weapon = detect_weapon(line)

        if weapon:
            current_weapon = weapon

        if not current_weapon:
            continue

        category = classify(line)

        if category is None:
            continue

        text = format_change(line)

        # Retirer le nom de l'arme du texte
        for weapon_name in WEAPONS:

            if text.upper().startswith(
                weapon_name.upper()
            ):

                text = text[
                    len(weapon_name):
                ].strip()

                break

        if not text:
            continue

        # Ligne composée uniquement de chiffres
        if re.fullmatch(
            r"[\d\s\-\>\<\.m⇧⇩↑↓]+",
            text
        ):
            continue

        item = (
            current_weapon,
            text
        )

        if category == "buff":
            buffs.append(item)

        elif category == "nerf":
            nerfs.append(item)

    return buffs, nerfs


# ============================================================
# NETTOYAGE DES DOUBLONS
# ============================================================

def remove_duplicates(items):

    result = []
    seen = set()

    for weapon, change in items:

        key = (
            weapon.lower(),
            re.sub(
                r"\s+",
                " ",
                change.lower()
            ).strip()
        )

        if key in seen:
            continue

        seen.add(key)

        result.append(
            (weapon, change)
        )

    return result


# ============================================================
# SUPPRESSION DES DOUBLONS COURTS
# ============================================================

def remove_redundant(items):

    items = remove_duplicates(items)

    result = []

    for weapon, change in items:

        duplicate = False

        for existing_weapon, existing_change in result:

            if weapon != existing_weapon:
                continue

            a = change.lower().strip()
            b = existing_change.lower().strip()

            # Exactement la même chose
            if a == b:
                duplicate = True
                break

            # Une ligne courte est déjà contenue
            # dans une ligne complète
            if len(a) < len(b) and a in b:
                duplicate = True
                break

        if not duplicate:
            result.append(
                (weapon, change)
            )

    return result


# ============================================================
# REGROUPEMENT
# ============================================================

def group(items):

    result = {}

    for weapon, change in items:

        if weapon not in result:
            result[weapon] = []

        if change not in result[weapon]:
            result[weapon].append(change)

    return result


# ============================================================
# MESSAGE DISCORD
# ============================================================

def build_message(buffs, nerfs):

    buffs = remove_redundant(buffs)
    nerfs = remove_redundant(nerfs)

    buff_groups = group(buffs)
    nerf_groups = group(nerfs)

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
                f"**{weapon}**\n"
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
                f"**{weapon}**\n"
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
            "DISCORD_WEBHOOK n'est pas configuré."
        )

    # Discord limite les messages à 2000 caractères.
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
# PROGRAMME PRINCIPAL
# ============================================================

def main():

    print(
        "🔎 Recherche des notes de correctif..."
    )

    response = requests.get(
        PATCH_URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    print(
        "✅ Page Call of Duty récupérée."
    )

    lines = extract_lines(
        response.text
    )

    print(
        f"📄 {len(lines)} lignes analysées."
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

    message = build_message(
        buffs,
        nerfs
    )

    print(
        "\n========== MESSAGE ==========\n"
    )

    print(message)

    print(
        "\n=============================\n"
    )

    send_discord(
        message
    )

    print(
        "✅ Message envoyé sur Discord."
    )


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":
    main()
