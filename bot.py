import os
import re
import requests
from bs4 import BeautifulSoup

# ============================================================
# CONFIGURATION
# ============================================================

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

PATCH_URL = "https://www.callofduty.com/patchnotes/2026/08/call-of-duty-bo7-warzone-season-05-reloaded-patch-notes"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
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
    "gunkick": "Recul de visée",
    "Viewkick": "Recul de caméra",
    "viewkick": "Recul de caméra",

    "ADS Speed": "Vitesse ADS",
    "Aim Down Sight Speed": "Vitesse ADS",

    "Damage Range": "Portée des dégâts",
    "damage range": "Portée des dégâts",

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
        "damage": "dégâts",
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

    # Pourcentages
    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*%\s*(?:à|to)\s*(\d+(?:\.\d+)?)\s*%",
        r"\1 % → \2 %",
        text,
        flags=re.I
    )

    # m/s
    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*m/s\s*(?:à|to)\s*(\d+(?:\.\d+)?)\s*m/s",
        r"\1 m/s → \2 m/s",
        text,
        flags=re.I
    )

    # mètres
    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*m\s*(?:à|to)\s*(\d+(?:\.\d+)?)\s*m",
        r"\1 m → \2 m",
        text,
        flags=re.I
    )

    # multiplicateurs
    text = re.sub(
        r"(\d+(?:\.\d+)?)x\s*(?:à|to)\s*(\d+(?:\.\d+)?)x",
        r"\1× → \2×",
        text,
        flags=re.I
    )

    # nombres simples
    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*(?:à|to)\s*(\d+(?:\.\d+)?)",
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

        "ADS Dégâts Dégâts maximum":
            "Dégâts maximum en ADS",

        "ADS Dégâts":
            "Dégâts en ADS",

        "Mid 1 Dégâts":
            "Dégâts intermédiaires",

        "Max Portée des dégâts":
            "Portée maximale des dégâts",

        "Mid 1 Portée des dégâts":
            "Portée intermédiaire des dégâts",

        "Headshot multiplier":
            "Multiplicateur de dégâts à la tête",

        "Tir à la tête multiplier":
            "Multiplicateur de dégâts à la tête",

        "headshot et upper torse dégâts":
            "dégâts aux tirs à la tête et au haut du torse",

        "headshot et haut du torse dégâts":
            "dégâts aux tirs à la tête et au haut du torse",

        "damage":
            "dégâts"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# DÉTECTION DE L'ARME
# ============================================================

def detect_weapon(text):

    upper = text.upper()

    for weapon in sorted(WEAPONS, key=len, reverse=True):

        if weapon.upper() in upper:
            return weapon

    return None


# ============================================================
# TEXTE À IGNORER
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

    return any(word in lower for word in ignored)


def is_table_value(text):

    text = text.strip()

    if not any(x in text for x in ["⇧", "⇩", "↑", "↓"]):
        return False

    cleaned = re.sub(r"[⇧⇩↑↓]", "", text).strip()

    return bool(
        re.fullmatch(
            r"[\d\s\-\>\<\.m]+",
            cleaned,
            re.I
        )
    )


# ============================================================
# CLASSIFICATION BUFF / NERF
# ============================================================

