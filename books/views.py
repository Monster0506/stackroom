from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
import json
import threading
import urllib.request
from pathlib import Path

from .models import Book
from .lookup import lookup_isbn, lookup_title_author

COVERS_DIR = Path(settings.BASE_DIR) / 'covers'


def _download_cover(pk, url):
    """Fetch a cover image and cache it to disk. Runs in a background thread."""
    COVERS_DIR.mkdir(exist_ok=True)
    dest = COVERS_DIR / f'{pk}.img'
    ct_dest = COVERS_DIR / f'{pk}.ct'
    if dest.exists():
        return
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get('Content-Type', 'image/jpeg').split(';')[0].strip()
            dest.write_bytes(resp.read())
            ct_dest.write_text(content_type)
    except Exception:
        pass


def library(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    books = Book.objects.all()
    if q:
        books = books.filter(Q(title__icontains=q) | Q(author__icontains=q) | Q(isbn__icontains=q))
    if status:
        books = books.filter(status=status)
    return render(request, "books/library.html", {
        "books": books,
        "q": q,
        "status_filter": status,
        "status_choices": Book.STATUS_CHOICES,
    })


def add_book(request):
    return render(request, "books/add.html")


@ensure_csrf_cookie
def scan(request):
    return render(request, "books/scan.html")


def api_lookup_isbn(request):
    isbn = request.GET.get("isbn", "").strip()
    if not isbn:
        return JsonResponse({"error": "No ISBN provided"}, status=400)
    data = lookup_isbn(isbn)
    if data:
        return JsonResponse({"result": data})
    return JsonResponse({"error": "Book not found"}, status=404)


def api_search(request):
    title = request.GET.get("title", "").strip()
    author = request.GET.get("author", "").strip()
    if not title:
        return JsonResponse({"error": "Title required"}, status=400)
    results = lookup_title_author(title, author)
    return JsonResponse({"results": results})


@require_POST
def save_book(request):
    data = json.loads(request.body)
    isbn = data.get("isbn", "").strip()

    # Avoid exact duplicates by ISBN
    if isbn and Book.objects.filter(isbn=isbn).exists():
        book = Book.objects.filter(isbn=isbn).first()
        messages.info(request, f'"{book.title}" is already in your library.')
        return JsonResponse({"id": book.pk, "duplicate": True})

    book = Book.objects.create(
        isbn=isbn,
        title=data.get("title", "Untitled"),
        author=data.get("author", ""),
        publisher=data.get("publisher", ""),
        published_date=data.get("published_date", ""),
        description=data.get("description", ""),
        cover_url=data.get("cover_url", ""),
        page_count=data.get("page_count") or None,
        status=data.get("status", "want"),
    )
    if book.cover_url:
        threading.Thread(target=_download_cover, args=(book.pk, book.cover_url), daemon=True).start()
    return JsonResponse({"id": book.pk, "duplicate": False})


def cover_image(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if not book.cover_url:
        return HttpResponse(status=404)
    COVERS_DIR.mkdir(exist_ok=True)
    img_path = COVERS_DIR / f'{pk}.img'
    ct_path  = COVERS_DIR / f'{pk}.ct'
    if not img_path.exists():
        _download_cover(pk, book.cover_url)
    if not img_path.exists():
        return redirect(book.cover_url)
    content_type = ct_path.read_text() if ct_path.exists() else 'image/jpeg'
    return FileResponse(open(img_path, 'rb'), content_type=content_type)


def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    return render(request, "books/detail.html", {"book": book, "status_choices": Book.STATUS_CHOICES})


@require_POST
def book_update(request, pk):
    book = get_object_or_404(Book, pk=pk)
    data = request.POST
    book.status = data.get("status", book.status)
    book.rating = data.get("rating") or None
    book.notes = data.get("notes", book.notes)
    finished = data.get("date_finished", "")
    book.date_finished = finished if finished else None
    book.save()
    messages.success(request, "Book updated.")
    return redirect("book_detail", pk=pk)


@require_POST
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.delete()
    messages.success(request, "Book removed from library.")
    return redirect("library")
