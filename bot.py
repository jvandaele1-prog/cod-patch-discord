import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

INDEX_URL = "https://www.callofduty.com/fr/patchnotes"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def get_html(url):
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_warzone_patch(index_html):
    soup = BeautifulSoup(index_html, "html.parser")

    links = soup.find_all("a", href=True)

    candidates = []

    for link in links:
        text = clean_text(link.get_text(" ", strip=True))
        href = link.get("href", "")

        combined = f"{text} {href}".lower()

        if (
            "warzone" in combined
            and "patch" in combined
        ):
            full_url = urljoin(INDEX_URL, href)

            if full_url not in candidates:
                candidates.append(full_url)

    # On privilégie les liens contenant warzone + patch-notes
    for url in candidates:
        if "warzone" in url.lower() and "patch" in url.lower():
            return url

    return candidates[0] if candidates else None


def extract_sections(html):
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(["script", "style", "noscript", "svg"]):
        element.decompose()

    text = soup.get_text("\n")

    lines = []

    for line in text.splitlines():
        line = clean_text(line)

        if line:
            lines.append(line)

    return lines


def remove_duplicates(lines):
    result = []
    seen = set()

    for line in lines:
        key = line.lower()

        if key not in seen:
            seen.add(key)
            result.append(line)

    return result


def find_useful_content(lines):
    useful = []

    keywords = [
        "arme",
        "armes",
        "fusil",
        "mitraillette",
        "pistolet",
        "fusil d'assaut",
        "fusil de précision",
        "dégâts",
        "portée",
        "recul",
        "correctif",
        "correction",
        "ajustement",
        "warzone",
        "battle royale",
        "résurgence"
    ]

    for i, line in enumerate(lines):

        if any(keyword in line.lower() for keyword in keywords):

            start = max(0, i - 2)
            end = min(len(lines), i + 8)

            for item in lines[start:end]:

                if item not in useful:
                    useful.append(item)

    return remove_duplicates(useful)


def classify(lines):
    buffs = []
    nerfs = []
    corrections = []
    other = []

    for line in lines:

        lower = line.lower()

        # BUFF
        if any(word in lower for word in [
            "increased",
            "increase",
            "increases",
            "augmented",
            "augmentée",
            "augmenté",
            "augmentées",
            "augmentés",
            "amélioré",
            "améliorée",
            "amélioration"
        ]):
            buffs.append(line)

        # NERF
        elif any(word in lower for word in [
            "reduced",
            "reduce",
            "decreased",
            "decrease",
            "réduit",
            "réduite",
            "réduits",
            "réduites",
            "diminué",
            "diminuée",
            "diminution"
        ]):
            nerfs.append(line)

        # CORRECTIONS
        elif any(word in lower for word in [
            "correction",
            "correctif",
            "corrigé",
            "corrigée",
            "résolu",
            "résolue",
            "problème"
        ]):
            corrections.append(line)

        else:
            other.append(line)

    return buffs, nerfs, corrections, other


def limit_text(lines, maximum=900):
    result = []
    total = 0

    for line in lines:

        addition = f"• {line}\n"

        if total + len(addition) > maximum:
            break

        result.append(addition)
        total += len(addition)

    return "".join(result)


def send_discord(message):
    if not WEBHOOK_URL:
        raise RuntimeError("DISCORD_WEBHOOK est introuvable.")

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

    print("🔎 Recherche des notes Warzone...")

    index_html = get_html(INDEX_URL)

    patch_url = find_warzone_patch(index_html)

    if not patch_url:
        print("❌ Impossible de trouver la note Warzone.")
        return

    print(f"✅ Note trouvée : {patch_url}")

    patch_html = get_html(patch_url)

    lines = extract_sections(patch_html)

    useful = find_useful_content(lines)

    buffs, nerfs, corrections, other = classify(useful)

    message = (
        "🇫🇷 **CALL OF DUTY — WARZONE**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if buffs:
        message += "🟢 **BUFFS**\n"
        message += limit_text(buffs)
        message += "\n"

    if nerfs:
        message += "🔴 **NERFS**\n"
        message += limit_text(nerfs)
        message += "\n"

    if corrections:
        message += "🛠️ **CORRECTIONS**\n"
        message += limit_text(corrections)
        message += "\n"

    if not buffs and not nerfs and not corrections:
        message += "📋 **MODIFICATIONS**\n"
        message += limit_text(useful)

    message += (
        "\n🔗 **Notes officielles :**\n"
        + patch_url
    )

    if len(message) > 1900:
        message = message[:1850] + "\n\n…\n\n" + patch_url

    send_discord(message)

    print("✅ Message envoyé sur Discord.")


if __name__ == "__main__":
    main()
