"""Deterministic perturbation choices for observation fields.

The generator is deliberately rule-based: no LLM paraphrase enters the
manipulation. Critical fields prefer domain-aware alternatives (status, cabin,
route, date, price, identifiers) and fall back to another value of the same
field in the observation. Non-critical fields may be omitted when no plausible
alternative exists.
"""

from __future__ import annotations

import copy
import random
import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from ..harvest.relevance import flatten_leaves, normalize_scalar

AIRPORTS = (
    "ATL",
    "BOS",
    "CLT",
    "DEN",
    "DFW",
    "DTW",
    "EWR",
    "IAH",
    "JFK",
    "LAS",
    "LAX",
    "LGA",
    "MCO",
    "MIA",
    "MSP",
    "ORD",
    "PHL",
    "PHX",
    "SEA",
    "SFO",
)

STATUS_ALTERNATIVES = {
    "delivered": "pending",
    "pending": "delivered",
    "cancelled": "confirmed",
    "confirmed": "cancelled",
    "available": "unavailable",
    "unavailable": "available",
    "open": "closed",
    "closed": "open",
    "success": "failed",
    "failed": "success",
    "completed": "pending",
    "returned": "delivered",
    "paid": "refunded",
    "refunded": "paid",
    "return requested": "return completed",
    "return completed": "return requested",
    "exchange requested": "exchange completed",
    "exchange completed": "exchange requested",
    "processed": "pending",
    "shipped": "delivered",
}

CANCEL_REASON_ALTERNATIVES = {
    "no longer needed": "ordered by mistake",
    "ordered by mistake": "no longer needed",
    "changed mind": "no longer needed",
    "found cheaper": "no longer needed",
}

STATE_CODES = (
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
    "DC",
)

COUNTRY_ALTERNATIVES = {"usa": "Canada", "canada": "USA"}

CABIN_ALTERNATIVES = {
    "basic_economy": "economy",
    "economy": "business",
    "business": "economy",
}

FLIGHT_TYPE_ALTERNATIVES = {"one_way": "round_trip", "round_trip": "one_way"}

COLOR_ALTERNATIVES = {
    "blue": "black",
    "black": "blue",
    "red": "blue",
    "white": "black",
    "green": "blue",
    "silver": "black",
    "grey": "black",
    "gray": "black",
}

MATERIAL_ALTERNATIVES = {
    "cotton": "polyester",
    "polyester": "cotton",
    "leather": "fabric",
    "fabric": "leather",
    "glass": "plastic",
    "plastic": "glass",
    "steel": "aluminum",
    "aluminum": "steel",
    "wood": "metal",
    "metal": "wood",
}

SIZE_ALTERNATIVES = {
    "small": "medium",
    "medium": "large",
    "large": "medium",
    "xs": "s",
    "s": "m",
    "m": "l",
    "l": "xl",
    "xl": "l",
}

DIFFICULTY_ALTERNATIVES = {
    "beginner": "intermediate",
    "intermediate": "advanced",
    "advanced": "beginner",
    "easy": "medium",
    "medium": "hard",
    "hard": "easy",
}

THEME_ALTERNATIVES = {
    "art": "nature",
    "nature": "art",
    "space": "ocean",
    "ocean": "space",
    "animals": "flowers",
    "flowers": "animals",
}

IDENTIFIER_KEYS = frozenset(
    {
        "order_id",
        "reservation_id",
        "product_id",
        "item_id",
        "flight_number",
        "transaction_id",
    }
)

PII_KEYS = frozenset(
    {
        "user_id",
        "payment_id",
        "payment_method_id",
        "email",
        "phone",
        "first_name",
        "last_name",
        "address1",
        "address2",
        "city",
        "zip",
        "dob",
    }
)

PRODUCT_NAMES = (
    "Water Bottle",
    "Office Chair",
    "Desk Lamp",
    "Backpack",
    "T-Shirt",
    "Laptop",
    "Tablet",
    "Smart Watch",
    "Headphones",
    "Wireless Earbuds",
    "Running Shoes",
    "Sunglasses",
    "Coffee Maker",
    "Electric Kettle",
    "Yoga Mat",
)

PRICE_KEYS = frozenset(
    {"price", "amount", "cost", "fee", "balance", "refund", "total", "difference", "value"}
)
COUNT_KEYS = frozenset(
    {"count", "quantity", "baggages", "seats", "stock", "available", "rating", "reviews"}
)


