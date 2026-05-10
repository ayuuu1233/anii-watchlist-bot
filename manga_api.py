# ╔══════════════════════════════════════════════════╗
# ║      📚 M A N G A  A P I  U T I L I T Y         ║
# ║   AniList (manga) + MangaDex (manhwa/webtoon)   ║
# ╚══════════════════════════════════════════════════╝

import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)

ANILIST_URL  = "https://graphql.anilist.co"
MANGADEX_URL = "https://api.mangadex.org"

# ── MangaDex content ratings ──────────────────────
SAFE_RATINGS   = ["safe", "suggestive"]
ADULT_RATINGS  = ["erotica", "pornographic"]
ALL_RATINGS    = SAFE_RATINGS + ADULT_RATINGS


# ╔══════════════════════════════════════════════════╗
# ║              ANILIST — MANGA                     ║
# ╚══════════════════════════════════════════════════╝

ANILIST_MANGA_SEARCH = """
query($search:String,$page:Int,$isAdult:Boolean){
  Page(page:$page,perPage:10){
    media(
      search:$search,
      type:MANGA,
      isAdult:$isAdult,
      sort:SEARCH_MATCH
    ){
      id
      title{ romaji english native }
      coverImage{ large medium }
      bannerImage
      averageScore
      chapters
      volumes
      status
      countryOfOrigin
      genres
      description(asHtml:false)
      startDate{ year month day }
      staff{ edges{ role node{ name{ full } } } }
    }
  }
}
"""

ANILIST_MANGA_BY_ID = """
query($id:Int){
  Media(id:$id,type:MANGA){
    id
    title{ romaji english native }
    coverImage{ large medium }
    bannerImage
    averageScore
    popularity
    chapters
    volumes
    status
    countryOfOrigin
    genres
    description(asHtml:false)
    startDate{ year }
    staff{ edges{ role node{ name{ full } } } }
    tags{ name rank }
  }
}
"""

async def anilist_search_manga(query: str, is_adult: bool = False, page: int = 1):
    """Search AniList for manga/manhwa/manhua."""
    try:
        async with aiohttp.ClientSession() as s:
            r = await s.post(ANILIST_URL, json={
                "query": ANILIST_MANGA_SEARCH,
                "variables": {"search": query, "page": page, "isAdult": is_adult}
            }, timeout=aiohttp.ClientTimeout(total=10))
            d = await r.json()
            return d.get("data", {}).get("Page", {}).get("media", [])
    except Exception as e:
        logger.error(f"AniList manga search error: {e}")
        return []

async def anilist_get_manga(manga_id: int):
    """Get single manga details from AniList."""
    try:
        async with aiohttp.ClientSession() as s:
            r = await s.post(ANILIST_URL, json={
                "query": ANILIST_MANGA_BY_ID,
                "variables": {"id": manga_id}
            }, timeout=aiohttp.ClientTimeout(total=10))
            d = await r.json()
            return d.get("data", {}).get("Media")
    except Exception as e:
        logger.error(f"AniList manga fetch error: {e}")
        return None


# ╔══════════════════════════════════════════════════╗
# ║            MANGADEX — SEARCH                     ║
# ╚══════════════════════════════════════════════════╝

async def mangadex_search(
    query: str,
    content_type: str = "safe",   # "safe" | "adult"
    manga_type: str = "all",      # "all" | "manhwa" | "webtoon" | "manga"
    limit: int = 10,
    offset: int = 0,
):
    """Search MangaDex with filters for type and content rating."""

    ratings = ADULT_RATINGS if content_type == "adult" else SAFE_RATINGS

    params = {
        "title": query,
        "limit": limit,
        "offset": offset,
        "contentRating[]": ratings,
        "includes[]": ["cover_art", "author", "artist"],
        "order[relevance]": "desc",
    }

    # Filter by origin country / format
    if manga_type == "manhwa":
        params["originalLanguage[]"] = ["ko"]
    elif manga_type == "manga":
        params["originalLanguage[]"] = ["ja"]
    elif manga_type == "manhua":
        params["originalLanguage[]"] = ["zh", "zh-hk"]
    elif manga_type == "webtoon":
        params["originalLanguage[]"] = ["ko"]
        params["publicationDemographic[]"] = ["none"]

    try:
        async with aiohttp.ClientSession() as s:
            r = await s.get(
                f"{MANGADEX_URL}/manga",
                params=params,
                timeout=aiohttp.ClientTimeout(total=12)
            )
            d = await r.json()
            return _parse_mangadex_results(d.get("data", []))
    except Exception as e:
        logger.error(f"MangaDex search error: {e}")
        return []


