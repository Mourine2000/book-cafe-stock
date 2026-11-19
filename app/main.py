from datetime import datetime, timezone
import os
from typing import Any

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

APP_NAME = os.getenv("APP_NAME", "Page & Pour Book Cafe")
APP_VERSION = os.getenv("APP_VERSION", "v1.0.0")
APP_ENV = os.getenv("APP_ENV", "development")

_BOOKS: list[dict[str, Any]] = []
_MEMBERS: list[dict[str, Any]] = []
_NOTIFICATIONS: list[dict[str, Any]] = []
_NEXT_BOOK_ID = 1
_NEXT_MEMBER_ID = 1
_NEXT_NOTIFICATION_ID = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _find_book(book_id: int) -> tuple[int, dict[str, Any]] | None:
    for idx, book in enumerate(_BOOKS):
        if book["id"] == book_id:
            return idx, book
    return None


def _notify_interested_members(book: dict[str, Any], event_type: str) -> list[dict[str, Any]]:
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
                "created_at": _now_iso(),
            }
            _NEXT_NOTIFICATION_ID += 1
            _NOTIFICATIONS.append(notif)
            created.append(notif)

    return created


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
    _NEXT_BOOK_ID = 3
    _NEXT_MEMBER_ID = 3
    _NEXT_NOTIFICATION_ID = 1


reset_state()


@app.get("/")
def index() -> str:
    return render_template(
        "index.html",
        app_name=APP_NAME,
        version=APP_VERSION,
        env_name=APP_ENV,
    )


@app.get("/health")
def health() -> tuple[Any, int]:
    return jsonify({"status": "ok", "version": APP_VERSION}), 200


@app.get("/version")
def version() -> tuple[Any, int]:
    return jsonify(
        {
            "app": APP_NAME,
            "version": APP_VERSION,
            "environment": APP_ENV,
        }
    ), 200


@app.get("/books")
def list_books() -> tuple[Any, int]:
    only_in_stock = request.args.get("in_stock")
    books = _BOOKS
    if only_in_stock is not None:
        flag = only_in_stock.lower() == "true"
        books = [b for b in _BOOKS if b["in_stock"] is flag]
    return jsonify({"books": books, "count": len(books)}), 200


@app.post("/books")
def create_book() -> tuple[Any, int]:
    global _NEXT_BOOK_ID
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    if not title:
        return jsonify({"error": "Book 'title' is required"}), 400

    author = str(payload.get("author", "Unknown Author")).strip() or "Unknown Author"
    genre = str(payload.get("genre", "general")).strip() or "general"
    in_stock = bool(payload.get("in_stock", True))

    book = {
        "id": _NEXT_BOOK_ID,
        "title": title,
        "author": author,
        "genre": genre,
        "in_stock": in_stock,
    }
    _NEXT_BOOK_ID += 1
    _BOOKS.append(book)

    notifications = _notify_interested_members(book, "new_arrival") if in_stock else []
    return jsonify({"book": book, "notifications_sent": notifications}), 201


@app.patch("/books/<int:book_id>/stock")
def update_book_stock(book_id: int) -> tuple[Any, int]:
    found = _find_book(book_id)
    if found is None:
        return jsonify({"error": f"Book {book_id} not found"}), 404

    _, book = found
    payload = request.get_json(silent=True) or {}
    if "in_stock" not in payload or not isinstance(payload["in_stock"], bool):
        return jsonify({"error": "Boolean 'in_stock' is required"}), 400

    was_in_stock = book["in_stock"]
    now_in_stock = payload["in_stock"]
    book["in_stock"] = now_in_stock

    notifications: list[dict[str, Any]] = []
    if not was_in_stock and now_in_stock:
        notifications = _notify_interested_members(book, "back_in_stock")

    return jsonify(
        {
            "book": book,
            "restocked": (not was_in_stock and now_in_stock),
            "notifications_sent": notifications,
        }
    ), 200


@app.delete("/books/<int:book_id>")
def delete_book(book_id: int) -> tuple[Any, int]:
    found = _find_book(book_id)
    if found is None:
        return jsonify({"error": f"Book {book_id} not found"}), 404

    idx, _ = found
    removed = _BOOKS.pop(idx)
    return jsonify({"deleted": removed}), 200


@app.get("/members")
def list_members() -> tuple[Any, int]:
    return jsonify({"members": _MEMBERS, "count": len(_MEMBERS)}), 200


@app.post("/members")
def create_member() -> tuple[Any, int]:
    global _NEXT_MEMBER_ID
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    contact = str(payload.get("contact", "")).strip()
    interest = str(payload.get("interest", "all")).strip() or "all"

    if not name or not contact:
        return jsonify({"error": "Both 'name' and 'contact' are required"}), 400

    member = {
        "id": _NEXT_MEMBER_ID,
        "name": name,
        "contact": contact,
        "interest": interest,
    }
    _NEXT_MEMBER_ID += 1
    _MEMBERS.append(member)
    return jsonify(member), 201


@app.get("/notifications")
def list_notifications() -> tuple[Any, int]:
    return jsonify({"notifications": _NOTIFICATIONS, "count": len(_NOTIFICATIONS)}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