def classify(text):

    lower = text.lower()

    # --------------------------------------------------------
    # RÈGLE PRIORITAIRE : MALUS
    # --------------------------------------------------------

    # Un malus qui diminue = BUFF
    if "malus" in lower or "penalty" in lower:

        if any(word in lower for word in [
            "malus diminué",
            "malus réduit",
            "malus decrease",
            "malus decreased",
            "malus reduced",
            "penalty diminué",
            "penalty réduit",
            "penalty decreased",
            "penalty reduced"
        ]):
            return "buff"

        # Un malus qui augmente = NERF
        if any(word in lower for word in [
            "malus augmenté",
            "malus augmente",
            "penalty augmenté",
            "penalty increased"
        ]):
            return "nerf"

    # --------------------------------------------------------
    # BONUS
    # --------------------------------------------------------

    if any(word in lower for word in [
        "bonus amélioré",
        "bonus augmenté",
        "benefit amélioré",
        "benefit augmenté"
    ]):
        return "buff"

    if any(word in lower for word in [
        "bonus réduit",
        "bonus diminué",
        "benefit réduit",
        "benefit diminué"
    ]):
        return "nerf"

    # --------------------------------------------------------
    # RECUL
    # --------------------------------------------------------

    if any(word in lower for word in [
        "recul",
        "recoil",
        "gunkick",
        "viewkick"
    ]):

        if any(word in lower for word in [
            "réduit",
            "réduite",
            "réduits",
            "réduites",
            "diminué",
            "diminuée",
            "diminués",
            "diminuées",
            "reduced",
            "decreased"
        ]):
            return "buff"

        if any(word in lower for word in [
            "augmenté",
            "augmentée",
            "augmentés",
            "augmentées",
            "increased"
        ]):
            return "nerf"

    # --------------------------------------------------------
    # VITESSE DES PROJECTILES
    # --------------------------------------------------------

    if any(word in lower for word in [
        "vitesse des projectiles",
        "bullet velocity"
    ]):

        if any(word in lower for word in [
            "augmenté",
            "augmentée",
            "augmentés",
            "augmentées",
            "amélioré",
            "améliorée",
            "increased",
            "improved"
        ]):
            return "buff"

        if any(word in lower for word in [
            "diminué",
            "diminuée",
            "diminués",
            "diminuées",
            "réduit",
            "réduite",
            "réduits",
            "réduites",
            "decreased",
            "reduced"
        ]):
            return "nerf"

    # --------------------------------------------------------
    # DÉGÂTS
    # --------------------------------------------------------

    if any(word in lower for word in [
        "dégâts",
        "damage",
        "multiplicateur"
    ]):

        if any(word in lower for word in [
            "augmenté",
            "augmentée",
            "augmentés",
            "augmentées",
            "amélioré",
            "améliorée",
            "increased",
            "improved"
        ]):
            return "buff"

        if any(word in lower for word in [
            "diminué",
            "diminuée",
            "diminués",
            "diminuées",
            "réduit",
            "réduite",
            "réduits",
            "réduites",
            "decreased",
            "reduced"
        ]):
            return "nerf"

    # --------------------------------------------------------
    # PORTÉE
    # --------------------------------------------------------

    if any(word in lower for word in [
        "portée des dégâts",
        "damage range"
    ]):

        if any(word in lower for word in [
            "augmenté",
            "augmentée",
            "augmentés",
            "augmentées",
            "amélioré",
            "améliorée",
            "increased",
            "improved"
        ]):
            return "buff"

        if any(word in lower for word in [
            "diminué",
            "diminuée",
            "diminués",
            "diminuées",
            "réduit",
            "réduite",
            "réduits",
            "réduites",
            "decreased",
            "reduced"
        ]):
            return "nerf"

    return None


# ============================================================
# EXTRACTION DE LA PAGE
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
            ["h1", "h2", "h3", "h4", "p", "li", "td", "th"]
        )
    else:
        elements = soup.find_all(
            ["h1", "h2", "h3", "h4", "p", "li", "td", "th"]
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

        # Retire le nom de l'arme du début
        for weapon_name in WEAPONS:

            if text.upper().startswith(
                weapon_name.upper()
            ):

                text = text[len(weapon_name):].strip()

                break

        if not text:
            continue

        if category == "buff":
            buffs.append((current_weapon, text))

        elif category == "nerf":
            nerfs.append((current_weapon, text))

    return buffs, nerfs


# ============================================================
# NORMALISATION
# ============================================================

def normalize(text):

    text = text.lower()

    # IMPORTANT :
    # "réduit" et "diminué" doivent être identiques
    text = text.replace("réduit", "diminué")
    text = text.replace("réduite", "diminuée")
    text = text.replace("réduits", "diminués")
    text = text.replace("réduites", "diminuées")

    text = text.replace("reduced", "diminué")
    text = text.replace("decreased", "diminué")

    # Uniformisation
    text = text.replace(" ", "")
    text = text.replace("→", "")
    text = text.replace("de", "")
    text = text.replace("à", "")
    text = text.replace("from", "")
    text = text.replace("to", "")

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
            (weapon, change)
        )

    return result


