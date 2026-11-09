import csv
from collections import Counter
from pathlib import Path
from statistics import mean, median

from django.conf import settings
from django.shortcuts import render

from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods


from django.contrib.auth import login, logout
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST


import io
from datetime import datetime

from django.db import transaction
from .models import Book, UserBook


from django.db.models import Q
from django.shortcuts import get_object_or_404

from django.shortcuts import get_object_or_404

from django.core.cache import cache
from django.utils.crypto import salted_hmac



CSV_FILE = Path(settings.BASE_DIR) / 'private_data' / 'goodreads_library_export.csv'


def as_num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_books():
    if not CSV_FILE.exists():
        return []
    with CSV_FILE.open(encoding='utf-8-sig', newline='') as handle:
        records = list(csv.DictReader(handle))
    books = []
    for row in records:
        rating = as_num(row.get('My Rating')) or 0
        books.append({
            'title': row.get('Title', '').strip(),
            'author': row.get('Author', '').strip(),
            'shelf': row.get('Exclusive Shelf', '').strip(),
            'pages': as_num(row.get('Number of Pages')),
            'year': as_num(row.get('Original Publication Year')),
            'rating': rating,
        })
    return books


def median_of(books, field):
    values = [x[field] for x in books if x[field] is not None]
    return median(values) if values else None


REQUIRED_COLUMNS = {
    "Title",
    "Author",
    "Exclusive Shelf",
    "My Rating",
    "Number of Pages",
    "Original Publication Year",
}


def parse_goodreads_date(value):
    if not value:
        return None

    value = value.strip()

    for date_format in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(
                value, date_format
            ).date()
        except ValueError:
            continue

    return None



@login_required
@require_http_methods(["GET", "POST"])
def upload_csv(request):
    if request.method == "GET":
        return render(request, "analytics/upload.html")

    uploaded_file = request.FILES.get("csv_file")

    if not uploaded_file:
        return render(request, "analytics/upload.html", {
            "error": "Please select a CSV file."
        })

    if not uploaded_file.name.lower().endswith(".csv"):
        return render(request, "analytics/upload.html", {
            "error": "The file must be a CSV."
        })

    if uploaded_file.size > 2 * 1024 * 1024:
        return render(request, "analytics/upload.html", {
            "error": "Maximum file size is 2 MB."
        })

    required_columns = {
        "Book Id",
        "Title",
        "Author",
        "Exclusive Shelf",
        "My Rating",
        "Number of Pages",
        "Original Publication Year",
    }

    try:
        content = uploaded_file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        if not reader.fieldnames:
            raise ValueError("Missing CSV headers.")

        if not required_columns.issubset(reader.fieldnames):
            raise ValueError("Invalid Goodreads CSV format.")

        records = []
        seen_ids = set()

        for row in reader:
            book_id = (row.get("Book Id") or "").strip()

            if not book_id:
                raise ValueError("A book has no Goodreads ID.")

            if book_id in seen_ids:
                continue

            seen_ids.add(book_id)


            rating_value = float(row.get("My Rating") or 0)

            if not rating_value.is_integer():
                raise ValueError("Rating must be a whole number.")

            rating = int(rating_value)


            if not 0 <= rating <= 5:
                raise ValueError("Invalid book rating.")

            def optional_int(value):
                value = (value or "").strip()
                return int(value) if value else None

            pages = optional_int(row.get("Number of Pages"))
            year = optional_int(
                row.get("Original Publication Year")
            )

            if pages is not None and pages < 0:
                raise ValueError("Invalid page count.")

            records.append({
                "id": book_id,
                "title": (row.get("Title") or "").strip(),
                "author": (row.get("Author") or "").strip(),
                "pages": pages,
                "year": year,
                "shelf": (row.get("Exclusive Shelf") or "").strip(),
                "rating": rating,
                "date_added": parse_goodreads_date(
                    row.get("Date Added")
                ),
                "date_read": parse_goodreads_date(
                    row.get("Date Read")
                ),
                "notes": (row.get("Private Notes") or "").strip(),
            })

            if len(records) > 5000:
                raise ValueError("Maximum 5000 books allowed.")

        if not records:
            raise ValueError("The CSV contains no books.")

        # Save all changes together.
        with transaction.atomic():

            # Replace only the current user's library.
            UserBook.objects.filter(
                user=request.user
            ).delete()

            for record in records:
                book, created = Book.objects.get_or_create(
                    goodreads_id=record["id"],
                    defaults={
                        "title": record["title"],
                        "author": record["author"],
                        "number_of_pages": record["pages"],
                        "publication_year": record["year"],
                    }
                )

                UserBook.objects.create(
                    user=request.user,
                    book=book,
                    shelf=record["shelf"],
                    rating=record["rating"],
                    date_added=record["date_added"],
                    date_read=record["date_read"],
                    private_notes=record["notes"],
                )

    except (UnicodeDecodeError, ValueError, csv.Error):
        return render(request, "analytics/upload.html", {
            "error": "Unable to import the Goodreads CSV."
        })

    # Remove temporary data from the previous implementation.
    request.session.pop("books", None)

    return redirect("dashboard")



