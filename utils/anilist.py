import aiohttp
from config import ANILIST_URL

SEARCH_QUERY = """
query ($search: String, $page: Int) {
  Page(page: $page, perPage: 8) {
    media(search: $search, type: ANIME, sort: SEARCH_MATCH) {
      id
      title { romaji english native }
      episodes
      status
      averageScore
      coverImage { medium large }
      description(asHtml: false)
      genres
      season
      seasonYear
    }
  }
}
"""

ANIME_BY_ID_QUERY = """
query ($id: Int) {
  Media(id: $id, type: ANIME) {
    id
    title { romaji english native }
    episodes
    status
    averageScore
    coverImage { medium large }
    description(asHtml: false)
    genres
    season
    seasonYear
    nextAiringEpisode { episode airingAt }
  }
}
"""

async def search_anime(query: str, page: int = 1):
    """Search AniList for anime. Returns list of results."""
    async with aiohttp.ClientSession() as session:
        resp = await session.post(ANILIST_URL, json={
            "query": SEARCH_QUERY,
            "variables": {"search": query, "page": page}
        })
        data = await resp.json()
        return data.get("data", {}).get("Page", {}).get("media", [])

async def get_anime_by_id(anime_id: int):
    """Fetch single anime details by AniList ID."""
    async with aiohttp.ClientSession() as session:
        resp = await session.post(ANILIST_URL, json={
            "query": ANIME_BY_ID_QUERY,
            "variables": {"id": anime_id}
        })
        data = await resp.json()
        return data.get("data", {}).get("Media")

def format_anime_info(anime: dict) -> str:
    """Format anime dict to a nice text block."""
    title    = anime["title"].get("english") or anime["title"].get("romaji","?")
    romaji   = anime["title"].get("romaji","")
    eps      = anime.get("episodes") or "?"
    score    = anime.get("averageScore") or "N/A"
    status   = anime.get("status","").replace("_"," ").title()
    genres   = ", ".join(anime.get("genres",[])[:4]) or "N/A"
    desc_raw = anime.get("description") or ""
    desc     = desc_raw[:200].replace("<br>","").replace("\n"," ") + ("…" if len(desc_raw)>200 else "")
    season   = f"{anime.get('season','').title()} {anime.get('seasonYear','')}" if anime.get("season") else "N/A"

    return (
        f"🎌 <b>{title}</b>\n"
        f"<i>{romaji}</i>\n\n"
        f"📺 Episodes : <b>{eps}</b>\n"
        f"⭐ Score    : <b>{score}/100</b>\n"
        f"📡 Status   : <b>{status}</b>\n"
        f"🗓️ Season   : <b>{season}</b>\n"
        f"🎭 Genres   : {genres}\n\n"
        f"📖 {desc}"
  )
