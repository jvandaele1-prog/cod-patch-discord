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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
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

        # On arrête la section à Black Ops Royale
        # ou aux corrections.
        if line.strip().upper() in [
            "BUG FIXES",
            "BLACK OPS ROYALE"
        ]:
            break

        result.append(line)

    return result


def get_weapon_name(lines, index):

    # Cherche le dernier "Weapon:" avant la ligne actuelle
    # ou les titres connus.
    for i in range(index, -1, -1):

        line = lines[i].strip()

        if line.startswith("Weapon:"):

            name = line.replace(
                "Weapon:",
                ""
            ).strip()

            if name:
                return name

        # Les noms d'armes sont souvent seuls dans un H3
        if line.upper() in [
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
            "STRIDER 300"
        ]:
            return line

    return "Arme"


def extract_changes(lines):

    buffs = []
    nerfs = []
    corrections = []

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
        "STRIDER 300"
    ]

    for i, line in enumerate(lines):

        lower = line.lower()

        # ------------------------------------------------
        # CORRECTIONS
        # ------------------------------------------------

        if (
            "fixed an issue" in lower
            or "fixed" in lower
            or "correction" in lower
        ):
            corrections.append(line)
            continue

        # ------------------------------------------------
        # CHANGEMENTS DIRECTS
        # ------------------------------------------------

        is_weapon_change = any(
            word in lower
            for word in [
                "increased",
                "increased from",
                "improved",
                "reduced",
                "decreased",
                "decreased from",
                "penalty decreased",
                "benefit increased",
                "benefit improved"
            ]
        )

        # Valeurs du type :
        # 38 -> 41
        # 20% -> 25%
        # 900m/s -> 880m/s
        numeric_change = re.search(
            r"\b\d+(?:\.\d+)?%?\s*"
            r"(?:to|→|->)\s*"
            r"\d+(?:\.\d+)?%?",
            line,
            re.IGNORECASE
        )

        # ------------------------------------------------
        # TABLEAUX PRE-PATCH / POST-PATCH
        # ------------------------------------------------

        arrow_up = "⇧" in line or "↑" in line
        arrow_down = "⇩" in line or "↓" in line

        if arrow_up:
            is_weapon_change = True

        if arrow_down:
            is_weapon_change = True

        if not is_weapon_change and not numeric_change:
            continue

        weapon = get_weapon_name(
            lines,
            i
        )

        entry = f"**{weapon}** — {line}"

        if arrow_down:
            nerfs.append(entry)

        elif (
            "decreased" in lower
            or "reduced" in lower
            or "decrease" in lower
            or "reduction" in lower
        ):
            nerfs.append(entry)

        else:
            buffs.append(entry)

    return (
        unique(buffs),
        unique(nerfs),
        unique(corrections)
    )


def unique(items):

    result = []
    seen = set()

    for item in items:

        key = item.lower()

        if key not in seen:

            seen.add(key)
            result.append(item)

    return result


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

        "Sprint to Fire speed": "Vitesse de sprint vers tir",

        "ADS Speed": "Vitesse ADS",

        "Benefit": "Bonus",

        "improved from": "amélioré de",
        "increased from": "augmenté de",
        "decreased from": "réduit de",
        "reduced from": "réduit de",

        "to": "à",

        "All Modes": "Tous les modes",
        "BR/RES Only": "Battle Royale / Résurgence uniquement",

        "Max Damage": "Dégâts max.",
        "Mid 1 Damage": "Dégâts moyens 1",
        "Minimum Damage": "Dégâts minimum",

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


def format_section(
    title,
    emoji,
    lines,
    maximum=750
):

    if not lines:
        return ""

    message = (
        f"{emoji} **{title}**\n"
    )

    total = len(message)

    for line in lines:

        line = translate(line)

        item = f"• {line}\n"

        if total + len(item) > maximum:

            message += "• ...\n"
            break

        message += item
        total += len(item)

    return message + "\n"


def build_message(lines):

    buffs, nerfs, corrections = extract_changes(
        lines
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

    if not buffs and not nerfs:

        message += (
            "⚠️ Aucun changement d'arme détecté.\n\n"
        )

    message += (
        "📅 **Patch : Saison 05 Reloaded**\n\n"
        "🔗 **Notes officielles :**\n"
        f"{PATCH_URL}"
    )

    return message


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


def send_discord(message):

    if not WEBHOOK_URL:

        raise RuntimeError(
            "Le secret DISCORD_WEBHOOK est absent."
        )

    # Discord limite les messages à 2000 caractères.
    chunks = []

    while len(message) > 1900:

        position = message.rfind(
            "\n",
            0,
            1900
        )

        if position == -1:
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


def main():

    print(
        "🔎 Téléchargement des notes Warzone..."
    )

    html = get_page(PATCH_URL)

    lines = get_content(html)

    print(
        f"📄 {len(lines)} éléments récupérés."
    )

    weapon_section = find_weapon_section(
        lines
    )

    print(
        f"🔫 {len(weapon_section)} éléments "
        "dans la section armes."
    )

    last_patch = get_last_patch()

    if last_patch == PATCH_URL:

        print(
            "ℹ️ Ce patch a déjà été envoyé."
        )

        return

    message = build_message(
        weapon_section
    )

    send_discord(message)

    save_last_patch()

    print(
        "✅ Patch envoyé sur Discord."
    )


if __name__ == "__main__":
    main()
