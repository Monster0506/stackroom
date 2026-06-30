from django.contrib import admin
from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "isbn", "status", "rating", "date_added")
    list_filter = ("status", "rating")
    search_fields = ("title", "author", "isbn")