def load_user_books(user):
    user_books = UserBook.objects.filter(
        user=user
    ).select_related("book")

    books = []

    for item in user_books:
        books.append({
            "title": item.book.title,
            "author": item.book.author,
            "shelf": item.shelf,
            "pages": item.book.number_of_pages,
            "year": item.book.publication_year,
            "rating": item.rating,
        })

    return books


@login_required
def dashboard(request):
    books = load_user_books(request.user)
    if not books:
        return redirect("upload")
    read = [b for b in books if b['shelf'] == 'read']
    pending = [b for b in books if b['shelf'] == 'to-read']
    rated = [b for b in read if b['rating'] > 0]
    favorites = [b for b in rated if b['rating'] >= 4]
    ref = favorites or rated
    ref_pages = median_of(ref, 'pages')
    ref_year = median_of(ref, 'year')

    # An intentionally simple, transparent similarity heuristic, not ML.
    recommendations = []
    if ref_pages is not None and ref_year is not None:
        for b in pending:
            if b['pages'] is None or b['year'] is None:
                continue
            page_similarity = max(0, 1 - abs(b['pages'] - ref_pages) / 500)
            year_similarity = max(0, 1 - abs(b['year'] - ref_year) / 80)
            score = round(100 * (0.55 * page_similarity + 0.45 * year_similarity))
            recommendations.append({**b, 'score': score})
        recommendations.sort(key=lambda b: (-b['score'], b['title']))

    page_median_read = median_of(read, 'pages')
    page_median_pending = median_of(pending, 'pages')
    year_median_read = median_of(read, 'year')
    year_median_pending = median_of(pending, 'year')
    spread = Counter(int(b['rating']) for b in rated)
    max_spread = max(spread.values(), default=1)
    rating_bars = [
        {'stars': stars, 'count': spread[stars], 'width': round(spread[stars] / max_spread * 100)}
        for stars in range(1, 6)
    ]
    context = {
        'has_data': bool(books),
        'book_count': len(books),
        'read_count': len(read),
        'pending_count': len(pending),
        'rated_count': len(rated),
        'favorite_count': len(favorites),
        'median_read_pages': page_median_read,
        'median_pending_pages': page_median_pending,
        'median_read_year': year_median_read,
        'median_pending_year': year_median_pending,
        'rating_bars': rating_bars,
        'recommendations': recommendations[:5],
        'reference_pages': ref_pages,
        'reference_year': ref_year,
    }
    return render(request, 'analytics/dashboard.html', context)



def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("upload")
    else:
        form = UserCreationForm()

    return render(request, "analytics/register.html", {
        "form": form
    })