async def mangadex_get(manga_id: str):
    """Get full details of a MangaDex manga by UUID."""
    try:
        async with aiohttp.ClientSession() as s:
            r = await s.get(
                f"{MANGADEX_URL}/manga/{manga_id}",
                params={"includes[]": ["cover_art", "author", "artist"]},
                timeout=aiohttp.ClientTimeout(total=10)
            )
            d = await r.json()
            items = _parse_mangadex_results([d.get("data", {})])
            return items[0] if items else None
    except Exception as e:
        logger.error(f"MangaDex fetch error: {e}")
        return None


def _parse_mangadex_results(raw: list) -> list:
    """Normalize MangaDex response into clean dicts."""
    results = []
    for item in raw:
        if not item:
            continue
        attrs = item.get("attributes", {})
        rels  = item.get("relationships", [])

        # Title
        titles = attrs.get("title", {})
        title  = titles.get("en") or next(iter(titles.values()), "Unknown")

        # Cover image
        cover_rel = next((r for r in rels if r["type"] == "cover_art"), None)
        cover_url = ""
        if cover_rel:
            fname    = cover_rel.get("attributes", {}).get("fileName", "")
            manga_id = item.get("id", "")
            if fname:
                cover_url = f"https://uploads.mangadex.org/covers/{manga_id}/{fname}.256.jpg"

        # Author
        author_rel = next((r for r in rels if r["type"] == "author"), None)
        author = ""
        if author_rel:
            author = author_rel.get("attributes", {}).get("name", "")

        # Description
        desc_map = attrs.get("description", {})
        desc     = desc_map.get("en") or next(iter(desc_map.values()), "")

        # Genres / tags
        tags = [
            t.get("attributes", {}).get("name", {}).get("en", "")
            for t in attrs.get("tags", [])
            if t.get("attributes", {}).get("name", {}).get("en")
        ]

        results.append({
            "source":          "mangadex",
            "id":              item.get("id", ""),
            "title":           title,
            "cover_url":       cover_url,
            "status":          attrs.get("status", "unknown").title(),
            "chapters":        attrs.get("lastChapter") or "?",
            "content_rating":  attrs.get("contentRating", "safe"),
            "origin":          attrs.get("originalLanguage", ""),
            "year":            attrs.get("year") or "?",
            "genres":          tags[:6],
            "description":     desc[:400] if desc else "No description.",
            "author":          author,
        })
    return results


# ╔══════════════════════════════════════════════════╗
# ║           COMBINED SEARCH                        ║
# ╚══════════════════════════════════════════════════╝