@dataclass(slots=True)
class PerturbationChoice:
    """One concrete field change."""

    json_path: str
    path_pattern: str
    true_value: Any
    false_value: Any
    criticality: str
    mode: str
    value_type: str


def parse_path(path: str) -> list[str | int]:
    """Parse a path produced by :func:`flatten_leaves`."""
    if not path.startswith("$"):
        raise ValueError(f"path must start with $: {path}")
    tokens: list[str | int] = []
    index = 1
    while index < len(path):
        if path[index] == ".":
            index += 1
            start = index
            while index < len(path) and path[index] not in ".[":
                index += 1
            tokens.append(path[start:index])
        elif path[index] == "[":
            end = path.index("]", index)
            inner = path[index + 1 : end]
            if inner.startswith(("'", '"')):
                tokens.append(inner[1:-1])
            else:
                tokens.append(int(inner))
            index = end + 1
        else:
            raise ValueError(f"bad path segment in {path!r}")
    return tokens


def get_path(value: Any, path: str) -> Any:
    current = value
    for token in parse_path(path):
        current = current[token]
    return current


def set_path(value: Any, path: str, new_value: Any) -> None:
    tokens = parse_path(path)
    current = value
    for token in tokens[:-1]:
        current = current[token]
    current[tokens[-1]] = new_value


def delete_path(value: Any, path: str) -> None:
    tokens = parse_path(path)
    current = value
    for token in tokens[:-1]:
        current = current[token]
    del current[tokens[-1]]


def _last_key(path: str) -> str:
    tokens = parse_path(path)
    for token in reversed(tokens):
        if isinstance(token, str):
            return token.lower()
    return ""


def _shift_date(value: str, days: int = 1) -> str | None:
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    return (parsed + timedelta(days=days)).isoformat()


def _change_identifier(value: str) -> str:
    match = re.search(r"(\d)(?!.*\d)", value)
    if match:
        digit = (int(match.group(1)) + 1) % 10
        return f"{value[: match.start(1)]}{digit}{value[match.end(1):]}"
    if value:
        return f"{value[:-1]}{'A' if value[-1] != 'A' else 'B'}"
    return "ALT"


def _other_same_field_value(observation: Any, path_pattern: str, true_value: Any) -> Any:
    values = [
        leaf.value
        for leaf in flatten_leaves(observation)
        if leaf.path_pattern == path_pattern and leaf.value != true_value
    ]
    return values[0] if values else None


def _other_string_from_observation(observation: Any, true_value: Any) -> Any:
    """Pick another string leaf, for list-like reference tools."""
    values = [
        leaf.value
        for leaf in flatten_leaves(observation)
        if isinstance(leaf.value, str) and leaf.value != true_value and len(leaf.value) > 1
    ]
    return sorted(values)[0] if values else None


def _other_product_name(value: Any) -> str | None:
    for name in PRODUCT_NAMES:
        if name != value:
            return name
    return None


