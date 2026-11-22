import os
from typing import Any

from flask import Flask, jsonify, redirect, render_template, request, url_for

from app.store import (
    APP_ENV,
    APP_NAME,
    APP_VERSION,
    CAFE_PRODUCTS,
    GENRE_CATALOG,
    add_book,
    add_member,
    find_book,
    get_books,
    get_members,
    get_notifications,
    notify_interested_members,
    reset_state,
)

app = Flask(__name__)


def _filter_books(query: str = "", genre: str = "all") -> list[dict[str, Any]]:
    books = get_books()
    clean_genre = genre.strip().lower()
    clean_query = query.strip().lower()

    if clean_genre and clean_genre != "all":
        books = [b for b in books if b["genre"].lower() == clean_genre]

    if clean_query:
        books = [
            b
            for b in books
            if clean_query in b["title"].lower()
            or clean_query in b["author"].lower()
            or clean_query in b["genre"].lower()
        ]
    return books


@app.get("/")
def index() -> str:
    books = get_books()
    in_stock_count = sum(1 for b in books if b["in_stock"])
    return render_template(
        "index.html",
        app_name=APP_NAME,
        version=APP_VERSION,
        env_name=APP_ENV,
        active_page="home",
        books=books,
        in_stock_count=in_stock_count,
        member_count=len(get_members()),
        notifications=get_notifications(),
        genres=GENRE_CATALOG,
        products=CAFE_PRODUCTS,
        subscribed=request.args.get("subscribed") == "1",
    )


@app.get("/search")
def search_page() -> str:
    query = str(request.args.get("q", "")).strip()
    selected_genre = str(request.args.get("genre", "all")).strip().lower() or "all"
    results = _filter_books(query=query, genre=selected_genre)
    return render_template(
        "search.html",
        app_name=APP_NAME,
        version=APP_VERSION,
        env_name=APP_ENV,
        active_page="search",
        query=query,
        selected_genre=selected_genre,
        genres=GENRE_CATALOG,
        results=results,
    )


@app.get("/about")
def about_page() -> str:
    return render_template(
        "about.html",
        app_name=APP_NAME,
        version=APP_VERSION,
        env_name=APP_ENV,
        active_page="about",
        products=CAFE_PRODUCTS,
    )


@app.post("/subscribe")
def subscribe_from_ui() -> Any:
    name = str(request.form.get("name", "")).strip()
    contact = str(request.form.get("contact", "")).strip()
    interest = str(request.form.get("interest", "all")).strip() or "all"
    if name and contact:
        add_member(name=name, contact=contact, interest=interest)
        return redirect(url_for("index", subscribed="1"))
    return redirect(url_for("index"))


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
    books = get_books()
    if only_in_stock is not None:
        flag = only_in_stock.lower() == "true"
        books = [b for b in books if b["in_stock"] is flag]
    return jsonify({"books": books, "count": len(books)}), 200


@app.get("/books/search")
def search_books() -> tuple[Any, int]:
    query = str(request.args.get("q", "")).strip().lower()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    matches = _filter_books(query=query)
    return jsonify({"query": query, "results": matches, "count": len(matches)}), 200


@app.post("/books")
def create_book() -> tuple[Any, int]:
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    if not title:
        return jsonify({"error": "Book 'title' is required"}), 400

    author = str(payload.get("author", "Unknown Author")).strip() or "Unknown Author"
    genre = str(payload.get("genre", "general")).strip() or "general"
    raw_in_stock = payload.get("in_stock", True)
    if not isinstance(raw_in_stock, bool):
        return jsonify({"error": "Boolean 'in_stock' is required"}), 400

    book, notifications = add_book(title=title, author=author, genre=genre, in_stock=raw_in_stock)
    return jsonify({"book": book, "notifications_sent": notifications}), 201


@app.patch("/books/<int:book_id>/stock")
def update_book_stock(book_id: int) -> tuple[Any, int]:
    found = find_book(book_id)
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
        notifications = notify_interested_members(book, "back_in_stock")

    return jsonify(
        {
            "book": book,
            "restocked": (not was_in_stock and now_in_stock),
            "notifications_sent": notifications,
        }
    ), 200


@app.delete("/books/<int:book_id>")
def delete_book(book_id: int) -> tuple[Any, int]:
    found = find_book(book_id)
    if found is None:
        return jsonify({"error": f"Book {book_id} not found"}), 404

    idx, _ = found
    removed = get_books().pop(idx)
    return jsonify({"deleted": removed}), 200


@app.get("/members")
def list_members() -> tuple[Any, int]:
    members = get_members()
    return jsonify({"members": members, "count": len(members)}), 200


@app.post("/members")
def create_member() -> tuple[Any, int]:
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    contact = str(payload.get("contact", "")).strip()
    interest = str(payload.get("interest", "all")).strip() or "all"

    if not name or not contact:
        return jsonify({"error": "Both 'name' and 'contact' are required"}), 400

    member = add_member(name=name, contact=contact, interest=interest)
    return jsonify(member), 201


@app.get("/notifications")
def list_notifications() -> tuple[Any, int]:
    notifications = get_notifications()
    return jsonify({"notifications": notifications, "count": len(notifications)}), 200


__all__ = ["app", "reset_state"]


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
