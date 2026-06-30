import os
import requests
from django.conf import settings

OPENLIBRARY_ISBN = (
    "https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
)
OPENLIBRARY_SEARCH = "https://openlibrary.org/search.json"
OPENLIBRARY_WORKS = "https://openlibrary.org/search.json?isbn={isbn}"
GOOGLE_BOOKS = "https://www.googleapis.com/books/v1/volumes"

HEADERS = {"User-Agent": "booktracker/1.0 (personal book tracker)"}


def _google_params(extra: dict) -> dict:
    params = dict(extra)
    key = getattr(settings, "GOOGLE_BOOKS_API_KEY", "") or os.environ.get(
        "GOOGLE_BOOKS_API_KEY", ""
    )
    if key:
        params["key"] = key
    return params


def _ol_cover(cover_dict):
    for size in ("large", "medium", "small"):
        if url := cover_dict.get(size):
            return url
    return ""


def _ean13_to_isbn10(ean13: str) -> str | None:
    if len(ean13) != 13 or not ean13.startswith("978"):
        return None
    core = ean13[3:12]
    total = sum((10 - i) * int(d) for i, d in enumerate(core))
    check = (11 - total % 11) % 11
    return core + ("X" if check == 10 else str(check))


def lookup_isbn(isbn: str) -> dict | None:
    isbn = isbn.replace("-", "").replace(" ", "")
    candidates = [isbn]
    if len(isbn) == 13:
        isbn10 = _ean13_to_isbn10(isbn)
        if isbn10:
            candidates.append(isbn10)

    # 1. Open Library books API (exact match)
    for candidate in candidates:
        try:
            resp = requests.get(
                OPENLIBRARY_ISBN.format(isbn=candidate), headers=HEADERS, timeout=6
            )
            data = resp.json()
            key = f"ISBN:{candidate}"
            if key in data:
                book = data[key]
                authors = ", ".join(a["name"] for a in book.get("authors", []))
                publishers = ", ".join(p["name"] for p in book.get("publishers", []))
                return {
                    "isbn": candidate,
                    "title": book.get("title", ""),
                    "author": authors,
                    "publisher": publishers,
                    "published_date": book.get("publish_date", ""),
                    "description": (
                        book.get("notes", "")
                        if isinstance(book.get("notes"), str)
                        else ""
                    ),
                    "cover_url": _ol_cover(book.get("cover", {})),
                    "page_count": book.get("number_of_pages"),
                }
        except Exception:
            pass

    for candidate in candidates:
        for params in [
            {"isbn": candidate, "limit": 1},
            {"q": f"isbn:{candidate}", "limit": 1},
        ]:
            try:
                resp = requests.get(
                    OPENLIBRARY_SEARCH, params=params, headers=HEADERS, timeout=6
                )
                docs = resp.json().get("docs", [])
                if docs:
                    doc = docs[0]
                    cover = (
                        f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg"
                        if doc.get("cover_i")
                        else ""
                    )
                    return {
                        "isbn": candidate,
                        "title": doc.get("title", ""),
                        "author": ", ".join(doc.get("author_name", [])),
                        "publisher": ", ".join((doc.get("publisher") or [])[:2]),
                        "published_date": str(doc.get("first_publish_year", "")),
                        "description": "",
                        "cover_url": cover,
                        "page_count": doc.get("number_of_pages_median"),
                    }
            except Exception:
                pass

    # 3. Google Books (works well when API key is set)
    for candidate in candidates:
        try:
            params = _google_params({"q": f"isbn:{candidate}"})
            resp = requests.get(GOOGLE_BOOKS, params=params, headers=HEADERS, timeout=6)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    return _parse_google(items[0], candidate)
        except Exception:
            pass

    return None


def lookup_title_author(title: str, author: str = "") -> list[dict]:
    results = []
    query = title
    if author:
        query += f" {author}"

    # Google Books
    try:
        params = _google_params({"q": query, "maxResults": 10})
        resp = requests.get(GOOGLE_BOOKS, params=params, headers=HEADERS, timeout=6)
        if resp.status_code == 200:
            for item in resp.json().get("items", []):
                results.append(_parse_google(item))
    except Exception:
        pass

    try:
        params = {"title": title, "limit": 10}
        if author:
            params["author"] = author
        resp = requests.get(
            OPENLIBRARY_SEARCH, params=params, headers=HEADERS, timeout=6
        )
        for doc in resp.json().get("docs", [])[:10]:
            results.append(
                {
                    "isbn": (doc.get("isbn") or [""])[0],
                    "title": doc.get("title", ""),
                    "author": ", ".join(doc.get("author_name", [])),
                    "publisher": ", ".join((doc.get("publisher") or [])[:2]),
                    "published_date": str(doc.get("first_publish_year", "")),
                    "description": "",
                    "cover_url": (
                        f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-M.jpg"
                        if doc.get("cover_i")
                        else ""
                    ),
                    "page_count": doc.get("number_of_pages_median"),
                }
            )
    except Exception:
        pass

    return results


def _parse_google(item: dict, isbn: str = "") -> dict:
    info = item.get("volumeInfo", {})
    idents = {i["type"]: i["identifier"] for i in info.get("industryIdentifiers", [])}
    resolved_isbn = isbn or idents.get("ISBN_13") or idents.get("ISBN_10") or ""
    images = info.get("imageLinks", {})
    cover = images.get("thumbnail") or images.get("smallThumbnail") or ""
    if cover:
        cover = cover.replace("http://", "https://")
    return {
        "isbn": resolved_isbn,
        "title": info.get("title", ""),
        "author": ", ".join(info.get("authors", [])),
        "publisher": info.get("publisher", ""),
        "published_date": info.get("publishedDate", ""),
        "description": info.get("description", ""),
        "cover_url": cover,
        "page_count": info.get("pageCount"),
    }
