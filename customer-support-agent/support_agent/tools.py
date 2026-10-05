import re

from google.adk.tools import ToolContext


CUSTOMER = {"customer_id": "C001", "name": "Alex", "order_ids": ["ORD-1001", "ORD-1002"]}
ORDERS = {
    "ORD-1001": {
        "customer_id": "C001", "order_status": "shipped",
        "item": "Wireless headphones", "tracking_number": "DEMO-TRACK-001",
        "delivery_estimate": "Within 2 business days (demo estimate)",
    },
    "ORD-1002": {
        "customer_id": "C001", "order_status": "processing",
        "item": "USB-C charger", "delivery_estimate": "Within 5 business days (demo estimate)",
    },
    "ORD-2001": {"customer_id": "C002", "order_status": "delivered", "item": "Keyboard"},
}
ARTICLES = [
    {
        "id": "KB-SHIPPING", "title": "Shipping and tracking",
        "text": "Orders ship within 2 business days. Standard delivery takes 3-5 business days. Tracking is available after dispatch.",
        "keywords": "shipping shipped delivery tracking dispatch order late delayed",
    },
    {
        "id": "KB-RETURNS", "title": "Returns and refunds",
        "text": "Returns can be requested within 30 days of delivery. Refunds require human approval; this demo cannot issue refunds.",
        "keywords": "return returns refund refunds damaged broken money",
    },
    {
        "id": "KB-PAYMENTS", "title": "Payments and cancellations",
        "text": "Payment disputes and cancellation requests must be reviewed by a human support representative.",
        "keywords": "payment payments charge charged billing cancellation cancel",
    },
]


def search_knowledge_base(query: str) -> dict:
    """Search local support articles using keywords; return article IDs and text."""
    words = set(re.findall(r"\w+", query.lower()))
    matches = [
        {"article_id": article["id"], "title": article["title"], "text": article["text"]}
        for article in ARTICLES
        if words.intersection(article["keywords"].split())
    ]
    return {"status": "success" if matches else "not_found", "articles": matches}


def get_customer_details() -> dict:
    """Return the fixed demo customer's profile and order IDs."""
    return {"status": "success", **CUSTOMER}


def get_order_details(order_id: str) -> dict:
    """Return order status and tracking for demo customer C001 only."""
    order_id = order_id.strip().upper()
    order = ORDERS.get(order_id)
    if order is None or order["customer_id"] != CUSTOMER["customer_id"]:
        return {"status": "error", "message": "Order not found for this customer."}
    return {"status": "success", "order_id": order_id, **order}


def create_ticket(summary: str, category: str, tool_context: ToolContext) -> dict:
    """Create a session-local ticket. Category must be support or human_review.

    Use human_review for refunds, payments, cancellations, or critical complaints.
    This records a request only; it does not perform or approve sensitive actions.
    """
    if not summary.strip():
        return {"status": "error", "message": "A ticket summary is required."}
    if category not in {"support", "human_review"}:
        return {"status": "error", "message": "Category must be support or human_review."}
    tickets = dict(tool_context.state.get("tickets", {}))
    # Identical retries return the original ticket instead of creating duplicates.
    for ticket in tickets.values():
        if ticket["summary"] == summary.strip() and ticket["category"] == category:
            return {"status": "success", "ticket": ticket}
    ticket_id = f"TKT-{len(tickets) + 1:04d}"
    ticket = {
        "ticket_id": ticket_id, "summary": summary.strip(), "category": category,
        "status": "pending_human_review" if category == "human_review" else "open",
    }
    tickets[ticket_id] = ticket
    tool_context.state["tickets"] = tickets
    return {"status": "success", "ticket": ticket}


def get_ticket_details(ticket_id: str, tool_context: ToolContext) -> dict:
    """Return a ticket from the current session only."""
    ticket = tool_context.state.get("tickets", {}).get(ticket_id.strip().upper())
    if ticket is None:
        return {"status": "error", "message": "Ticket not found in this session."}
    return {"status": "success", "ticket": ticket}
