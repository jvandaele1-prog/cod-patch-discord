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
    "User-Agent": "Mozilla/5.0"
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

    "Headshot": "Tir à la tête",
    "headshot": "tir à la tête",

    "Upper Torso": "haut du torse",
    "Upper Body": "haut du corps",
    "upper torso": "haut du torse",
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
        text = text.replace(
            english,
            french
        )

    return clean(text)


# ============================================================
# FORMATAGE DES VALEURS
# ============================================================

def format_numbers(text):

    # m/s
    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*(m/s|%)\s*"
        r"(?:to|à)\s*"
        r"(\d+(?:\.\d+)?)\s*(m/s|%)",
        r"\1 \2 → \3 \4",
        text,
        flags=re.I
    )

    # de X à Y
    text = re.sub(
        r"de\s+"
        r"(\d+(?:\.\d+)?)\s*(m/s|%)\s+"
        r"à\s+"
        r"(\d+(?:\.\d+)?)\s*(m/s|%)",
        r"\1 \2 → \3 \4",
        text,
        flags=re.I
    )

    # mètres
    text = re.sub(
        r"(?:from|de)\s+"
        r"(\d+(?:\.\d+)?)\s*m\s+"
        r"(?:to|à)\s+"
        r"(\d+(?:\.\d+)?)\s*m",
        r"\1 m → \2 m",
        text,
        flags=re.I
    )

    # multiplicateurs
    text = re.sub(
        r"(?:from|de)\s+"
        r"(\d+(?:\.\d+)?)x\s+"
        r"(?:to|à)\s+"
        r"(\d+(?:\.\d+)?)x",
        r"\1× → \2×",
        text,
        flags=re.I
    )

    # nombres simples
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
# FORMATAGE FINAL
# ============================================================

def format_change(text):

    text = translate(text)
    text = format_numbers(text)

    replacements = {

        "Tir à la tête multiplier":
            "Multiplicateur de dégâts à la tête",

        "Tir à la tête Multiplicateur":
            "Multiplicateur de dégâts à la tête",

        "ADS Dégâts Dégâts maximum":
            "Dégâts maximum en ADS",

        "Mid 1 Dégâts":
            "Dégâts intermédiaires",

        "Max Portée des dégâts":
            "Portée maximale des dégâts",

        "Mid 1 Portée des dégâts":
            "Portée intermédiaire des dégâts",

        "headshot et upper torse dégâts":
            "dégâts aux tirs à la tête et au haut du torse",

        "headshot et haut du torse dégâts":
            "dégâts aux tirs à la tête et au haut du torse",

        "damage":
            "dégâts"
    }

    for old, new in replacements.items():
        text = text.replace(
            old,
            new
        )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# DÉTECTION DE L'ARME
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
# DESCRIPTIONS À IGNORER
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
# VALEURS DE TABLEAUX À IGNORER
# ============================================================

def is_table_value(text):

    text = text.strip()

    if not any(
        x in text
        for x in [
            "⇧",
            "⇩",
            "↑",
            "↓"
        ]
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
# ============================================================

def classify(text):

    lower = text.lower()

    # --------------------------------------------------------
    # MALUS
    # --------------------------------------------------------

    if "malus" in lower:

        # Diminution du malus = BUFF
        if any(x in lower for x in [
            "diminué",
            "réduit",
            "decreased",
            "reduced"
        ]):
            return "buff"

        # Augmentation du malus = NERF
        if any(x in lower for x in [
            "augmenté",
            "increased"
        ]):
            return "nerf"

    # --------------------------------------------------------
    # BONUS
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
    # RECUL
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
    # DÉGÂTS
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
    # VITESSE PROJECTILES
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
    # PORTÉE
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


# ============================================================
# EXTRACTION
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

        # Retirer le nom de l'arme
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
# NORMALISATION POUR COMPARAISON
# ============================================================

def normalize(text):

    text = text.lower()

    text = text.replace(
        " ",
        ""
    )

    text = text.replace(
        "→",
        "to"
    )

    text = text.replace(
        "de",
        ""
    )

    text = text.replace(
        "à",
        ""
    )

    return text


# ============================================================
# SUPPRESSION DES DOUBLONS
# ============================================================

def remove_duplicates(items):

    result = []
    seen = set()

    for weapon, change in items:

        key = (
            weapon.lower(),
            normalize(change)
        )

        if key in seen:
            continue

        seen.add(key)

        result.append(
            (
                weapon,
                change
            )
        )

    return result


# ============================================================
# RÈGLE IMPORTANTE :
#
# UNE MODIFICATION IDENTIQUE NE PEUT PAS ÊTRE
# À LA FOIS BUFF ET NERF.
#
# PRIORITÉ AU BUFF.
# ============================================================

def remove_cross_duplicates(
    buffs,
    nerfs
):

    buffs = remove_duplicates(
        buffs
    )

    nerfs = remove_duplicates(
        nerfs
    )

    buff_keys = set()

    for weapon, change in buffs:

        buff_keys.add(
            (
                weapon.lower(),
                normalize(change)
            )
        )

    clean_nerfs = []

    for weapon, change in nerfs:

        key = (
            weapon.lower(),
            normalize(change)
        )

        if key in buff_keys:
            continue

        clean_nerfs.append(
            (
                weapon,
                change
            )
        )

    return buffs, clean_nerfs


# ============================================================
# SUPPRESSION DES LIGNES REDONDANTES
# ============================================================

def remove_redundant(items):

    items = remove_duplicates(
        items
    )

    result = []

    for weapon, change in items:

        duplicate = False

        for old_weapon, old_change in result:

            if weapon != old_weapon:
                continue

            a = normalize(
                change
            )

            b = normalize(
                old_change
            )

            if a == b:
                duplicate = True
                break

            if len(a) < len(b) and a in b:
                duplicate = True
                break

        if not duplicate:

            result.append(
                (
                    weapon,
                    change
                )
            )

    return result


# ============================================================
# REGROUPEMENT PAR ARME
# ============================================================

def group(items):

    result = {}

    for weapon, change in items:

        if weapon not in result:
            result[weapon] = []

        if change not in result[weapon]:
            result[weapon].append(
                change
            )

    return result


# ============================================================
# MESSAGE DISCORD
# ============================================================

def build_message(
    buffs,
    nerfs
):

    # Nettoyage
    buffs = remove_redundant(
        buffs
    )

    nerfs = remove_redundant(
        nerfs
    )

    # Suppression des doublons entre
    # BUFF et NERF
    buffs, nerfs = remove_cross_duplicates(
        buffs,
        nerfs
    )

    buff_groups = group(
        buffs
    )

    nerf_groups = group(
        nerfs
    )

    message = (
        "🇫🇷 **CALL OF DUTY — WARZONE**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    # --------------------------------------------------------
    # BUFFS
    # --------------------------------------------------------

    if buff_groups:

        message += (
            "🟢 **BUFFS**\n\n"
        )

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

        message += (
            "🔴 **NERFS**\n\n"
        )

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


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():

    print(
        "🔎 Recherche du patch Call of Duty..."
    )

    response = requests.get(
        PATCH_URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    print(
        "✅ Page récupérée."
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
        f"🟢 Buffs détectés : {len(buffs)}"
    )

    print(
        f"🔴 Nerfs détectés : {len(nerfs)}"
    )

    message = build_message(
        buffs,
        nerfs
    )

    print(
        "\n========== MESSAGE ==========\n"
    )

    print(
        message
    )

    print(
        "\n=============================\n"
    )

    send_discord(
        message
    )

    print(
        "✅ Patch envoyé sur Discord !"
    )


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":
    main()
