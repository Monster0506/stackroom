from django.contrib import admin
from .models import Book, Bookcase, Shelf


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "isbn", "shelf", "rating", "date_added")
    list_filter = ("rating", "shelf__bookcase")
    search_fields = ("title", "author", "isbn")


@admin.register(Bookcase)
class BookcaseAdmin(admin.ModelAdmin):
    list_display = ("name", "position")


@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ("name", "bookcase", "position")
    list_filter = ("bookcase",)
