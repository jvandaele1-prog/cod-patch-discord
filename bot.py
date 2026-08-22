import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

INDEX_URL = "https://www.callofduty.com/fr/patchnotes"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/131.0 Safari/537.36"
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


def find_warzone_links(html):
    soup = BeautifulSoup(html, "html.parser")

    results = []

    for link in soup.find_all("a", href=True):

        text = clean(link.get_text(" ", strip=True))
        href = link["href"]

        full_url = urljoin(INDEX_URL, href)

        combined = (text + " " + full_url).lower()

        # On cherche uniquement les véritables notes Warzone
        if "warzone" in combined and "patch-notes" in combined:

            if full_url not in results:
                results.append(full_url)

    return results


def choose_latest_link(links):

    if not links:
        return None

    # Les URL Call of Duty contiennent généralement
    # l'année et le mois de publication.
    # On choisit la première URL trouvée dans la rubrique WZ.

    return links[0]


def extract_patch(html):

    soup = BeautifulSoup(html, "html.parser")

    for element in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "nav",
        "footer"
    ]):
        element.decompose()

    # Cherche le contenu principal
    main = soup.find("main")

    if main:
        text = main.get_text("\n", strip=True)
    else:
        text = soup.get_text("\n", strip=True)

    lines = []

    for line in text.splitlines():

        line = clean(line)

        if not line:
            continue

        # Élimine certains éléments de navigation
        if line in [
            "Skip To Main Content",
            "Search",
            "Profil",
            "Menu",
            "Close Menu",
            "Connexion",
            "S'inscrire"
        ]:
            continue

        lines.append(line)

    return lines


def find_weapon_section(lines):

    start = None

    for i, line in enumerate(lines):

        upper = line.upper()

        if upper in [
            "WEAPONS",
            "ARMES",
            "WEAPONS ADJUSTMENTS",
            "AJUSTEMENTS DES ARMES"
        ]:
            start = i
            break

    if start is None:
        return []

    section = []

    for line in lines[start:]:

        upper = line.upper()

        # On s'arrête à une nouvelle grande section
        if line in [
            "MAPS",
            "MODES",
            "PERKS",
            "EQUIPMENT",
            "FIELD UPGRADES",
            "KILLSTREAKS",
            "BUG FIXES",
            "CORRECTIONS DE BUGS"
        ] and len(section) > 5:
            break

        section.append(line)

        if len(section) >= 120:
            break

    return section


def classify_weapon_changes(lines):

    buffs = []
    nerfs = []
    corrections = []

    for line in lines:

        lower = line.lower()

        # Changements positifs
        positive = [
            "increased",
            "increase",
            "improved",
            "improvement",
            "augmenté",
            "augmentée",
            "augmentés",
            "augmentées",
            "amélioré",
            "améliorée",
            "amélioration",
            "↑"
        ]

        # Changements négatifs
        negative = [
            "reduced",
            "reduction",
            "decreased",
            "decrease",
            "reduction",
            "réduit",
            "réduite",
            "réduits",
            "réduites",
            "diminué",
            "diminuée",
            "diminution",
            "↓"
        ]

        if any(word in lower for word in positive):
            buffs.append(line)

        elif any(word in lower for word in negative):
            nerfs.append(line)

        elif any(word in lower for word in [
            "fixed",
            "fix",
            "correction",
            "corrected",
            "corrigé",
            "corrigée"
        ]):
            corrections.append(line)

    return buffs, nerfs, corrections


def unique(items):

    result = []
    seen = set()

    for item in items:

        key = item.lower()

        if key not in seen:
            seen.add(key)
            result.append(item)

    return result


def format_section(title, emoji, lines, maximum=650):

    if not lines:
        return ""

    output = f"{emoji} **{title}**\n"

    total = len(output)

    for line in unique(lines):

        item = f"• {line}\n"

        if total + len(item) > maximum:
            output += "• ...\n"
            break

        output += item
        total += len(item)

    return output + "\n"


def send_discord(message):

    if not WEBHOOK_URL:
        raise RuntimeError(
            "Le secret DISCORD_WEBHOOK est absent."
        )

    response = requests.post(
        WEBHOOK_URL,
        json={
            "username": "COD Patch Bot",
            "content": message
        },
        timeout=30
    )

    response.raise_for_status()


def main():

    print("🔎 Recherche des notes Call of Duty...")

    index_html = get_page(INDEX_URL)

    links = find_warzone_links(index_html)

    print("🔗 Liens Warzone trouvés :", len(links))

    for link in links:
        print(link)

    patch_url = choose_latest_link(links)

    if not patch_url:
        print("❌ Aucune note Warzone trouvée.")
        return

    print("✅ Note sélectionnée :")
    print(patch_url)

    patch_html = get_page(patch_url)

    lines = extract_patch(patch_html)

    print("📄 Lignes récupérées :", len(lines))

    weapon_section = find_weapon_section(lines)

    print("🔫 Lignes de la section armes :", len(weapon_section))

    buffs, nerfs, corrections = classify_weapon_changes(
        weapon_section
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

    if not buffs and not nerfs and not corrections:

        message += (
            "📋 **MODIFICATIONS D'ARMES**\n"
            "Aucun changement détecté automatiquement.\n\n"
        )

    message += (
        "🔗 **Notes officielles :**\n"
        + patch_url
    )

    if len(message) > 1900:
        message = message[:1800]
        message += "\n\n🔗 **Notes officielles :**\n"
        message += patch_url

    send_discord(message)

    print("✅ Message envoyé sur Discord.")


if __name__ == "__main__":
    main()
