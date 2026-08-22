import os
import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

# Page officielle anglaise : elle est actuellement plus à jour
# que la page française.
INDEX_URL = "https://www.callofduty.com/patchnotes"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    )
}

STATE_FILE = "last_patch.txt"


# ---------------------------------------------------------
# OUTILS
# ---------------------------------------------------------

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


def normalize_url(url):
    return url.split("#")[0].rstrip("/")


# ---------------------------------------------------------
# RECHERCHE DE LA DERNIÈRE NOTE WARZONE
# ---------------------------------------------------------

def find_latest_warzone_patch():

    html = get_page(INDEX_URL)

    soup = BeautifulSoup(html, "html.parser")

    candidates = []

    for link in soup.find_all("a", href=True):

        text = clean(link.get_text(" ", strip=True))
        href = link.get("href", "")

        full_url = urljoin(INDEX_URL, href)

        combined = (
            text + " " + full_url
        ).lower()

        # On cherche uniquement les notes Warzone
        if "warzone" in combined and "patch-notes" in combined:

            full_url = normalize_url(full_url)

            if full_url not in candidates:
                candidates.append(full_url)

    if not candidates:
        raise RuntimeError(
            "Impossible de trouver une note Warzone."
        )

    # La page officielle présente les notes de la plus récente
    # vers les anciennes.
    return candidates[0]


# ---------------------------------------------------------
# EXTRACTION DU CONTENU
# ---------------------------------------------------------

def extract_content(html):

    soup = BeautifulSoup(html, "html.parser")

    # Suppression des éléments inutiles
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


# ---------------------------------------------------------
# TRADUCTION SIMPLE
# ---------------------------------------------------------

TRANSLATIONS = {
    "Weapons": "Armes",
    "Weapon": "Arme",
    "Weapons & Attachments": "Armes et accessoires",
    "Weapon Adjustments": "Ajustements des armes",
    "Gameplay": "Gameplay",
    "Killstreaks": "Séries d'éliminations",
    "Bug Fixes": "Corrections de bugs",
    "Bug Fix": "Correction de bug",
    "General": "Général",
    "Modes": "Modes",
    "Maps": "Cartes",
    "Perks": "Atouts",
    "Equipment": "Équipement",
    "Increased": "Augmenté",
    "Increase": "Augmentation",
    "Reduced": "Réduit",
    "Reduction": "Réduction",
    "Decreased": "Diminué",
    "Decrease": "Diminution",
    "Damage": "Dégâts",
    "Damage Range": "Portée des dégâts",
    "Range": "Portée",
    "Recoil": "Recul",
    "Fire Rate": "Cadence de tir",
    "Movement Speed": "Vitesse de déplacement",
    "Sprint Speed": "Vitesse de sprint",
    "Reload Speed": "Vitesse de rechargement",
    "Magazine Size": "Taille du chargeur",
    "Bullet Velocity": "Vitesse des projectiles",
    "Headshot": "Tir à la tête",
    "Fixed": "Correction",
    "Fixed an issue": "Correction d'un problème",
    "Addressed an issue": "Correction d'un problème",
    "Players": "Joueurs",
    "Health": "Points de vie",
    "Duration": "Durée",
    "Radius": "Rayon",
    "seconds": "secondes",
    "second": "seconde",
    "meters": "mètres",
    "meter": "mètre"
}


def translate_line(text):

    result = text

    # Traductions des expressions les plus importantes
    # On commence par les expressions longues.
    replacements = sorted(
        TRANSLATIONS.items(),
        key=lambda x: len(x[0]),
        reverse=True
    )

    for english, french in replacements:

        result = re.sub(
            r"\b" + re.escape(english) + r"\b",
            french,
            result,
            flags=re.IGNORECASE
        )

    return result


# ---------------------------------------------------------
# DÉTECTION BUFF / NERF
# ---------------------------------------------------------

def classify_line(line):

    lower = line.lower()

    positive_words = [
        "increased",
        "increase",
        "increases",
        "improved",
        "improvement",
        "augmenté",
        "augmentée",
        "augmentés",
        "augmentées",
        "amélioré",
        "améliorée",
        "amélioration"
    ]

    negative_words = [
        "reduced",
        "reduce",
        "reduces",
        "decreased",
        "decrease",
        "reduction",
        "réduit",
        "réduite",
        "réduits",
        "réduites",
        "diminué",
        "diminuée",
        "diminution"
    ]

    correction_words = [
        "fixed",
        "fix",
        "addressed an issue",
        "correction",
        "corrected",
        "corrigé",
        "corrigée",
        "problème"
    ]

    if any(word in lower for word in positive_words):
        return "buff"

    if any(word in lower for word in negative_words):
        return "nerf"

    if any(word in lower for word in correction_words):
        return "correction"

    return None