def alternative_value(
    path: str,
    value: Any,
    observation: Any,
    *,
    criticality: str,
) -> Any:
    """Return a plausible alternative, or ``None`` if none can be generated."""
    key = _last_key(path)
    if key in PII_KEYS or "payment" in key or "passenger" in key:
        return None

    if isinstance(value, bool):
        return not value

    if isinstance(value, (int, float)):
        if key in PRICE_KEYS:
            changed = round(float(value) * 1.15, 2)
            if changed == value:
                changed = round(float(value) * 0.85, 2)
            return int(changed) if isinstance(value, int) else changed
        if key in COUNT_KEYS:
            changed = int(value) + 1
            return changed if changed != value else int(value) - 1
        changed = value + 1 if isinstance(value, int) else round(value * 1.1, 2)
        return changed if changed != value else value + 2

    if isinstance(value, str):
        lowered = value.lower()
        if key == "status" and lowered in STATUS_ALTERNATIVES:
            return STATUS_ALTERNATIVES[lowered]
        if key == "cabin" and lowered in CABIN_ALTERNATIVES:
            return CABIN_ALTERNATIVES[lowered]
        if key == "flight_type" and lowered in FLIGHT_TYPE_ALTERNATIVES:
            return FLIGHT_TYPE_ALTERNATIVES[lowered]
        if key == "insurance":
            return "no" if lowered == "yes" else "yes"
        if key == "cancel_reason" and lowered in CANCEL_REASON_ALTERNATIVES:
            return CANCEL_REASON_ALTERNATIVES[lowered]
        if key == "state" and value in STATE_CODES:
            return STATE_CODES[(STATE_CODES.index(value) + 1) % len(STATE_CODES)]
        if key == "country" and lowered in COUNTRY_ALTERNATIVES:
            return COUNTRY_ALTERNATIVES[lowered]
        if lowered in {"yes", "no"} and key != "insurance":
            return "no" if lowered == "yes" else "yes"
        if key in {"origin", "destination"} and value in AIRPORTS:
            return AIRPORTS[(AIRPORTS.index(value) + 1) % len(AIRPORTS)]
        if key == "flight_number":
            return _change_identifier(value)
        if key in {"date", "delivered_at", "created_at"}:
            shifted = _shift_date(value)
            if shifted is not None:
                return shifted
        if key in IDENTIFIER_KEYS:
            return _change_identifier(value)
        if key == "name":
            other_name = _other_product_name(value)
            if other_name is not None:
                return other_name
        if key == "difficulty level" and lowered in DIFFICULTY_ALTERNATIVES:
            return DIFFICULTY_ALTERNATIVES[lowered]
        if key == "theme" and lowered in THEME_ALTERNATIVES:
            return THEME_ALTERNATIVES[lowered]
        if value.isdigit():
            return _change_identifier(value)
        if key == "color" and lowered in COLOR_ALTERNATIVES:
            return COLOR_ALTERNATIVES[lowered]
        if key == "material" and lowered in MATERIAL_ALTERNATIVES:
            return MATERIAL_ALTERNATIVES[lowered]
        if key in {"size", "capacity"} and lowered in SIZE_ALTERNATIVES:
            return SIZE_ALTERNATIVES[lowered]
        if key in {"transaction_type"}:
            return "refund" if lowered == "payment" else "payment"
        if key in {"source"}:
            return None

        other = _other_same_field_value(observation, _pattern_for(path, observation), value)
        if other is not None and other != value:
            return other
        leaves = list(flatten_leaves(observation))
        if criticality == "critical" and leaves and all(
            isinstance(leaf.value, str) for leaf in leaves
        ):
            other = _other_string_from_observation(observation, value)
            if other is not None and other != value:
                return other
        if criticality == "noncritical":
            return None
        return None

    return None


def _pattern_for(path: str, observation: Any) -> str:
    for leaf in flatten_leaves(observation):
        if leaf.json_path == path:
            return leaf.path_pattern
    return path


def choose_perturbation(
    observation: Any,
    candidates: list[str],
    *,
    criticality: str,
    seed: str,
    excluded_paths: set[str] | None = None,
) -> PerturbationChoice | None:
    """Choose the first field in a deterministic shuffled order that can change."""
    excluded = excluded_paths or set()
    paths = [path for path in candidates if path not in excluded]
    random.Random(seed).shuffle(paths)
    for path in paths:
        try:
            true_value = get_path(observation, path)
        except (KeyError, IndexError, TypeError):
            continue
        pattern = _pattern_for(path, observation)
        if any(
            token in pattern
            for token in ("payment_id", "payment_method", "first_name", "last_name", "dob")
        ):
            continue
        false_value = alternative_value(path, true_value, observation, criticality=criticality)
        if false_value is not None and false_value != true_value:
            return PerturbationChoice(
                json_path=path,
                path_pattern=pattern,
                true_value=true_value,
                false_value=false_value,
                criticality=criticality,
                mode="replace",
                value_type=type(true_value).__name__,
            )
        if criticality == "noncritical" and true_value is not None:
            return PerturbationChoice(
                json_path=path,
                path_pattern=pattern,
                true_value=true_value,
                false_value=None,
                criticality=criticality,
                mode="omit",
                value_type=type(true_value).__name__,
            )
    return None


def apply_choice(observation: Any, choice: PerturbationChoice) -> Any:
    """Return a deep copy with one choice applied."""
    if choice.json_path == "$":
        return None if choice.mode == "omit" else choice.false_value
    updated = copy.deepcopy(observation)
    if choice.mode == "omit":
        delete_path(updated, choice.json_path)
    else:
        set_path(updated, choice.json_path, choice.false_value)
    return updated


def value_set(observation: Any) -> list[tuple[str, str]]:
    """Return normalized scalar leaves as ``(path_pattern, value)`` pairs."""
    pairs: list[tuple[str, str]] = []
    for leaf in flatten_leaves(observation):
        normalized = normalize_scalar(leaf.value)
        if normalized is not None:
            pairs.append((leaf.path_pattern, normalized))
    return sorted(pairs)
