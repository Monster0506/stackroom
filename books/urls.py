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
    path("api/move/", views.move_book, name="move_book"),
    path("cover/<int:pk>/", views.cover_image, name="cover_image"),
    path("cases/add/", views.bookcase_add, name="bookcase_add"),
    path("cases/<int:pk>/delete/", views.bookcase_delete, name="bookcase_delete"),
    path("cases/<int:pk>/shelves/add/", views.shelf_add, name="shelf_add"),
    path("shelves/<int:pk>/delete/", views.shelf_delete, name="shelf_delete"),
]