# ---------------------------------------------------------
# DÉTECTION DES CHANGEMENTS INTÉRESSANTS
# ---------------------------------------------------------

def extract_changes(lines):

    buffs = []
    nerfs = []
    corrections = []

    weapon_context = False

    for line in lines:

        lower = line.lower()

        # Détection des sections d'armes
        if (
            "weapons" in lower
            or "weapon adjustments" in lower
            or "weapons & attachments" in lower
            or "armes" in lower
        ):
            weapon_context = True

        # Une nouvelle grosse section peut terminer le contexte armes
        if lower in [
            "gameplay",
            "killstreaks",
            "bug fixes",
            "maps",
            "modes",
            "perks",
            "equipment"
        ]:
            weapon_context = False

        category = classify_line(line)

        # On garde les changements chiffrés même si
        # le mot increased/reduced n'est pas présent.
        numeric_change = bool(
            re.search(
                r"\b\d+(?:\.\d+)?\s*(?:→|->|to)\s*\d+(?:\.\d+)?\b",
                line,
                flags=re.IGNORECASE
            )
        )

        if category == "buff":
            buffs.append(line)

        elif category == "nerf":
            nerfs.append(line)

        elif category == "correction":
            corrections.append(line)

        elif weapon_context and numeric_change:
            # Si une valeur change dans la section armes,
            # on la conserve.
            buffs.append(line)

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


# ---------------------------------------------------------
# FORMATAGE DISCORD
# ---------------------------------------------------------

def format_section(title, emoji, lines, maximum=600):

    if not lines:
        return ""

    message = f"{emoji} **{title}**\n"

    total = len(message)

    for line in lines:

        translated = translate_line(line)

        item = f"• {translated}\n"

        if total + len(item) > maximum:
            message += "• ...\n"
            break

        message += item
        total += len(item)

    return message + "\n"


def build_message(patch_url, lines):

    buffs, nerfs, corrections = extract_changes(lines)

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

    if not buffs and not nerfs and not corrections:

        message += (
            "📋 **MODIFICATIONS**\n"
            "Aucun changement automatiquement détecté.\n\n"
        )

    message += (
        "🔗 **Notes officielles :**\n"
        + patch_url
    )

    return message


# ---------------------------------------------------------
# MÉMOIRE DU DERNIER PATCH
# ---------------------------------------------------------

def get_last_patch():

    if not os.path.exists(STATE_FILE):
        return ""

    with open(
        STATE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return file.read().strip()


def save_last_patch(patch_url):

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(patch_url)


# ---------------------------------------------------------
# DISCORD
# ---------------------------------------------------------

def send_discord(message):

    if not WEBHOOK_URL:
        raise RuntimeError(
            "Le secret DISCORD_WEBHOOK est absent."
        )

    # Discord limite un message à 2000 caractères.
    # On découpe automatiquement si nécessaire.

    chunks = []

    while len(message) > 1900:

        split_at = message.rfind(
            "\n",
            0,
            1900
        )

        if split_at <= 0:
            split_at = 1900

        chunks.append(
            message[:split_at]
        )

        message = message[split_at:].lstrip()

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


# ---------------------------------------------------------
# PROGRAMME PRINCIPAL
# ---------------------------------------------------------

def main():

    print("======================================")
    print("   CALL OF DUTY WARZONE PATCH BOT")
    print("======================================")

    print("🔎 Recherche de la dernière note Warzone...")

    patch_url = find_latest_warzone_patch()

    print("✅ Dernière note trouvée :")
    print(patch_url)

    last_patch = get_last_patch()

    # Si elle a déjà été envoyée, on ne renvoie rien.
    if patch_url == last_patch:

        print("ℹ️ Cette note a déjà été envoyée.")
        print("⏭️ Aucun message Discord envoyé.")

        return

    print("📥 Téléchargement de la note...")

    html = get_page(patch_url)

    lines = extract_content(html)

    print(
        "📄",
        len(lines),
        "éléments récupérés."
    )

    message = build_message(
        patch_url,
        lines
    )

    print("📤 Envoi vers Discord...")

    send_discord(message)

    save_last_patch(patch_url)

    print("✅ Patch envoyé avec succès.")


if __name__ == "__main__":
    main()
