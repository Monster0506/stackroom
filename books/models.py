from django.db import models


class Bookcase(models.Model):
    name = models.CharField(max_length=200, blank=True)
    position = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return self.name or f"Case {self.pk}"


class Shelf(models.Model):
    bookcase = models.ForeignKey(
        Bookcase, related_name="shelves", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200, blank=True)
    position = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return self.name or f"Shelf {self.pk}"


class Book(models.Model):
    isbn = models.CharField(max_length=20, blank=True, db_index=True)
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=300, blank=True)
    publisher = models.CharField(max_length=300, blank=True)
    published_date = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    cover_url = models.URLField(max_length=1000, blank=True)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_finished = models.DateField(null=True, blank=True)
    shelf = models.ForeignKey(Shelf, related_name="books", on_delete=models.PROTECT)
    position = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["position", "-date_added"]

    def __str__(self):
        return f"{self.title}: {self.author}"

    @property
    def stars(self):
        if self.rating:
            return "★" * self.rating + "☆" * (5 - self.rating)
        return ""
