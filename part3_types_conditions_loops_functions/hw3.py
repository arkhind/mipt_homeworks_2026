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

_DATE_PARTS = 3
_YEAR_STR_LEN = 4
_MAX_MONTH = 12
_CATEGORY_PARTS = 2
_INCOME_CMD_ARGS = 3
_COST_CMD_ARGS = 4
_STATS_CMD_ARGS = 2
_COST_CATEGORIES_CMD_ARGS = 2
_CATEGORY_KEY = "category"
_LEAP_FEB_DAYS = 29
_FEB_MONTH = 2
_KEEP_RUNNING = True

_DateTuple = tuple[int, int, int]
_MonthStats = tuple[float, float]
_StatsResult = tuple[float, float, _MonthStats, dict[str, float]]


def is_leap_year(year: int) -> bool:
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def _days_in_month(month: int, year: int) -> int:
    if month == _FEB_MONTH:
        return _LEAP_FEB_DAYS if is_leap_year(year) else 28
    if month in (4, 6, 9, 11):
        return 30
    return 31


def extract_date(maybe_dt: str) -> _DateTuple | None:
    parts = maybe_dt.split("-")
    if len(parts) != _DATE_PARTS:
        return None
    day_str, month_str, year_str = parts
    digits_valid = day_str.isdigit() and month_str.isdigit() and year_str.isdigit()
    parts_valid = digits_valid and len(year_str) == _YEAR_STR_LEN
    if not parts_valid:
        return None
    day = int(day_str)
    month = int(month_str)
    year = int(year_str)
    if year < 1 or not (1 <= month <= _MAX_MONTH):
        return None
    if not (1 <= day <= _days_in_month(month, year)):
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
    if len(cat_parts) != _CATEGORY_PARTS:
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY
    common_cat, target_cat = cat_parts
    if common_cat not in EXPENSE_CATEGORIES or target_cat not in EXPENSE_CATEGORIES[common_cat]:
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY
    financial_transactions_storage.append({_CATEGORY_KEY: category_name, "amount": amount, "date": parsed_date})
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    categories = (f"{k}::{v}" for k, kv in EXPENSE_CATEGORIES.items() for v in kv)
    return "\n".join(categories)


def _get_date_tuple(entry: dict[str, Any]) -> _DateTuple | None:
    date = entry.get("date")
    if date is None:
        return None
    if isinstance(date, tuple):
        return date
    return extract_date(str(date))


def _date_leq(date_tuple: _DateTuple, report_tuple: _DateTuple) -> bool:
    day, month, year = date_tuple
    rd, rm, ry = report_tuple
    return (year, month, day) <= (ry, rm, rd)


def _is_same_month(date_tuple: _DateTuple, report_ym: tuple[int, int]) -> bool:
    _, em, ey = date_tuple
    rm, ry = report_ym
    return em == rm and ey == ry


def _accumulate_monthly_entry(
    entry: dict[str, Any],
    amount: float,
    *,
    is_cost: bool,
) -> tuple[float, float, str]:
    if not is_cost:
        return amount, 0, ""
    cat = entry.get(_CATEGORY_KEY, "")
    return 0, amount, cat


def _process_storage_entry(
    entry: dict[str, Any],
    parsed_report: _DateTuple,
    report_ym: tuple[int, int],
    category_totals: dict[str, float],
) -> tuple[float, float, float, float]:
    date_tuple = _get_date_tuple(entry)
    if date_tuple is None:
        return 0, 0, 0, 0
    if not _date_leq(date_tuple, parsed_report):
        return 0, 0, 0, 0
    amount = entry.get("amount", 0)
    is_cost = _CATEGORY_KEY in entry
    income = amount * (not is_cost)
    expense = amount * is_cost
    if not _is_same_month(date_tuple, report_ym):
        return income, expense, 0, 0
    mi, me, cat = _accumulate_monthly_entry(entry, amount, is_cost=is_cost)
    if cat:
        category_totals[cat] = category_totals.get(cat, 0) + me
    return income, expense, mi, me


