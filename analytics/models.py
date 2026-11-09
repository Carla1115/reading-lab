
from django.conf import settings
from django.db import models

from .encrypted_fields import EncryptedTextField

class Book(models.Model):
    # Information about a book from Goodreads
    goodreads_id = models.CharField(
        max_length=50,
        unique=True
    )

    title = models.CharField(max_length=500)
    author = models.CharField(max_length=300)

    number_of_pages = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    publication_year = models.IntegerField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.title


class UserBook(models.Model):
    # Reading information belonging to one user
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="library"
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="readers"
    )

    shelf = models.CharField(max_length=50)

    rating = models.PositiveSmallIntegerField(
        default=0
    )

    date_added = models.DateField(
        null=True,
        blank=True
    )

    date_read = models.DateField(
        null=True,
        blank=True
    )



    # FLAW 4 - A02:2021 Cryptographic Failures

    # VULNERABLE CODE:
    # Private notes are stored without application-level encryption.
    private_notes = models.TextField(blank=True)

    # FIX: Encrypt private notes using Fernet.
    # private_notes = EncryptedTextField(blank=True)



    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "book"],
                name="unique_user_book"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"
