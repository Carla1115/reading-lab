
from django.contrib import admin
from .models import Book, UserBook


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "goodreads_id",
        "title",
        "author",
        "publication_year",
    )

    search_fields = ("title", "author")

@admin.register(UserBook)
class UserBookAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "book",
        "shelf",
        "rating",
        "date_read",
    )

    list_filter = ("shelf", "rating")
    search_fields = ("book__title", "user__username")
