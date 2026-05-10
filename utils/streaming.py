# ╔══════════════════════════════════════════════════╗
# ║    🔗 W H E R E  T O  W A T C H  /  R E A D     ║
# ║      Legal streaming + reading links system      ║
# ╚══════════════════════════════════════════════════╝

# ── ANIME STREAMING PLATFORMS ─────────────────────────────────────
# Format: { "Platform Name": ("base_search_url", "emoji", "free?") }

ANIME_PLATFORMS = {
    "Crunchyroll": (
        "https://www.crunchyroll.com/search?q=",
        "🟠", True,
        "Largest anime library, free with ads"
    ),
    "Netflix": (
        "https://www.netflix.com/search?q=",
        "🔴", False,
        "Premium only, exclusive titles"
    ),
    "HiDive": (
        "https://www.hidive.com/search#/",
        "🔵", True,
        "Niche & classic anime, free tier available"
    ),
    "Amazon Prime": (
        "https://www.amazon.com/s?k=",
        "🟡", False,
        "Prime subscription needed"
    ),
    "Funimation": (
        "https://www.funimation.com/search/?q=",
        "🟣", True,
        "Merging with Crunchyroll"
    ),
    "Bilibili": (
        "https://www.bilibili.tv/en/search?keyword=",
        "🩵", True,
        "Free, great for seasonal anime"
    ),
    "RetroCrush": (
        "https://retrocrush.tv/search?q=",
        "🟤", True,
        "100% free, classic anime only"
    ),
    "Tubi": (
        "https://tubitv.com/search/",
        "⚪", True,
        "Free with ads, limited library"
    ),
    "Muse Asia": (
        "https://www.youtube.com/@MuseAsia/search?query=",
        "🎬", True,
        "Free on YouTube, Asian content"
    ),
}

# ── MANGA / MANHWA READING PLATFORMS ──────────────────────────────

MANGA_PLATFORMS = {
    "MangaDex": (
        "https://mangadex.org/search?q=",
        "🟠", True,
        "Huge library, fan translations"
    ),
    "Webtoon": (
        "https://www.webtoons.com/en/search?keyword=",
        "🟦", True,
        "Official webtoons, free + coins system"
    ),
    "MangaPlus": (
        "https://mangaplus.shueisha.co.jp/search_result?word=",
        "🔴", True,
        "Official Shueisha — free first & last chapters"
    ),
    "Viz Media": (
        "https://www.viz.com/search?search=",
        "🔵", True,
        "Official English manga, free previews"
    ),
    "K Manga": (
        "https://kmanga.kodansha.com/search?word=",
        "🟣", True,
        "Official Kodansha platform"
    ),
    "Tapas": (
        "https://tapas.io/search?q=",
        "🟡", True,
        "Webtoons & novels, free + ink system"
    ),
    "Tappytoon": (
        "https://www.tappytoon.com/en/search?query=",
        "🩷", False,
        "Official manhwa, coins needed"
    ),
    "Lezhin Comics": (
        "https://www.lezhinus.com/en/search?q=",
        "⚫", False,
        "Premium manhwa including adult"
    ),
    "Pocket Comics": (
        "https://www.pocketcomics.com/search?q=",
        "🟤", True,
        "Free manhwa, official translations"
    ),
    "MangaFire": (
        "https://mangafire.to/filter?keyword=",
        "🔥", True,
        "Free manga reader"
    ),
}

# ── ADULT MANHWA PLATFORMS (18+) ───────────────────────────────────
# Only legal platforms that explicitly allow adult content

ADULT_PLATFORMS = {
    "Lezhin Comics": (
        "https://www.lezhinus.com/en/search?q=",
        "⚫", False,
        "Premium adult manhwa, official"
    ),
    "Toomics": (
        "https://toomics.com/en/search/q/",
        "🔞", False,
        "Adult webtoons, subscription"
    ),
    "MrBlue": (
        "https://www.mrblue.com/search?keyword=",
        "🟦", False,
        "Korean adult manhwa platform"
    ),
    "Bomtoon": (
        "https://www.bomtoon.com/search?keyword=",
        "💗", False,
        "BL & adult manhwa official"
    ),
}


