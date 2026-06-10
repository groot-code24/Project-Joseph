from dataclasses import asdict

import database
from policy_guard import PolicyGuard

TOOLS = [
    {
        "name": "lookup_customer",
        "description": (
            "Look up a customer's profile by their customer ID. "
            "Returns name, email, tier (standard/vip/new), and phone."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The customer's ID, e.g. CUS-001",
                }
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "lookup_order",
        "description": (
            "Look up a complete order record by order ID. Returns product, amount, "
            "dates, delivery status, days since delivery, is_final_sale, "
            "is_digital_good, is_defective flags."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID, e.g. ORD-001",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "check_refund_eligibility",
        "description": (
            "MANDATORY BEFORE ANY DECISION. Runs a deterministic policy check against "
            "the order and customer's refund history. Returns: decision "
            "(approve/deny/escalate), violated_rules list, cited_sections list, "
            "rationale string. You MUST call this before making any refund decision. "
            "If it returns deny, you MUST deny. If it returns escalate, you MUST "
            "escalate. You cannot override it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "customer_id": {"type": "string"},
            },
            "required": ["order_id", "customer_id"],
        },
    },
    {
        "name": "create_refund_ticket",
        "description": (
            "Creates a refund ticket and persists the decision. Call this ONLY after "
            "check_refund_eligibility confirms the decision. status must be exactly: "
            "'approved', 'denied', or 'escalated_human'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "customer_id": {"type": "string"},
                "reason": {
                    "type": "string",
                    "description": "The customer's stated reason for the refund",
                },
                "status": {
                    "type": "string",
                    "enum": ["approved", "denied", "escalated_human"],
                },
                "resolution": {
                    "type": "string",
                    "description": "The resolution summary citing relevant policy sections",
                },
            },
            "required": ["order_id", "customer_id", "reason", "status", "resolution"],
        },
    },
]


async def handle_tool_call(tool_name: str, tool_input: dict) -> dict:
    try:
        if tool_name == "lookup_customer":
            return await _lookup_customer(**tool_input)
        if tool_name == "lookup_order":
            return await _lookup_order(**tool_input)
        if tool_name == "check_refund_eligibility":
            return await _check_refund_eligibility(**tool_input)
        if tool_name == "create_refund_ticket":
            return await _create_refund_ticket(**tool_input)
        return {"error": f"Unknown tool: {tool_name}", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}


async def _lookup_customer(customer_id: str) -> dict:
    customer = await database.get_customer(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found", "success": False}
    return {"success": True, "customer": customer}


async def _lookup_order(order_id: str) -> dict:
    order = await database.get_order(order_id)
    if not order:
        return {"error": f"Order {order_id} not found", "success": False}
    return {"success": True, "order": order}


async def _check_refund_eligibility(order_id: str, customer_id: str) -> dict:
    order = await database.get_order(order_id)
    if not order:
        return {"error": f"Order {order_id} not found", "success": False}

    history = await database.get_refund_history(customer_id)
    is_duplicate = await database.check_duplicate_refund(order_id)

    guard = PolicyGuard()
    result = guard.evaluate(order, history, is_duplicate)
    payload = asdict(result)
    payload["success"] = True
    return payload


async def _create_refund_ticket(
    order_id: str,
    customer_id: str,
    reason: str,
    status: str,
    resolution: str,
) -> dict:
    if status not in ("approved", "denied", "escalated_human"):
        return {"error": f"Invalid status: {status}", "success": False}
    ticket_id = await database.create_refund_request(
        order_id=order_id,
        customer_id=customer_id,
        reason=reason,
        status=status,
        resolution=resolution,
        resolved_by="nova-ai",
    )
    return {"success": True, "ticket_id": ticket_id, "status": status}
