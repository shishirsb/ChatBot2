from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def extract_image_candidates(url):
    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    candidates = []
    seen = set()

    skip_words = {
        "icon",
        "logo",
        "avatar",
        "favicon",
        "social",
        "button",
        "menu",
        "arrow",
        "facebook",
        "twitter",
        "instagram",
        "linkedin",
        "youtube"
    }

    for img in soup.find_all("img"):

        src = (
            img.get("src")
            or img.get("data-src")
            or img.get("data-lazy-src")
            or img.get("data-original")
        )

        if not src:
            continue

        if src.startswith("data:"):
            continue

        image_url = urljoin(url, src)

        if image_url in seen:
            continue

        seen.add(image_url)

        # ----------------------------------------
        # Inspect HTML metadata
        # ----------------------------------------

        alt = (img.get("alt") or "").lower()

        class_name = " ".join(
            img.get("class", [])
        ).lower()

        image_name = (
            urlparse(image_url)
            .path
            .split("/")[-1]
            .lower()
        )

        combined = (
            alt + " "
            + class_name + " "
            + image_name
        )

        # ----------------------------------------
        # Skip obvious decorative images
        # ----------------------------------------

        if any(word in combined for word in skip_words):
            print("Skipping likely icon:", image_url)
            continue

        candidates.append(image_url)

    return candidates