def login_view(request):
    # FLAW 3 - A07:2021 Identification and Authentication Failures

    # VULNERABLE CODE:
    # The application does not limit failed login attempts.
    # Attackers can repeatedly try different passwords.

    if request.user.is_authenticated:
        if UserBook.objects.filter(user=request.user).exists():
            return redirect("dashboard")
        return redirect("upload")

    # TO ACTIVATE THE FIX:
    # 1. Comment out the vulnerable POST/else block below.
    # 2. Uncomment the complete rate-limiting FIX block.
    # 3. Add "error_message": error_message to the render context.
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            login(request, form.get_user())

            if UserBook.objects.filter(user=request.user).exists():
                return redirect("dashboard")

            return redirect("upload")
    else:
        form = AuthenticationForm(request)

    # FIX: Limit failed login attempts using Django's cache.
    #
    # MAX_ATTEMPTS = 5
    # BLOCK_SECONDS = 300
    #
    # error_message = None
    #
    # username = (
    #     request.POST.get("username", "").strip()
    #     if request.method == "POST"
    #     else ""
    # )
    #
    # cache_key = "login_attempts_" + salted_hmac(
    #     "reading-lab-login",
    #     username.lower()
    # ).hexdigest()
    #
    # if request.method == "POST":
    #     attempts = cache.get(cache_key, 0)
    #
    #     if attempts >= MAX_ATTEMPTS:
    #         form = AuthenticationForm(request)
    #         error_message = (
    #             "Too many failed login attempts. "
    #             "Please try again in 5 minutes."
    #         )
    #     else:
    #         form = AuthenticationForm(request, data=request.POST)
    #
    #         if form.is_valid():
    #             cache.delete(cache_key)
    #             login(request, form.get_user())
    #
    #             if UserBook.objects.filter(user=request.user).exists():
    #                 return redirect("dashboard")
    #
    #             return redirect("upload")
    #
    #         cache.set(
    #             cache_key,
    #             attempts + 1,
    #             timeout=BLOCK_SECONDS
    #         )
    # else:
    #     form = AuthenticationForm(request)

    return render(request, "analytics/login.html", {
        "form": form,
    # FIX: Uncomment this when enabling rate limiting.
    # "error_message": error_message,
    })



@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")



def home(request):
    if not request.user.is_authenticated:
        return redirect("login")

    if UserBook.objects.filter(user=request.user).exists():
        return redirect("dashboard")

    return redirect("upload")


from django.db.models import Q


@login_required
@require_http_methods(["GET", "POST"])
def library_view(request):

    if request.method == "POST":

        # FLAW 1 - A01:2021 Broken Access Control

        # Vulnerable code: Missing ownership verification.
        user_book = get_object_or_404(
           UserBook,
           id=request.POST.get("user_book_id")
        )

        # FIX: Verify that the requested book belongs to the logged-in user.
        # user_book = get_object_or_404(
        #     UserBook,
        #     id=request.POST.get("user_book_id"),
        #     user=request.user
        #)

        try:
            rating = int(request.POST.get("rating", ""))

            if rating < 0 or rating > 5:
                raise ValueError()

            user_book.rating = rating
            user_book.save(update_fields=["rating"])

            return redirect("library")

        except (ValueError, TypeError):
            pass



    # FLAW 2 - A03:2021 Injection (SQL Injection)

    search = request.GET.get("search", "").strip()
    shelf = request.GET.get("shelf", "").strip()

    # VULNERABLE CODE:
    # User-controlled input is directly inserted into the SQL query.
    if search:
        query = f"""
            SELECT ub.*
            FROM analytics_userbook AS ub
            JOIN analytics_book AS b ON ub.book_id = b.id
            WHERE ub.user_id = {request.user.id}
              AND (b.title || ' ' || b.author) LIKE '%{search}%'
            ORDER BY b.title
        """
        books = UserBook.objects.raw(query)

    else:
        books = UserBook.objects.filter(
            user=request.user
        ).select_related("book").order_by("book__title")

    if shelf:
        books = [
            user_book for user_book in books
            if user_book.shelf == shelf
        ]

    # FIX: Use Django ORM with parameterized queries
    # to prevent SQL Injection.
    #
    # books = UserBook.objects.filter(
    #     user=request.user
    # ).select_related("book")

    # if search:
    #    books = books.filter(
    #         Q(book__title__icontains=search) |
    #         Q(book__author__icontains=search)
    #     )
    #
    # if shelf:
    #     books = books.filter(shelf=shelf)
    #
    # books = books.order_by("book__title")

    # return render(request, "analytics/library.html", {
    #    "books": books,
    #    "search": search,
    #    "selected_shelf": shelf,
    #    "total_books": len(books),
    # })
