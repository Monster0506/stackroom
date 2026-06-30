from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import urllib.request
import urllib.error

from books.models import Book

COVERS_DIR = Path(settings.BASE_DIR) / "covers"


class Command(BaseCommand):
    help = "Download and cache cover images for all books that have a cover_url"

    def handle(self, *args, **options):
        COVERS_DIR.mkdir(exist_ok=True)
        books = Book.objects.exclude(cover_url="")
        total = books.count()
        self.stdout.write(f"Caching covers for {total} books...")

        ok = skip = fail = 0
        for book in books:
            dest = COVERS_DIR / f"{book.pk}.img"
            ct_dest = COVERS_DIR / f"{book.pk}.ct"
            if dest.exists():
                skip += 1
                continue
            try:
                req = urllib.request.Request(
                    book.cover_url,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    ct = (
                        resp.headers.get("Content-Type", "image/jpeg")
                        .split(";")[0]
                        .strip()
                    )
                    dest.write_bytes(resp.read())
                    ct_dest.write_text(ct)
                ok += 1
                self.stdout.write(f"  [{ok+skip}/{total}] {book.title[:50]}")
            except Exception as e:
                fail += 1
                self.stdout.write(self.style.WARNING(f"  FAIL {book.pk}: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {ok} downloaded, {skip} already cached, {fail} failed."
            )
        )
