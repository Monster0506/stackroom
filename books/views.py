from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Max, Prefetch
import json
import threading
import urllib.request
from pathlib import Path

from .models import Book, Bookcase, Shelf
from .lookup import lookup_isbn, lookup_title_author
from .search import fuzzy_search

COVERS_DIR = Path(settings.BASE_DIR) / "covers"


def _download_cover(pk, url):
    """Fetch a cover image and cache it to disk. Runs in a background thread."""
    COVERS_DIR.mkdir(exist_ok=True)
    dest = COVERS_DIR / f"{pk}.img"
    ct_dest = COVERS_DIR / f"{pk}.ct"
    if dest.exists():
        return
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = (
                resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
            )
            dest.write_bytes(resp.read())
            ct_dest.write_text(content_type)
    except Exception:
        pass


def library(request):
    q = request.GET.get("q", "").strip()

    if q:
        books = fuzzy_search(Book.objects.all(), q)
        context = {"q": q, "books": books}
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return render(request, "books/_search_results.html", context)
        return render(request, "books/library.html", context)

    bookcases = Bookcase.objects.annotate(
        book_count=Count("shelves__books")
    ).prefetch_related(
        Prefetch(
            "shelves",
            queryset=Shelf.objects.annotate(book_count=Count("books")).prefetch_related(
                "books"
            ),
        )
    )
    context = {"q": q, "bookcases": bookcases}
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render(request, "books/_bookcases.html", context)
    return render(request, "books/library.html", context)


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


def _next_position(queryset):
    """Position for a newly-appended row. Aggregate can legitimately return
    0 for the max, so this can't just fall back to a value with `or`."""
    current_max = queryset.aggregate(Max("position"))["position__max"]
    return 0 if current_max is None else current_max + 1


def _landing_shelf():
    """The shelf a newly added book lands on: the first empty shelf, in
    bookcase/shelf order, creating one if every existing shelf has books."""
    shelf = (
        Shelf.objects.annotate(book_count=Count("books"))
        .filter(book_count=0)
        .order_by("bookcase__position", "position")
        .first()
    )
    if shelf:
        return shelf

    case = Bookcase.objects.order_by("-position").first()
    if not case:
        case = Bookcase.objects.create(name="Case 1", position=0)

    next_shelf_position = _next_position(case.shelves)
    return Shelf.objects.create(
        bookcase=case,
        name=f"Shelf {case.shelves.count() + 1}",
        position=next_shelf_position,
    )


@require_POST
def save_book(request):
    data = json.loads(request.body)
    isbn = data.get("isbn", "").strip()

    # Avoid exact duplicates by ISBN
    if isbn and Book.objects.filter(isbn=isbn).exists():
        book = Book.objects.filter(isbn=isbn).first()
        messages.info(request, f'"{book.title}" is already in your library.')
        return JsonResponse({"id": book.pk, "duplicate": True})

    shelf = _landing_shelf()
    book = Book.objects.create(
        isbn=isbn,
        title=data.get("title", "Untitled"),
        author=data.get("author", ""),
        publisher=data.get("publisher", ""),
        published_date=data.get("published_date", ""),
        description=data.get("description", ""),
        cover_url=data.get("cover_url", ""),
        page_count=data.get("page_count") or None,
        shelf=shelf,
        position=0,
    )
    if book.cover_url:
        threading.Thread(
            target=_download_cover, args=(book.pk, book.cover_url), daemon=True
        ).start()
    return JsonResponse({"id": book.pk, "duplicate": False})


def cover_image(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if not book.cover_url:
        return HttpResponse(status=404)
    COVERS_DIR.mkdir(exist_ok=True)
    img_path = COVERS_DIR / f"{pk}.img"
    ct_path = COVERS_DIR / f"{pk}.ct"
    if not img_path.exists():
        _download_cover(pk, book.cover_url)
    if not img_path.exists():
        return redirect(book.cover_url)
    content_type = ct_path.read_text() if ct_path.exists() else "image/jpeg"
    return FileResponse(open(img_path, "rb"), content_type=content_type)


def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    return render(request, "books/detail.html", {"book": book})


@require_POST
def book_update(request, pk):
    book = get_object_or_404(Book, pk=pk)
    data = request.POST

    title = data.get("title", "").strip()
    if title:
        book.title = title
    book.author = data.get("author", book.author).strip()
    book.isbn = data.get("isbn", book.isbn).strip()
    book.publisher = data.get("publisher", book.publisher).strip()
    book.published_date = data.get("published_date", book.published_date).strip()
    page_count = data.get("page_count", "").strip()
    book.page_count = int(page_count) if page_count.isdigit() else None
    book.description = data.get("description", book.description).strip()

    book.rating = data.get("rating") or None
    book.notes = data.get("notes", book.notes)
    finished = data.get("date_finished", "")
    book.date_finished = finished if finished else None
    book.save()
    messages.success(request, "Book updated.")
    return redirect("book_detail", pk=pk)


@require_POST
def move_book(request):
    """Persist a drag-and-drop move: the book's new shelf, and the full
    ordered pk list for that shelf after the drop."""
    data = json.loads(request.body)
    book_pk = data.get("book")
    shelf_pk = data.get("shelf")
    order = data.get("order", [])
    with transaction.atomic():
        Book.objects.filter(pk=book_pk).update(shelf_id=shelf_pk)
        for position, pk in enumerate(order):
            Book.objects.filter(pk=pk).update(position=position)
    return JsonResponse({"ok": True})


@require_POST
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.delete()
    messages.success(request, "Book removed from library.")
    return redirect("library")


@require_POST
def bookcase_add(request):
    next_position = _next_position(Bookcase.objects)
    Bookcase.objects.create(
        name=f"Case {Bookcase.objects.count() + 1}", position=next_position
    )
    return redirect("library")


@require_POST
def bookcase_delete(request, pk):
    case = get_object_or_404(Bookcase, pk=pk)
    if Book.objects.filter(shelf__bookcase=case).exists():
        messages.error(
            request, f'"{case}" still has books on its shelves - move them first.'
        )
        return redirect("library")
    case.delete()
    messages.success(request, f'"{case}" removed.')
    return redirect("library")


@require_POST
def shelf_add(request, pk):
    case = get_object_or_404(Bookcase, pk=pk)
    next_position = _next_position(case.shelves)
    Shelf.objects.create(
        bookcase=case, name=f"Shelf {case.shelves.count() + 1}", position=next_position
    )
    return redirect("library")


@require_POST
def shelf_delete(request, pk):
    shelf = get_object_or_404(Shelf, pk=pk)
    if shelf.books.exists():
        messages.error(request, f'"{shelf}" still has books on it - move them first.')
        return redirect("library")
    shelf.delete()
    messages.success(request, f'"{shelf}" removed.')
    return redirect("library")
