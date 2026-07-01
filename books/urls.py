from django.urls import path
from . import views

urlpatterns = [
    path("", views.library, name="library"),
    path("add/", views.add_book, name="add_book"),
    path("scan/", views.scan, name="scan"),
    path("book/<int:pk>/", views.book_detail, name="book_detail"),
    path("book/<int:pk>/update/", views.book_update, name="book_update"),
    path("book/<int:pk>/delete/", views.book_delete, name="book_delete"),
    path("api/isbn/", views.api_lookup_isbn, name="api_lookup_isbn"),
    path("api/search/", views.api_search, name="api_search"),
    path("api/save/", views.save_book, name="save_book"),
    path("api/reorder/", views.reorder_books, name="reorder_books"),
    path("cover/<int:pk>/", views.cover_image, name="cover_image"),
]
