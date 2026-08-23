import os
import re
import json
import hashlib
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
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    )
}

# Fichier qui mémorise le dernier patch envoyé
STATE_FILE = "last_patch.json"


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
    "vertical recoil": "Recul vertical",

    "Horizontal Recoil": "Recul horizontal",
    "horizontal recoil": "Recul horizontal",

    "Recoil Control": "Contrôle du recul",
    "recoil control": "Contrôle du recul",

    "Recoil": "Recul",
    "recoil": "Recul",

    "Gunkick": "Recul de visée",
    "gunkick": "Recul de visée",

    "Viewkick": "Recul de caméra",
    "viewkick": "Recul de caméra",

    "ADS Speed": "Vitesse ADS",
    "ADS speed": "Vitesse ADS",

    "Aim Down Sight Speed": "Vitesse ADS",

    "Damage Range": "Portée des dégâts",
    "damage range": "Portée des dégâts",

    "Max Damage": "Dégâts maximum",
    "max damage": "Dégâts maximum",

    "Minimum Damage": "Dégâts minimum",
    "minimum damage": "Dégâts minimum",

    "Damage": "Dégâts",
    "damage": "Dégâts",

    "Headshot Multiplier": "Multiplicateur de dégâts à la tête",
    "Headshot multiplier": "Multiplicateur de dégâts à la tête",

    "Headshot": "Tir à la tête",
    "headshot": "tir à la tête",

    "Upper Torso": "haut du torse",
    "upper torso": "haut du torse",

    "Upper Body": "haut du corps",
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
        text = text.replace(english, french)

    return clean(text)


# ============================================================
# FORMATAGE DES VALEURS
# ============================================================

def format_numbers(text):

    # Pourcentages
    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*%\s*(?:à|to)\s*"
        r"(\d+(?:\.\d+)?)\s*%",
        r"\1 % → \2 %",
        text,
        flags=re.I
    )

    # m/s
    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*m/s\s*(?:à|to)\s*"
        r"(\d+(?:\.\d+)?)\s*m/s",
        r"\1 m/s → \2 m/s",
        text,
        flags=re.I
    )

    # mètres
    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*m\s*(?:à|to)\s*"
        r"(\d+(?:\.\d+)?)\s*m",
        r"\1 m → \2 m",
        text,
        flags=re.I
    )

    # multiplicateurs
    text = re.sub(
        r"(\d+(?:\.\d+)?)x\s*(?:à|to)\s*"
        r"(\d+(?:\.\d+)?)x",
        r"\1× → \2×",
        text,
        flags=re.I
    )

    # nombres simples
    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*(?:à|to)\s*"
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

        "Tir à la tête multiplier":
            "Multiplicateur de dégâts à la tête",

        "Headshot multiplier":
            "Multiplicateur de dégâts à la tête",

        "headshot et upper torse dégâts":
            "dégâts aux tirs à la tête et au haut du torse",

        "headshot et haut du torse dégâts":
            "dégâts aux tirs à la tête et au haut du torse",
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

    for weapon in sorted(
        WEAPONS,
        key=len,
        reverse=True
    ):
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

    return any(
        word in lower
        for word in ignored
    )


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
            r"[\d\s\-><\.m]+",
            cleaned,
            re.I
        )
    )


# ============================================================
# CLASSIFICATION BUFF / NERF
# ============================================================

