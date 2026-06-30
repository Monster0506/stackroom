from django.db import models


class Book(models.Model):
    STATUS_CHOICES = [
        ("want", "Want to Read"),
        ("reading", "Currently Reading"),
        ("read", "Read"),
    ]

    isbn = models.CharField(max_length=20, blank=True, db_index=True)
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=300, blank=True)
    publisher = models.CharField(max_length=300, blank=True)
    published_date = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    cover_url = models.URLField(max_length=1000, blank=True)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="want")
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_finished = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_added"]

    def __str__(self):
        return f"{self.title} — {self.author}"

    @property
    def stars(self):
        if self.rating:
            return "★" * self.rating + "☆" * (5 - self.rating)
        return ""
