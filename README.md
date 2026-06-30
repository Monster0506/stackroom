# Booktracker

A personal book catalog built with Django. Scan a barcode or search by title, pull in cover art and metadata automatically, and browse your collection on a searchable bookshelf.

## Features

- Add books by scanning an ISBN barcode or searching by title/author
- Automatic metadata lookup via Open Library and Google Books
- Cover images are cached locally after a book is added
- Optional rating, notes, and date finished on each book
- Search your library by title, author, or ISBN

## Setup

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
uv sync
uv run manage.py migrate
uv run manage.py runserver
```

Then visit `http://localhost:8000`.

## Configuration

Copy `.env` and set `GOOGLE_BOOKS_API_KEY` if you want higher-volume lookups via the Google Books API. Open Library lookups work without any key.
