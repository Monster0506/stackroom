from difflib import SequenceMatcher

FUZZY_THRESHOLD = 0.55

# Weight title/author/isbn matches above description hits, so an incidental
# word match buried in a description can't outrank an actual title match.
FIELD_WEIGHTS = {
    "title": 1.0,
    "author": 0.95,
    "isbn": 0.9,
    "description": 0.75,
}


def _ratio(a, b):
    return SequenceMatcher(None, a, b).ratio()


def _field_score(query, field):
    if not field:
        return 0.0
    field = field.lower()
    if query in field:
        return 1.0
    best = _ratio(query, field)
    for word in field.split():
        best = max(best, _ratio(query, word))
    return best


def fuzzy_score(book, query):
    return max(
        _field_score(query, book.title) * FIELD_WEIGHTS["title"],
        _field_score(query, book.author) * FIELD_WEIGHTS["author"],
        _field_score(query, book.isbn) * FIELD_WEIGHTS["isbn"],
        _field_score(query, book.description) * FIELD_WEIGHTS["description"],
    )


def fuzzy_search(books, query):
    query = query.lower().strip()
    scored = ((fuzzy_score(book, query), book) for book in books)
    matches = [(score, book) for score, book in scored if score >= FUZZY_THRESHOLD]
    matches.sort(key=lambda pair: pair[0], reverse=True)
    return [book for _, book in matches]
