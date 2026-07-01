from django.db import migrations
from django.db.models import F

# A reference row width matching the app's narrow, phone-width layout
# (max-w-2xl minus its padding), used only to decide where a shelf's
# books currently wrap into a new visual row.
AVAILABLE_WIDTH = 590
GAP = 4


def _spine_width(pk, page_count, title):
    if page_count:
        if page_count < 100:
            return 14
        if page_count < 200:
            return 18
        if page_count < 350:
            return 24
        if page_count < 550:
            return 32
        return 42
    return 14 + (pk * 5 + len(title or "") * 3) % 20


def _pack_into_rows(books):
    rows, row, row_width = [], [], 0
    for book in books:
        width = _spine_width(book.pk, book.page_count, book.title)
        needed = row_width + GAP + width if row else width
        if row and needed > AVAILABLE_WIDTH:
            rows.append(row)
            row, row_width = [book], width
        else:
            row.append(book)
            row_width = needed
    if row:
        rows.append(row)
    return rows


def split_shelves_into_rows(apps, schema_editor):
    Shelf = apps.get_model("books", "Shelf")
    Bookcase = apps.get_model("books", "Bookcase")

    for shelf in list(Shelf.objects.all()):
        shelf.refresh_from_db()
        books = list(shelf.books.order_by("position"))
        if not books:
            continue

        rows = _pack_into_rows(books)
        if len(rows) <= 1:
            continue

        case = shelf.bookcase
        Shelf.objects.filter(bookcase=case, position__gt=shelf.position).update(
            position=F("position") + (len(rows) - 1)
        )

        for i, row_books in enumerate(rows):
            target = (
                shelf
                if i == 0
                else Shelf.objects.create(
                    bookcase=case, name="", position=shelf.position + i
                )
            )
            for position, book in enumerate(row_books):
                book.shelf = target
                book.position = position
                book.save(update_fields=["shelf", "position"])

    for case in Bookcase.objects.all():
        for i, shelf in enumerate(case.shelves.order_by("position")):
            shelf.name = f"Shelf {i + 1}"
            shelf.save(update_fields=["name"])


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0004_bookcase_shelf"),
    ]

    operations = [
        migrations.RunPython(split_shelves_into_rows, migrations.RunPython.noop),
    ]