async def combined_search(query: str, content_type: str = "safe", manga_type: str = "all"):
    """
    Run AniList + MangaDex in parallel and merge results.
    AniList first (better metadata), MangaDex fills the rest.
    """
    is_adult = content_type == "adult"

    al_task = anilist_search_manga(query, is_adult=is_adult)
    md_task = mangadex_search(query, content_type=content_type, manga_type=manga_type, limit=8)

    al_results_raw, md_results = await asyncio.gather(al_task, md_task)

    # Normalize AniList results to same schema
    al_results = []
    for a in al_results_raw:
        al_results.append({
            "source":         "anilist",
            "id":             str(a["id"]),
            "title":          a["title"].get("english") or a["title"].get("romaji", "?"),
            "cover_url":      a["coverImage"].get("large") or a["coverImage"].get("medium", ""),
            "status":         a.get("status", "").replace("_", " ").title(),
            "chapters":       a.get("chapters") or "?",
            "content_rating": "erotica" if is_adult else "safe",
            "origin":         a.get("countryOfOrigin", ""),
            "year":           a.get("startDate", {}).get("year") or "?",
            "genres":         a.get("genres", [])[:5],
            "description":    (a.get("description") or "")[:400],
            "author":         "",
            "score":          a.get("averageScore"),
            "volumes":        a.get("volumes"),
            "al_id":          a["id"],
        })

    # Merge — AniList first, then MangaDex (deduplicate by title similarity)
    seen_titles = {r["title"].lower()[:20] for r in al_results}
    for m in md_results:
        if m["title"].lower()[:20] not in seen_titles:
            al_results.append(m)
            seen_titles.add(m["title"].lower()[:20])

    return al_results[:12]


# ╔══════════════════════════════════════════════════╗
# ║             CAPTION BUILDERS                     ║
# ╚══════════════════════════════════════════════════╝

ORIGIN_FLAG = {
    "JP": "🇯🇵 Manga",
    "KR": "🇰🇷 Manhwa",
    "CN": "🇨🇳 Manhua",
    "zh": "🇨🇳 Manhua",
    "ko": "🇰🇷 Manhwa",
    "ja": "🇯🇵 Manga",
}

def get_type_label(origin: str) -> str:
    return ORIGIN_FLAG.get(origin, "📚 Manga")

def build_manga_list_caption(query: str, results: list) -> str:
    text = (
        f"┏━━━❖ 📚 ❖━━━┓\n"
        f"  <b>Results for '{query}'</b>\n"
        f"┗━━━❖ 📚 ❖━━━┛\n\n"
    )
    for i, r in enumerate(results[:10], 1):
        label   = get_type_label(r.get("origin", ""))
        score   = f" ★{r['score']/10:.1f}" if r.get("score") else ""
        ch      = r.get("chapters") or "?"
        adult   = " 🔞" if r.get("content_rating") in ADULT_RATINGS else ""
        title   = r["title"][:35]
        text   += f"{i}. {label}  <b>{title}</b>{score}  📖{ch}ch{adult}\n"
    text += "\n👇 <i>Select one for full details~</i>"
    return text


def build_manga_detail_caption(r: dict) -> str:
    label   = get_type_label(r.get("origin", ""))
    score   = f"{r['score']/10:.1f}/10" if r.get("score") else "N/A"
    ch      = r.get("chapters") or "?"
    vol     = r.get("volumes") or "?"
    genres  = " · ".join(r.get("genres", [])[:4]) or "N/A"
    desc    = r.get("description", "")[:300]
    author  = r.get("author", "") or "N/A"
    adult   = "\n🔞 <b>Adult Content</b>" if r.get("content_rating") in ADULT_RATINGS else ""
    src     = "AniList" if r.get("source") == "anilist" else "MangaDex"

    return (
        f"┏━━━❖ 📚 ❖━━━┓\n"
        f"  <b>{r['title']}</b>\n"
        f"┗━━━❖ 📚 ❖━━━┛\n\n"
        f"{label}{adult}\n\n"
        f"⭐ Score    : <b>{score}</b>\n"
        f"📖 Chapters : <b>{ch}</b>\n"
        f"📦 Volumes  : <b>{vol}</b>\n"
        f"📡 Status   : <b>{r.get('status','?')}</b>\n"
        f"🗓️ Year     : <b>{r.get('year','?')}</b>\n"
        f"✍️ Author   : <b>{author}</b>\n"
        f"🎭 Genres   : {genres}\n\n"
        f"📖 {desc}\n\n"
        f"<i>Source: {src}</i>"
  )
