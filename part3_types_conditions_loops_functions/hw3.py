#!/usr/bin/env python

from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"


EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}


financial_transactions_storage: list[dict[str, Any]] = []


def is_leap_year(year: int) -> bool:

    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    parts = maybe_dt.split("-")
    if len(parts) != 3:
        return None
    day_str, month_str, year_str = parts
    if not day_str.isdigit() or not month_str.isdigit() or not year_str.isdigit():
        return None
    if len(year_str) != 4:
        return None
    day, month, year = int(day_str), int(month_str), int(year_str)
    if year < 1 or month < 1 or month > 12:
        return None
    days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if is_leap_year(year):
        days_in_month[2] = 29
    if day < 1 or day > days_in_month[month]:
        return None
    return (day, month, year)


def income_handler(amount: float, income_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG
    parsed_date = extract_date(income_date)
    if parsed_date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG
    financial_transactions_storage.append({"amount": amount, "date": parsed_date})
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG
    parsed_date = extract_date(income_date)
    if parsed_date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG
    cat_parts = category_name.split("::")
    if len(cat_parts) != 2:
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY
    common_cat, target_cat = cat_parts
    if common_cat not in EXPENSE_CATEGORIES or target_cat not in EXPENSE_CATEGORIES[common_cat]:
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY
    financial_transactions_storage.append({"category": category_name, "amount": amount, "date": parsed_date})
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    return "\n".join(f"{k}::{v}" for k, kv in EXPENSE_CATEGORIES.items() for v in kv)


def _get_date_tuple(entry: dict[str, Any]) -> tuple[int, int, int] | None:
    date = entry.get("date")
    if date is None:
        return None
    if isinstance(date, tuple):
        return date
    return extract_date(str(date))


def _date_leq(date_tuple: tuple[int, int, int], report_tuple: tuple[int, int, int]) -> bool:
    day, month, year = date_tuple
    rd, rm, ry = report_tuple
    return (year, month, day) <= (ry, rm, rd)


def stats_handler(report_date: str) -> str:
    parsed_report = extract_date(report_date)
    if parsed_report is None:
        return INCORRECT_DATE_MSG

    _, rm, ry = parsed_report

    total_income = 0.0
    total_expense = 0.0
    month_income = 0.0
    month_expense = 0.0
    category_totals: dict[str, float] = {}

    for entry in financial_transactions_storage:
        if not entry:
            continue
        date_tuple = _get_date_tuple(entry)
        if date_tuple is None:
            continue
        if not _date_leq(date_tuple, parsed_report):
            continue

        is_cost = "category" in entry
        amount = entry.get("amount", 0.0)

        if is_cost:
            total_expense += amount
        else:
            total_income += amount

        _, em, ey = date_tuple
        if em == rm and ey == ry:
            if is_cost:
                month_expense += amount
                cat = entry["category"]
                if cat not in category_totals:
                    category_totals[cat] = 0.0
                category_totals[cat] += amount
            else:
                month_income += amount

    total_capital = round(total_income - total_expense, 2)
    monthly_diff = round(month_income - month_expense, 2)
    amount_word = "profit" if monthly_diff >= 0 else "loss"
    display_diff = abs(monthly_diff)

    lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {total_capital:.2f} rubles",
        f"This month, the {amount_word} amounted to {display_diff:.2f} rubles.",
        f"Income: {month_income:.2f} rubles",
        f"Expenses: {month_expense:.2f} rubles",
        "",
        "Details (category: amount):",
    ]

    for i, (cat, amt) in enumerate(sorted(category_totals.items()), 1):
        lines.append(f"{i}. {cat}: {amt}")

    return "\n".join(lines)


def _parse_amount(s: str) -> float | None:
    s = s.replace(",", ".")
    if not s:
        return None
    start = 0
    if s[0] == "-":
        start = 1
    if start >= len(s):
        return None
    has_dot = False
    for i in range(start, len(s)):
        c = s[i]
        if c == ".":
            if has_dot:
                return None
            has_dot = True
        elif not c.isdigit():
            return None
    if s[start:] in (".", ""):
        return None
    return float(s)


def _handle_command(parts: list[str]) -> str:
    if not parts:
        return UNKNOWN_COMMAND_MSG

    cmd = parts[0]

    if cmd == "income":
        if len(parts) != 3:
            return UNKNOWN_COMMAND_MSG
        amount = _parse_amount(parts[1])
        if amount is None:
            return UNKNOWN_COMMAND_MSG
        return income_handler(amount, parts[2])

    if cmd == "cost":
        if len(parts) == 2 and parts[1] == "categories":
            return cost_categories_handler()
        if len(parts) != 4:
            return UNKNOWN_COMMAND_MSG
        amount = _parse_amount(parts[2])
        if amount is None:
            return UNKNOWN_COMMAND_MSG
        return cost_handler(parts[1], amount, parts[3])

    if cmd == "stats":
        if len(parts) != 2:
            return UNKNOWN_COMMAND_MSG
        return stats_handler(parts[1])

    return UNKNOWN_COMMAND_MSG


def main() -> None:
    while True:
        line = input()
        parts = line.strip().split()
        if not parts:
            continue
        print(_handle_command(parts))


if __name__ == "__main__":
    main()