def classify(text):

    lower = text.lower()

    # ========================================================
    # MALUS
    # ========================================================

    if "malus" in lower or "penalty" in lower:

        # Un malus qui diminue = BUFF
        if any(
            word in lower
            for word in [
                "malus diminué",
                "malus réduit",
                "malus decreased",
                "malus reduced",
                "penalty diminué",
                "penalty réduit",
                "penalty decreased",
                "penalty reduced"
            ]
        ):
            return "buff"

        # Un malus qui augmente = NERF
        if any(
            word in lower
            for word in [
                "malus augmenté",
                "malus augmente",
                "penalty augmenté",
                "penalty increased"
            ]
        ):
            return "nerf"

    # ========================================================
    # BONUS
    # ========================================================

    if any(
        word in lower
        for word in [
            "bonus amélioré",
            "bonus augmenté",
            "benefit amélioré",
            "benefit augmenté"
        ]
    ):
        return "buff"

    if any(
        word in lower
        for word in [
            "bonus réduit",
            "bonus diminué",
            "benefit réduit",
            "benefit diminué"
        ]
    ):
        return "nerf"

    # ========================================================
    # RECUL
    # ========================================================

    if any(
        word in lower
        for word in [
            "recul",
            "recoil",
            "gunkick",
            "viewkick"
        ]
    ):

        if any(
            word in lower
            for word in [
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
            ]
        ):
            return "buff"

        if any(
            word in lower
            for word in [
                "augmenté",
                "augmentée",
                "augmentés",
                "augmentées",
                "increased"
            ]
        ):
            return "nerf"

    # ========================================================
    # VITESSE DES PROJECTILES
    # ========================================================

    if (
        "vitesse des projectiles" in lower
        or "bullet velocity" in lower
    ):

        if any(
            word in lower
            for word in [
                "augmenté",
                "augmentée",
                "augmentés",
                "augmentées",
                "amélioré",
                "améliorée",
                "increased",
                "improved"
            ]
        ):
            return "buff"

        if any(
            word in lower
            for word in [
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
            ]
        ):
            return "nerf"

    # ========================================================
    # DÉGÂTS
    # ========================================================

    if any(
        word in lower
        for word in [
            "dégâts",
            "damage",
            "multiplicateur"
        ]
    ):

        if any(
            word in lower
            for word in [
                "augmenté",
                "augmentée",
                "augmentés",
                "augmentées",
                "amélioré",
                "améliorée",
                "increased",
                "improved"
            ]
        ):
            return "buff"

        if any(
            word in lower
            for word in [
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
            ]
        ):
            return "nerf"

    # ========================================================
    # PORTÉE
    # ========================================================

    if (
        "portée des dégâts" in lower
        or "damage range" in lower
    ):

        if any(
            word in lower
            for word in [
                "augmenté",
                "augmentée",
                "augmentés",
                "augmentées",
                "amélioré",
                "améliorée",
                "increased",
                "improved"
            ]
        ):
            return "buff"

        if any(
            word in lower
            for word in [
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
            ]
        ):
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

        if category == "buff":
            buffs.append(
                (current_weapon, text)
            )

        elif category == "nerf":
            nerfs.append(
                (current_weapon, text)
            )

    return buffs, nerfs


# ============================================================
# NORMALISATION
# ============================================================

def normalize(text):

    text = text.lower()

    replacements = {
        "réduit": "diminué",
        "réduite": "diminuée",
        "réduits": "diminués",
        "réduites": "diminuées",
        "reduced": "diminué",
        "decreased": "diminué"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = text.replace(" ", "")

    return text


# ============================================================
# DOUBLONS
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
# BUFF / NERF EN DOUBLE
# ============================================================

def remove_cross_duplicates(
    buffs,
    nerfs
):

    buffs = remove_duplicates(buffs)
    nerfs = remove_duplicates(nerfs)

    buff_keys = set()

    for weapon, change in buffs:

        buff_keys.add(
            (
                weapon.lower(),
                normalize(change)
            )
        )

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
# ACCESSOIRES
# ============================================================

ATTACHMENT_PATTERNS = [
    r'\d+(?:\.\d+)?".*?Barrel',
    r'\d+(?:\.\d+)?".*?Grip',
    r'\d+(?:\.\d+)?".*?Compensator',
    r'\d+(?:\.\d+)?".*?Stock',
    r'\d+(?:\.\d+)?".*?Magazine',
    r'\d+(?:\.\d+)?".*?Suppressor',
    r'\d+(?:\.\d+)?".*?Muzzle',
    r'\.300 WM Overpressured',
    r'5\.56 NATO FMJ',
    r'12 Gauge Slug',
    r'Argus Lever'
]


def is_attachment_start(text):

    text = text.strip()

    for pattern in ATTACHMENT_PATTERNS:

        if re.match(
            pattern,
            text,
            re.I
        ):
            return True

    return False


# ============================================================
# SÉPARATION INTELLIGENTE
# ============================================================

def split_multiple_changes(text):

    text = text.strip()

    patterns = [
        r"\s+(?=Portée intermédiaire des dégâts\s+bonus)",
        r"\s+(?=Portée maximale des dégâts\s+)",
        r"\s+(?=Multiplicateur de dégâts à la tête\s+)"
    ]

    parts = [text]

    for pattern in patterns:

        new_parts = []

        for part in parts:

            split = re.split(
                pattern,
                part,
                flags=re.I
            )

            if len(split) == 1:
                new_parts.append(part)

            else:

                first = split[0].strip()

                if first:
                    new_parts.append(first)

                for extra in split[1:]:

                    if extra.strip():
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
# CONSTRUCTION DU MESSAGE
# ============================================================

def build_message(
    buffs,
    nerfs
):

    buffs = remove_duplicates(buffs)
    nerfs = remove_duplicates(nerfs)

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
        "📅 **Saison 05 Reloaded**"
    )

    return message


