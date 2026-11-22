from datetime import datetime, timezone
import os
from typing import Any

APP_NAME = os.getenv("APP_NAME", "Page & Pour Book Cafe")
APP_VERSION = os.getenv("APP_VERSION", "v1.2.0")
APP_ENV = os.getenv("APP_ENV", "development")

GENRE_CATALOG: list[dict[str, str]] = [
    {"slug": "all", "label": "All Genres", "icon": "books"},
    {"slug": "sci-fi", "label": "Sci-Fi", "icon": "planet"},
    {"slug": "fantasy", "label": "Fantasy", "icon": "sparkles"},
    {"slug": "essays", "label": "Essays", "icon": "feather"},
    {"slug": "poetry", "label": "Poetry", "icon": "quill"},
    {"slug": "mystery", "label": "Mystery", "icon": "compass"},
]

CAFE_PRODUCTS: list[dict[str, str]] = [
    {
        "category": "Drinks",
        "name": "Cardamom Oat Latte",
        "price": "$4.75",
        "description": "Double-shot espresso steamed with velvety oat milk and crushed green cardamom.",
        "badge": "Barista Favorite",
        "visual": "latte",
    },
    {
        "category": "Drinks",
        "name": "Earl Grey Lavender Fog",
        "price": "$4.50",
        "description": "Loose-leaf bergamot black tea steeped with culinary lavender and vanilla foam.",
        "badge": "Caffeine-Light",
        "visual": "tea",
    },
    {
        "category": "Pastries",
        "name": "Brown-Butter Almond Croissant",
        "price": "$4.25",
        "description": "Flaky laminated pastry baked every morning with toasted frangipane filling.",
        "badge": "Baked Daily",
        "visual": "croissant",
    },
    {
        "category": "Pastries",
        "name": "Cinnamon Brioche Knot",
        "price": "$3.95",
        "description": "Warm cardamom-cinnamon twisted brioche glazed with raw Demerara sugar.",
        "badge": "Pairs with Espresso",
        "visual": "brioche",
    },
    {
        "category": "Merchandise",
        "name": "Heavyweight Canvas Book Tote",
        "price": "$18.00",
        "description": "16oz organic cotton tote with an interior pocket built for hardcovers and notebooks.",
        "badge": "Limited Batch",
        "visual": "tote",
    },
    {
        "category": "Merchandise",
        "name": "Brass Page-Holder Bookmark",
        "price": "$12.00",
        "description": "Engraved Page & Pour bookmark designed to hold thick paperbacks flat while you sip.",
        "badge": "Reader Gift",
        "visual": "bookmark",
    },
]

_BOOKS: list[dict[str, Any]] = []
_MEMBERS: list[dict[str, Any]] = []
_NOTIFICATIONS: list[dict[str, Any]] = []
_NEXT_BOOK_ID = 1
_NEXT_MEMBER_ID = 1
_NEXT_NOTIFICATION_ID = 1


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_books() -> list[dict[str, Any]]:
    return _BOOKS


def get_members() -> list[dict[str, Any]]:
    return _MEMBERS


def get_notifications() -> list[dict[str, Any]]:
    return _NOTIFICATIONS


def find_book(book_id: int) -> tuple[int, dict[str, Any]] | None:
    for idx, book in enumerate(_BOOKS):
        if book["id"] == book_id:
            return idx, book
    return None


def notify_interested_members(book: dict[str, Any], event_type: str) -> list[dict[str, Any]]:
    global _NEXT_NOTIFICATION_ID
    created: list[dict[str, Any]] = []
    book_genre = book["genre"].lower()
    book_author = book["author"].lower()

    for member in _MEMBERS:
        interest = member["interest"].lower()
        if interest in ("all", book_genre, book_author) or interest in book_genre or interest in book_author:
            action_text = "just arrived in stock" if event_type == "new_arrival" else "is back in stock"
            notif = {
                "id": _NEXT_NOTIFICATION_ID,
                "event": event_type,
                "member_id": member["id"],
                "member_name": member["name"],
                "contact": member["contact"],
                "book_id": book["id"],
                "book_title": book["title"],
                "message": f"Hi {member['name']}, '{book['title']}' by {book['author']} {action_text} at {APP_NAME}!",
                "created_at": now_iso(),
            }
            _NEXT_NOTIFICATION_ID += 1
            _NOTIFICATIONS.append(notif)
            created.append(notif)

    return created


def add_book(title: str, author: str, genre: str, in_stock: bool) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    global _NEXT_BOOK_ID
    book = {
        "id": _NEXT_BOOK_ID,
        "title": title,
        "author": author,
        "genre": genre,
        "in_stock": in_stock,
    }
    _NEXT_BOOK_ID += 1
    _BOOKS.append(book)
    notifications = notify_interested_members(book, "new_arrival") if in_stock else []
    return book, notifications


def add_member(name: str, contact: str, interest: str) -> dict[str, Any]:
    global _NEXT_MEMBER_ID
    member = {
        "id": _NEXT_MEMBER_ID,
        "name": name,
        "contact": contact,
        "interest": interest,
    }
    _NEXT_MEMBER_ID += 1
    _MEMBERS.append(member)
    return member


def reset_state() -> None:
    """Reset sample books, members, and notifications to a known state."""
    global _BOOKS, _MEMBERS, _NOTIFICATIONS, _NEXT_BOOK_ID, _NEXT_MEMBER_ID, _NEXT_NOTIFICATION_ID
    _BOOKS = [
        {
            "id": 1,
            "title": "The Left Hand of Darkness",
            "author": "Ursula K. Le Guin",
            "genre": "sci-fi",
            "in_stock": True,
        },
        {
            "id": 2,
            "title": "A Swim in a Pond in the Rain",
            "author": "George Saunders",
            "genre": "essays",
            "in_stock": False,
        },
        {
            "id": 3,
            "title": "Piranesi",
            "author": "Susanna Clarke",
            "genre": "fantasy",
            "in_stock": True,
        },
        {
            "id": 4,
            "title": "Devotions",
            "author": "Mary Oliver",
            "genre": "poetry",
            "in_stock": True,
        },
    ]
    _MEMBERS = [
        {
            "id": 1,
            "name": "Alex",
            "contact": "alex@example.com",
            "interest": "sci-fi",
        },
        {
            "id": 2,
            "name": "Sam",
            "contact": "+15550199",
            "interest": "all",
        },
    ]
    _NOTIFICATIONS = []
    _NEXT_BOOK_ID = 5
    _NEXT_MEMBER_ID = 3
    _NEXT_NOTIFICATION_ID = 1


reset_state()