# ============================================================
# SUPPRESSION BUFF / NERF EN DOUBLE
# ============================================================

def remove_cross_duplicates(
    buffs,
    nerfs
):

    buffs = remove_duplicates(buffs)
    nerfs = remove_duplicates(nerfs)

    buff_keys = {
        (
            weapon.lower(),
            normalize(change)
        )
        for weapon, change in buffs
    }

    final_nerfs = []

    for weapon, change in nerfs:

        key = (
            weapon.lower(),
            normalize(change)
        )

        if key in buff_keys:
            continue

        final_nerfs.append(
            (weapon, change)
        )

    return buffs, final_nerfs


# ============================================================
# SUPPRESSION DES LIGNES REDONDANTES
# ============================================================

def remove_redundant(items):

    items = remove_duplicates(items)

    result = []

    for weapon, change in items:

        current = normalize(change)

        duplicate = False

        for old_weapon, old_change in result:

            if weapon != old_weapon:
                continue

            old = normalize(old_change)

            if current == old:
                duplicate = True
                break

        if not duplicate:
            result.append(
                (weapon, change)
            )

    return result


# ============================================================
# SÉPARATION DES MODIFICATIONS
# ============================================================

def split_multiple_changes(text):

    # On ajoute une séparation avant les nouveaux
    # paramètres lorsqu'ils sont collés ensemble.

    keywords = [
        " Vitesse des projectiles ",
        " Portée intermédiaire des dégâts ",
        " Portée maximale des dégâts ",
        " Portée des dégâts ",
        " Recul vertical ",
        " Recul horizontal ",
        " Contrôle du recul ",
        " Recul de visée ",
        " Recul de caméra ",
        " Dégâts maximum ",
        " Dégâts intermédiaires ",
        " Multiplicateur de dégâts "
    ]

    parts = [text]

    for keyword in keywords:

        new_parts = []

        for part in parts:

            split = part.split(keyword)

            if len(split) == 1:
                new_parts.append(part)
                continue

            first = split[0].strip()

            if first:
                new_parts.append(first)

            for extra in split[1:]:

                extra = (
                    keyword.strip()
                    + " "
                    + extra.strip()
                )

                new_parts.append(
                    extra.strip()
                )

        parts = new_parts

    return [
        x.strip()
        for x in parts
        if x.strip()
    ]


# ============================================================
# REGROUPEMENT PAR ARME
# ============================================================

def group(items):

    result = {}

    for weapon, change in items:

        if weapon not in result:
            result[weapon] = []

        parts = split_multiple_changes(
            change
        )

        for part in parts:

            if part not in result[weapon]:
                result[weapon].append(part)

    return result


# ============================================================
# CONSTRUCTION DU MESSAGE DISCORD
# ============================================================

def build_message(
    buffs,
    nerfs
):

    buffs = remove_redundant(buffs)
    nerfs = remove_redundant(nerfs)

    # Une même modification ne peut pas être
    # simultanément BUFF et NERF.
    buffs, nerfs = remove_cross_duplicates(
        buffs,
        nerfs
    )

    buff_groups = group(buffs)
    nerf_groups = group(nerfs)

    message = (
        "🇫🇷 **CALL OF DUTY — WARZONE**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    # ========================================================
    # BUFFS
    # ========================================================

    if buff_groups:

        message += "🟢 **BUFFS**\n\n"

        for weapon, changes in buff_groups.items():

            message += f"**{weapon}**\n"

            for change in changes:
                message += f"• {change}\n"

            message += "\n"

    # ========================================================
    # NERFS
    # ========================================================

    if nerf_groups:

        message += "🔴 **NERFS**\n\n"

        for weapon, changes in nerf_groups.items():

            message += f"**{weapon}**\n"

            for change in changes:
                message += f"• {change}\n"

            message += "\n"

    # ========================================================
    # FOOTER
    # ========================================================

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


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():

    print("🔎 Recherche du patch Call of Duty...")

    response = requests.get(
        PATCH_URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    print("✅ Page récupérée.")

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

    print(message)

    print(
        "\n=============================\n"
    )

    send_discord(message)

    print(
        "✅ Patch envoyé sur Discord !"
    )


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":
    main()