def _collect_stats(parsed_report: _DateTuple) -> _StatsResult:
    report_ym = (parsed_report[1], parsed_report[2])
    total_income: float = 0
    total_expense: float = 0
    month_income: float = 0
    month_expense: float = 0
    category_totals: dict[str, float] = {}
    for entry in financial_transactions_storage:
        if not entry:
            continue
        inc, exp, mi, me = _process_storage_entry(entry, parsed_report, report_ym, category_totals)
        total_income += inc
        total_expense += exp
        month_income += mi
        month_expense += me
    return total_income, total_expense, (month_income, month_expense), category_totals


def _build_category_lines(category_totals: dict[str, float]) -> list[str]:
    sorted_items = sorted(category_totals.items())
    lines = []
    for i, (cat, amt) in enumerate(sorted_items, 1):
        lines.append(f"{i}. {cat}: {amt}")
    return lines


def _format_stats(report_date: str, stats: _StatsResult) -> str:
    total_income, total_expense, month_stats, category_totals = stats
    month_income, month_expense = month_stats
    total_capital = round(total_income - total_expense, 2)
    monthly_diff = round(month_income - month_expense, 2)
    amount_word = "profit" if monthly_diff >= 0 else "loss"
    display_diff = abs(monthly_diff)
    header_lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {total_capital:.2f} rubles",
        f"This month, the {amount_word} amounted to {display_diff:.2f} rubles.",
        f"Income: {month_income:.2f} rubles",
        f"Expenses: {month_expense:.2f} rubles",
        "",
        "Details (category: amount):",
    ]
    return "\n".join(header_lines + _build_category_lines(category_totals))


def stats_handler(report_date: str) -> str:
    parsed_report = extract_date(report_date)
    if parsed_report is None:
        return INCORRECT_DATE_MSG
    stats = _collect_stats(parsed_report)
    return _format_stats(report_date, stats)


def _is_valid_number_str(s: str) -> bool:
    if not s:
        return False
    start = 1 if s[0] == "-" else 0
    if start >= len(s):
        return False
    has_dot = False
    for c in s[start:]:
        if c == ".":
            if has_dot:
                return False
            has_dot = True
        elif not c.isdigit():
            return False
    return s[start:] not in (".", "")


def _parse_amount(s: str) -> float | None:
    normalized = s.replace(",", ".")
    if not _is_valid_number_str(normalized):
        return None
    return float(normalized)


def _handle_income_cmd(parts: list[str]) -> str:
    if len(parts) != _INCOME_CMD_ARGS:
        return UNKNOWN_COMMAND_MSG
    amount = _parse_amount(parts[1])
    if amount is None:
        return UNKNOWN_COMMAND_MSG
    return income_handler(amount, parts[2])


def _handle_cost_cmd(parts: list[str]) -> str:
    if len(parts) == _COST_CATEGORIES_CMD_ARGS and parts[1] == "categories":
        return cost_categories_handler()
    if len(parts) != _COST_CMD_ARGS:
        return UNKNOWN_COMMAND_MSG
    amount = _parse_amount(parts[2])
    if amount is None:
        return UNKNOWN_COMMAND_MSG
    return cost_handler(parts[1], amount, parts[3])


def _handle_stats_cmd(parts: list[str]) -> str:
    if len(parts) != _STATS_CMD_ARGS:
        return UNKNOWN_COMMAND_MSG
    return stats_handler(parts[1])


def _handle_command(parts: list[str]) -> str:
    if not parts:
        return UNKNOWN_COMMAND_MSG
    cmd = parts[0]
    if cmd == "income":
        return _handle_income_cmd(parts)
    if cmd == "cost":
        return _handle_cost_cmd(parts)
    if cmd == "stats":
        return _handle_stats_cmd(parts)
    return UNKNOWN_COMMAND_MSG


def main() -> None:
    while _KEEP_RUNNING:
        line = input()
        parts = line.strip().split()
        if not parts:
            continue
        print(_handle_command(parts))


if __name__ == "__main__":
    main()
