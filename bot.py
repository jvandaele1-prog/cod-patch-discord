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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
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
# TÉLÉCHARGEMENT DE LA PAGE
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
# NETTOYAGE DU TEXTE
# =========================================================

def clean(text):

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# TRADUCTION DES TERMES
# =========================================================

def translate(text):

    replacements = {

        # Armes / dégâts
        "Damage Range": "Portée des dégâts",
        "Max Damage": "Dégâts maximum",
        "Minimum Damage": "Dégâts minimum",
        "Damage": "Dégâts",

        # Projectiles
        "Bullet Velocity": "Vitesse des projectiles",

        # Recul
        "Vertical Recoil": "Recul vertical",
        "Horizontal Recoil": "Recul horizontal",
        "Recoil Control": "Contrôle du recul",
        "Recoil": "Recul",

        # Visée
        "Gunkick": "Recul de visée",
        "Viewkick": "Recul de caméra",
        "ADS Speed": "Vitesse ADS",
        "ADS": "ADS",

        # Tir
        "Fire Rate": "Cadence de tir",
        "Rate of Fire": "Cadence de tir",
        "Headshot Multiplier": "Multiplicateur de tir à la tête",
        "Headshot": "Tir à la tête",

        # Mobilité
        "Movement Speed": "Vitesse de déplacement",
        "Sprint Speed": "Vitesse de sprint",

        # Chargeur
        "Magazine Size": "Taille du chargeur",
        "Reload Speed": "Vitesse de rechargement",

        # Bonus / malus
        "Benefit": "Bonus",
        "benefit": "bonus",
        "Penalty": "Malus",
        "penalty": "malus",

        # Anglais → français
        "Increased": "augmenté",
        "increased": "augmenté",

        "Reduced": "réduit",
        "reduced": "réduit",

        "Decreased": "diminué",
        "decreased": "diminué",

        "Improved": "amélioré",
        "improved": "amélioré",

        "Increase": "augmentation",
        "increase": "augmentation",

        "Decrease": "diminution",
        "decrease": "diminution",

        "Now improves": "Améliore désormais",
        "now improves": "améliore désormais",

        "to": "à",
        "from": "de",
        "by": "de",

        "and": "et",

        "seconds": "secondes",
        "second": "seconde",

        "meters": "mètres",
        "meter": "mètre",

        "upper torso": "haut du torse",
        "upper arm": "haut du bras",

        "damage": "dégâts"
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
# DÉTECTION DE L'ARME
# =========================================================

def detect_weapon(text, current_weapon):

    upper = text.upper()

    for weapon in WEAPONS:

        if weapon in upper:

            return weapon

    return current_weapon


# =========================================================
# DESCRIPTION D'ARME À IGNORER
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
# IGNORER LES VALEURS ISOLEES
#
# Exemples :
# 41⇧
# 0 - 45m⇧
# 37⇧
# 46⇩
# >45m⇩
# =========================================================

def is_isolated_table_value(text):

    value = text.strip()

    # Présence d'une flèche
    if not any(
        arrow in value
        for arrow in ["⇧", "⇩", "↑", "↓"]
    ):
        return False

    # Retirer les flèches
    value = re.sub(
        r"[⇧⇩↑↓]",
        "",
        value
    ).strip()

    # Si ce qui reste est uniquement une valeur
    # ou une plage de valeurs, on ignore.
    pattern = (
        r"^[\d\s\-\>\<\.]+"
        r"(?:m)?$"
    )

    return bool(
        re.fullmatch(
            pattern,
            value,
            flags=re.IGNORECASE
        )
    )


# =========================================================
# CLASSIFICATION BUFF / NERF
# =========================================================

def classify(text):

    lower = text.lower()

    # -----------------------------------------------------
    # MALUS
    # -----------------------------------------------------

    if (
        "penalty" in lower
        or "malus" in lower
    ):

        if any(
            word in lower
            for word in [
                "reduced",
                "decreased",
                "réduit",
                "diminué"
            ]
        ):
            return "buff"

        if any(
            word in lower
            for word in [
                "increased",
                "augmenté"
            ]
        ):
            return "nerf"

    # -----------------------------------------------------
    # BONUS
    # -----------------------------------------------------

    if (
        "benefit" in lower
        or "bonus" in lower
    ):

        if any(
            word in lower
            for word in [
                "increased",
                "improved",
                "augmenté",
                "amélioré"
            ]
        ):
            return "buff"

        if any(
            word in lower
            for word in [
                "reduced",
                "decreased",
                "réduit",
                "diminué"
            ]
        ):
            return "nerf"

    # -----------------------------------------------------
    # RECUL
    # -----------------------------------------------------

    if (
        "recoil" in lower
        or "gunkick" in lower
        or "viewkick" in lower
    ):

        if any(
            word in lower
            for word in [
                "reduced",
                "decreased",
                "réduit",
                "diminué"
            ]
        ):
            return "buff"

        if any(
            word in lower
            for word in [
                "increased",
                "augmenté"
            ]
        ):
            return "nerf"

    # -----------------------------------------------------
    # DÉGÂTS
    # -----------------------------------------------------

    if (
        "damage" in lower
        or "dégâts" in lower
    ):

        if any(
            word in lower
            for word in [
                "increased",
                "improved",
                "augmenté",
                "amélioré"
            ]
        ):
            return "buff"

        if any(
            word in lower
            for word in [
                "reduced",
                "decreased",
                "réduit",
                "diminué"
            ]
        ):
            return "nerf"

    # -----------------------------------------------------
    # PORTÉE
    # -----------------------------------------------------

    if (
        "range" in lower
        or "portée" in lower
    ):

        if any(
            word in lower
            for word in [
                "increased",
                "improved",
                "augmenté",
                "amélioré"
            ]
        ):
            return "buff"

        if any(
            word in lower
            for word in [
                "reduced",
                "decreased",
                "réduit",
                "diminué"
            ]
        ):
            return "nerf"

    # -----------------------------------------------------
    # VITESSE DES PROJECTILES
    # -----------------------------------------------------

    if (
        "bullet velocity" in lower
        or "vitesse des projectiles" in lower
    ):

        if any(
            word in lower
            for word in [
                "increased",
                "improved",
                "augmenté",
                "amélioré"
            ]
        ):
            return "buff"

        if any(
            word in lower
            for word in [
                "reduced",
                "decreased",
                "réduit",
                "diminué"
            ]
        ):
            return "nerf"

    # -----------------------------------------------------
    # CADENCE
    # -----------------------------------------------------

    if (
        "fire rate" in lower
        or "rate of fire" in lower
        or "cadence" in lower
    ):

        if any(
            word in lower
            for word in [
                "increased",
                "improved",
                "augmenté",
                "amélioré"
            ]
        ):
            return "buff"

        if any(
            word in lower
            for word in [
                "reduced",
                "decreased",
                "réduit",
                "diminué"
            ]
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
# FORMATAGE DES VALEURS
# =========================================================

def format_change(text):

    text = clean(text)

    # -----------------------------------------------------
    # "from 900m/s to 880m/s"
    # devient :
    # "900 m/s → 880 m/s"
    # -----------------------------------------------------

    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*m/s\s+"
        r"(?:from|de)\s+"
        r"(\d+(?:\.\d+)?)\s*m/s\s+"
        r"(?:to|à)\s+"
        r"(\d+(?:\.\d+)?)\s*m/s",
        r"\2 m/s → \3 m/s",
        text,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # "from 20% to 25%"
    # -----------------------------------------------------

    text = re.sub(
        r"(?:from|de)\s+"
        r"(\d+(?:\.\d+)?%)\s+"
        r"(?:to|à)\s+"
        r"(\d+(?:\.\d+)?%)",
        r"\1 → \2",
        text,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # "from 32 to 34"
    # -----------------------------------------------------

    text = re.sub(
        r"(?:from|de)\s+"
        r"(\d+(?:\.\d+)?)\s+"
        r"(?:to|à)\s+"
        r"(\d+(?:\.\d+)?)",
        r"\1 → \2",
        text,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # "910m/s to 920m/s"
    # -----------------------------------------------------

    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*m/s\s+"
        r"(?:to|à)\s+"
        r"(\d+(?:\.\d+)?)\s*m/s",
        r"\1 m/s → \2 m/s",
        text,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # "20% to 25%"
    # -----------------------------------------------------

    text = re.sub(
        r"(\d+(?:\.\d+)?)%\s+"
        r"(?:to|à)\s+"
        r"(\d+(?:\.\d+)?)%",
        r"\1 % → \2 %",
        text,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # "32 to 34"
    # -----------------------------------------------------

    text = re.sub(
        r"(\d+(?:\.\d+)?)\s+"
        r"(?:to|à)\s+"
        r"(\d+(?:\.\d+)?)",
        r"\1 → \2",
        text,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # "reduced by 10%"
    # -----------------------------------------------------

    text = re.sub(
        r"\breduced\s+by\s+(\d+(?:\.\d+)?)%",
        r"réduit de \1 %",
        text,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # "increased by 10%"
    # -----------------------------------------------------

    text = re.sub(
        r"\bincreased\s+by\s+(\d+(?:\.\d+)?)%",
        r"augmenté de \1 %",
        text,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # Espaces propres
    # -----------------------------------------------------

    text = re.sub(
        r"(\d+(?:\.\d+)?)%",
        r"\1 %",
        text
    )

    text = re.sub(
        r"\s+m/s",
        " m/s",
        text
    )

    text = clean(text)

    return translate(text)


# =========================================================
# SUPPRIMER LE NOM DE L'ARME
# =========================================================

def remove_weapon_name(text):

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

    # Retirer les éléments inutiles
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
# TROUVER LA SECTION WEAPONS
# =========================================================

def weapon_section(lines):

    start = None

    for index, line in enumerate(lines):

        if line.strip().upper() == "WEAPONS":

            start = index

            break

    if start is None:

        return []

    result = []

    for line in lines[start:]:

        upper = line.strip().upper()

        if upper in [
            "BUG FIXES",
            "BLACK OPS ROYALE",
            "GAMEPLAY",
            "KILLSTREAKS",
            "EQUIPMENT",
            "PERKS"
        ]:

            break

        result.append(line)

    return result


# =========================================================
# EXTRACTION DES MODIFICATIONS
# =========================================================

def extract_changes(lines):

    buffs = []
    nerfs = []

    current_weapon = "Arme"

    for line in lines:

        if not line:
            continue

        # Description de nouvelle arme
        if is_description(line):
            continue

        # -------------------------------------------------
        # Trouver l'arme
        # -------------------------------------------------

        current_weapon = detect_weapon(
            line,
            current_weapon
        )

        # -------------------------------------------------
        # IGNORER LES VALEURS DU TABLEAU
        # -------------------------------------------------

        if is_isolated_table_value(line):
            continue

        # -------------------------------------------------
        # Classer
        # -------------------------------------------------

        category = classify(line)

        if category is None:
            continue

        # -------------------------------------------------
        # Formatage
        # -------------------------------------------------

        text = format_change(line)

        # Supprimer le nom de l'arme
        text = remove_weapon_name(
            text
        )

        text = text.strip()

        if not text:
            continue

        # -------------------------------------------------
        # Éviter les lignes trop courtes
        # -------------------------------------------------

        if len(text) < 4:
            continue

        # -------------------------------------------------
        # Éviter les lignes qui ne sont
        # que des chiffres
        # -------------------------------------------------

        if re.fullmatch(
            r"[\d\s\-\>\<\.m%→]+",
            text
        ):
            continue

        # -------------------------------------------------
        # Création de l'entrée
        # -------------------------------------------------

        entry = (
            f"**{current_weapon}** — {text}"
        )

        if category == "buff":

            buffs.append(entry)

        elif category == "nerf":

            nerfs.append(entry)

    # Supprimer doublons
    buffs = unique(buffs)
    nerfs = unique(nerfs)

    return buffs, nerfs


# =========================================================
# SUPPRESSION DES DOUBLONS
# =========================================================

def unique(items):

    result = []

    seen = set()

    for item in items:

        key = item.lower().strip()

        if key in seen:
            continue

        seen.add(key)

        result.append(item)

    return result


# =========================================================
# REGROUPER PAR ARME
# =========================================================

def group_by_weapon(items):

    groups = {}

    for item in items:

        match = re.match(
            r"\*\*(.*?)\*\*\s*—\s*(.*)",
            item
        )

        if not match:
            continue

        weapon = match.group(1)
        change = match.group(2)

        if weapon not in groups:
            groups[weapon] = []

        if change not in groups[weapon]:
            groups[weapon].append(change)

    return groups


# =========================================================
# CRÉATION DU MESSAGE DISCORD
# =========================================================

def build_message(buffs, nerfs):

    buff_groups = group_by_weapon(
        buffs
    )

    nerf_groups = group_by_weapon(
        nerfs
    )

    message = (
        "🇫🇷 **CALL OF DUTY — WARZONE**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    # -----------------------------------------------------
    # BUFFS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # NERFS
    # -----------------------------------------------------

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

    if not buff_groups and not nerf_groups:

        message += (
            "⚠️ Aucun changement d'arme détecté.\n\n"
        )

    # -----------------------------------------------------
    # FOOTER
    # -----------------------------------------------------

    message += (
        "📅 **Saison 05 Reloaded**\n\n"
        "🔗 **Notes officielles :**\n"
        f"{PATCH_URL}"
    )

    return message


# =========================================================
# ENVOI DISCORD
# =========================================================

def send_discord(message):

    if not WEBHOOK_URL:

        raise RuntimeError(
            "❌ Le secret DISCORD_WEBHOOK est absent."
        )

    # Discord accepte environ 2000 caractères
    # par message.

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
# MÉMOIRE DU PATCH
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
# PROGRAMME PRINCIPAL
# =========================================================

def main():

    print(
        "🔎 Lecture des notes de correctif Warzone..."
    )

    # -----------------------------------------------------
    # Télécharger
    # -----------------------------------------------------

    html = get_page(
        PATCH_URL
    )

    print(
        "✅ Page récupérée."
    )

    # -----------------------------------------------------
    # Extraire
    # -----------------------------------------------------

    lines = extract_lines(
        html
    )

    print(
        f"📄 {len(lines)} éléments trouvés."
    )

    # -----------------------------------------------------
    # Section armes
    # -----------------------------------------------------

    lines = weapon_section(
        lines
    )

    print(
        f"🔫 {len(lines)} lignes dans la section armes."
    )

    # -----------------------------------------------------
    # Vérifier le patch déjà envoyé
    # -----------------------------------------------------

    last_patch = get_last_patch()

    if last_patch == PATCH_URL:

        print(
            "ℹ️ Ce patch a déjà été envoyé."
        )

        return

    # -----------------------------------------------------
    # Extraire les changements
    # -----------------------------------------------------

    buffs, nerfs = extract_changes(
        lines
    )

    print(
        f"🟢 Buffs détectés : {len(buffs)}"
    )

    print(
        f"🔴 Nerfs détectés : {len(nerfs)}"
    )

    # -----------------------------------------------------
    # Construire Discord
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Envoyer
    # -----------------------------------------------------

    send_discord(
        message
    )

    # -----------------------------------------------------
    # Sauvegarder
    # -----------------------------------------------------

    save_last_patch()

    print(
        "✅ Patch envoyé sur Discord."
    )


# =========================================================
# LANCEMENT
# =========================================================

if __name__ == "__main__":

    main()