# ╔══════════════════════════════════════════════════╗
# ║           LINK BUILDER FUNCTIONS                 ║
# ╚══════════════════════════════════════════════════╝

import urllib.parse

def build_anime_links(title: str) -> list[tuple]:
    """
    Returns list of (platform_name, emoji, url, free, description)
    for all anime streaming platforms.
    """
    encoded = urllib.parse.quote(title)
    links = []
    for name, (base, emoji, free, desc) in ANIME_PLATFORMS.items():
        links.append((name, emoji, base + encoded, free, desc))
    return links


def build_manga_links(title: str, is_adult: bool = False) -> list[tuple]:
    """
    Returns list of (platform_name, emoji, url, free, description)
    for reading platforms.
    """
    encoded = urllib.parse.quote(title)
    links   = []

    platforms = MANGA_PLATFORMS.copy()
    if is_adult:
        platforms.update(ADULT_PLATFORMS)

    for name, (base, emoji, free, desc) in platforms.items():
        links.append((name, emoji, base + encoded, free, desc))

    return links


def build_watch_caption(title: str) -> str:
    return (
        f"┏━━━❖ 📺 ❖━━━┓\n"
        f"  <b>Where to Watch</b>\n"
        f"┗━━━❖ 📺 ❖━━━┛\n\n"
        f"🎌 <b>{title}</b>\n\n"
        f"Neeche platforms pe legally stream karo~\n"
        f"🟢 = Free available  🔒 = Paid only\n\n"
        f"<i>Availability region ke hisaab se vary kar sakti hai.</i>"
    )


def build_read_caption(title: str, is_adult: bool = False) -> str:
    adult_note = "\n🔞 <b>Adult platforms bhi include hain.</b>" if is_adult else ""
    return (
        f"┏━━━❖ 📖 ❖━━━┓\n"
        f"  <b>Where to Read</b>\n"
        f"┗━━━❖ 📖 ❖━━━┛\n\n"
        f"📚 <b>{title}</b>\n\n"
        f"Neeche platforms pe legally padho~\n"
        f"🟢 = Free available  🔒 = Paid only"
        f"{adult_note}\n\n"
        f"<i>Fan translations ke liye MangaDex best hai.</i>"
    )


# ╔══════════════════════════════════════════════════╗
# ║           KEYBOARD BUILDERS                      ║
# ╚══════════════════════════════════════════════════╝

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def watch_links_kb(title: str, back_cb: str = "menu_main") -> InlineKeyboardMarkup:
    """Inline keyboard with all streaming platform buttons."""
    links   = build_anime_links(title)
    buttons = []

    # Free platforms first, 2 per row
    free_btns = []
    paid_btns = []

    for name, emoji, url, free, _ in links:
        label = f"{emoji} {name} {'🟢' if free else '🔒'}"
        btn   = InlineKeyboardButton(label, url=url)
        if free:
            free_btns.append(btn)
        else:
            paid_btns.append(btn)

    # Pair into rows of 2
    all_btns = free_btns + paid_btns
    for i in range(0, len(all_btns), 2):
        row = all_btns[i:i+2]
        buttons.append(row)

    buttons.append([InlineKeyboardButton("🔙 Back", callback_data=back_cb)])
    return InlineKeyboardMarkup(buttons)


def read_links_kb(title: str, is_adult: bool = False, back_cb: str = "mg_main") -> InlineKeyboardMarkup:
    """Inline keyboard with all reading platform buttons."""
    links   = build_manga_links(title, is_adult=is_adult)
    buttons = []

    free_btns = []
    paid_btns = []

    for name, emoji, url, free, _ in links:
        label = f"{emoji} {name} {'🟢' if free else '🔒'}"
        btn   = InlineKeyboardButton(label, url=url)
        if free:
            free_btns.append(btn)
        else:
            paid_btns.append(btn)

    all_btns = free_btns + paid_btns
    for i in range(0, len(all_btns), 2):
        row = all_btns[i:i+2]
        buttons.append(row)

    buttons.append([InlineKeyboardButton("🔙 Back", callback_data=back_cb)])
    return InlineKeyboardMarkup(buttons)