# ============================================================
# MÉMOIRE DU DERNIER PATCH
# ============================================================

def load_last_patch():

    if not os.path.exists(STATE_FILE):
        return None

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        return data.get("hash")

    except Exception:

        return None


def save_last_patch(patch_hash):

    data = {
        "hash": patch_hash
    }

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


def get_patch_hash(message):

    return hashlib.sha256(
        message.encode("utf-8")
    ).hexdigest()


# ============================================================
# ENVOI DISCORD
# ============================================================

def send_discord(message):

    if not WEBHOOK_URL:

        raise RuntimeError(
            "La variable DISCORD_WEBHOOK est introuvable."
        )

    # Discord permet jusqu'à 4096 caractères
    # dans la description d'un embed.
    #
    # On utilise donc un embed pour éviter
    # plusieurs messages lorsque le patch dépasse
    # la limite classique de 2000 caractères.

    if len(message) <= 4096:

        payload = {
            "username": "COD Patch Bot",
            "embeds": [
                {
                    "description": message,
                    "color": 5763719,
                    "footer": {
                        "text": "Notes officielles Call of Duty"
                    },
                    "url": PATCH_URL
                }
            ]
        }

        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        return

    # Sécurité si le message dépasse 4096 caractères.
    # Dans ce cas seulement, plusieurs messages seront envoyés.

    chunks = []

    while len(message) > 3900:

        position = message.rfind(
            "\n",
            0,
            3900
        )

        if position <= 0:
            position = 3900

        chunks.append(
            message[:position]
        )

        message = message[
            position:
        ].lstrip()

    if message:
        chunks.append(message)

    for chunk in chunks:

        payload = {
            "username": "COD Patch Bot",
            "embeds": [
                {
                    "description": chunk,
                    "color": 5763719,
                    "url": PATCH_URL
                }
            ]
        }

        response = requests.post(
            WEBHOOK_URL,
            json=payload,
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

    if not WEBHOOK_URL:

        print(
            "❌ ERREUR : DISCORD_WEBHOOK n'est pas défini."
        )

        return

    try:

        response = requests.get(
            PATCH_URL,
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

    except requests.RequestException as error:

        print(
            f"❌ Impossible de récupérer le patch : {error}"
        )

        return

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

    # ========================================================
    # VÉRIFICATION DU DOUBLON GLOBAL
    # ========================================================

    current_hash = get_patch_hash(
        message
    )

    last_hash = load_last_patch()

    if last_hash == current_hash:

        print(
            "ℹ️ Ce patch a déjà été envoyé."
        )

        print(
            "🚫 Aucun nouveau message Discord envoyé."
        )

        return

    # ========================================================
    # NOUVEAU PATCH
    # ========================================================

    print(
        "🆕 Nouveau patch détecté !"
    )

    print(
        "\n========== MESSAGE ==========\n"
    )

    print(message)

    print(
        "\n=============================\n"
    )

    try:

        send_discord(
            message
        )

    except requests.RequestException as error:

        print(
            f"❌ Erreur lors de l'envoi Discord : {error}"
        )

        return

    # On mémorise uniquement après
    # un envoi Discord réussi.

    save_last_patch(
        current_hash
    )

    print(
        "✅ Patch envoyé sur Discord !"
    )

    print(
        "💾 Patch mémorisé pour éviter les doublons."
    )


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":
    main()
