"""
Day 2 - Sales Analytics Without Pandas
Squad Python Specialization - Data Science, AI & Analytics

Tasks 1-7 use only the standard library. pandas is allowed in task 8, to check your work.
"""
import csv
from pathlib import Path
import re

DATA_PATH = Path("data") / "electronics_sales.csv"


def read_sales(path: Path = DATA_PATH) -> list[dict[str, str]]:
    """Read the CSV with the csv module and return the raw rows."""
    
    with open(path, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError("The CSV file is missing its header.")

        columns = reader.fieldnames
        rows = list(reader)


    return rows


def parse_number(value: str) -> float | None:
    """Convert a messy numeric string to a float, or return None if it cannot be trusted."""
    if value is None:
        return None

    cleaned = value.strip()

    # Reject missing values.
    if not cleaned:
        return None

    # Remove recognized currency labels.
    cleaned = re.sub(r"(?i)KES|KSh", "", cleaned).strip()

    # Remove a leading or trailing currency symbol.
    cleaned = cleaned.strip("₦$€£").strip()

    # Accept correctly grouped thousands separators.
    number_pattern = r"[+-]?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?"

    if not re.fullmatch(number_pattern, cleaned):
        return None

    try:
        return float(cleaned.replace(",", ""))
    except ValueError:
        return None



def convert_rows(rows: list[dict[str, str]]) -> tuple[list[dict], list[dict]]:
    """Convert numeric fields and separate valid from skipped transactions."""

    clean_rows = []
    skipped_rows = []

    for row in rows:
        sale = row.copy()
        reasons = []

        quantity = parse_number(row.get("quantity"))
        unit_price = parse_number(row.get("unit_price_kes"))

        # Validate quantity.
        if quantity is None:
            reasons.append("Missing or invalid quantity")
        elif quantity <= 0:
            reasons.append("Quantity must be positive")
        elif not quantity.is_integer():
            reasons.append("Quantity must be a whole number")

        # Validate unit price.
        if unit_price is None:
            reasons.append("Missing or invalid unit price")
        elif unit_price < 0:
            reasons.append("Unit price cannot be negative")

        # Skip transactions with any validation errors.
        if reasons:
            sale["reason"] = "; ".join(reasons)
            skipped_rows.append(sale)
            continue

        # Store numeric values and calculate revenue.
        sale["quantity"] = int(quantity)
        sale["unit_price_kes"] = unit_price
        sale["revenue"] = sale["quantity"] * sale["unit_price_kes"]

        clean_rows.append(sale)

    return clean_rows, skipped_rows



def total_revenue(rows: list[dict]) -> float:

    return sum(row["revenue"] for row in rows)



def revenue_by(rows: list[dict], field: str) -> dict[str, float]:
    """Calculate total revenue grouped by a specified field."""

    totals = {}

    for row in rows:
        key = row[field]

        if key not in totals:
            totals[key] = 0.0

        totals[key] += row["revenue"]

    return totals




def top_n(totals: dict[str, float], n: int = 3) -> list[tuple[str, float]]:
    """Return the n highest (key, value) pairs, highest first."""

    return sorted(
        totals.items(),
        key=lambda item: (-item[1], item[0])
    )[:n]



def high_value(rows: list[dict], threshold: float) -> list[dict]:
    """Transactions whose revenue is at or above threshold (use a comprehension)."""
    return [row for row in rows if row["revenue"] >= threshold]


# Reusable statistics - implement these yourself, no statistics module.
def mean(values: list[float]) -> float:
    if not values:
        raise ValueError("Cannot calculate the mean of an empty list.")

    return sum(values) / len(values)


def median(values: list[float]) -> float:
    if not values:
        raise ValueError("Cannot calculate the median of an empty list.")

    sorted_values = sorted(values)
    middle = len(sorted_values) // 2

    if len(sorted_values) % 2 == 1:
        return sorted_values[middle]

    return (sorted_values[middle - 1] + sorted_values[middle]) / 2


def minimum_maximum(values: list[float]) -> tuple[float, float]:
    if not values:
        raise ValueError(
            "Cannot calculate minimum and maximum of an empty list."
        )

    minimum = values[0]
    maximum = values[0]

    for value in values[1:]:
        if value < minimum:
            minimum = value
        if value > maximum:
            maximum = value

    return minimum, maximum





def verify_with_pandas(path: Path, my_results: dict) -> list[str]:
    """Verify headline metrics independently with pandas."""

    try:
        import pandas as pd
    except ImportError:
        return [
            "Total revenue      : NOT CHECKED (pandas is not installed)",
            "Revenue by product : NOT CHECKED",
            "Top 3              : NOT CHECKED",
            "Mean / median      : NOT CHECKED",
        ]

    df = pd.read_csv(path, dtype=str, keep_default_na=False)

    # Apply the same parsing and validation rules as the pure Python analysis.
    df["quantity_num"] = df["quantity"].apply(parse_number)
    df["price_num"] = df["unit_price_kes"].apply(parse_number)

    valid_quantity = df["quantity_num"].apply(
        lambda value: (
            value is not None
            and value > 0
            and value.is_integer()
        )
    )
    valid_price = df["price_num"].apply(
        lambda value: value is not None and value >= 0
    )

    valid = df.loc[valid_quantity & valid_price].copy()

    valid["quantity_num"] = valid["quantity_num"].astype(int)
    valid["price_num"] = valid["price_num"].astype(float)
    valid["revenue"] = valid["quantity_num"] * valid["price_num"]

    # Independently calculate the verification metrics.
    pandas_total = float(valid["revenue"].sum())

    pandas_products = {
        product: float(amount)
        for product, amount in
        valid.groupby("product")["revenue"].sum().items()
    }

    pandas_top_three = sorted(
        pandas_products.items(),
        key=lambda item: (-item[1], item[0])
    )[:3]

    pandas_mean = float(valid["revenue"].mean())
    pandas_median = float(valid["revenue"].median())

    def close(a, b):
        return abs(a - b) < 0.005

    def format_amount(value):
        return f"KES {value:,.2f}"

    def product_breakdown_matches():
        expected = my_results["product_totals"]

        return (
            expected.keys() == pandas_products.keys()
            and all(
                close(expected[key], pandas_products[key])
                for key in expected
            )
        )

    def top_three_matches():
        expected = my_results["top_products"]

        return (
            len(expected) == len(pandas_top_three)
            and all(
                name_a == name_b and close(amount_a, amount_b)
                for (name_a, amount_a), (name_b, amount_b)
                in zip(expected, pandas_top_three)
            )
        )

    total_match = close(
        my_results["total_revenue"], pandas_total
    )
    products_match = product_breakdown_matches()
    top_match = top_three_matches()

    mean_match = close(my_results["mean"], pandas_mean)
    median_match = close(my_results["median"], pandas_median)
    stats_match = mean_match and median_match

    total_line = (
        "Total revenue      : MATCH"
        if total_match
        else (
            f"Total revenue      : MISMATCH "
            f"(pure={format_amount(my_results['total_revenue'])}, "
            f"pandas={format_amount(pandas_total)})"
        )
    )

    products_line = (
        "Revenue by product : MATCH"
        if products_match
        else "Revenue by product : MISMATCH (see breakdowns)"
    )

    top_line = (
        "Top 3              : MATCH"
        if top_match
        else f"Top 3              : MISMATCH "
             f"(pure={my_results['top_products']}, "
             f"pandas={pandas_top_three})"
    )

    stats_line = (
        "Mean / median      : MATCH"
        if stats_match
        else (
            "Mean / median      : MISMATCH "
            f"(mean pure={format_amount(my_results['mean'])}, "
            f"pandas={format_amount(pandas_mean)}; "
            f"median pure={format_amount(my_results['median'])}, "
            f"pandas={format_amount(pandas_median)})"
        )
    )

    return [total_line, products_line, top_line, stats_line]





if __name__ == "__main__":
    # Load and clean the data once
    raw_sales = read_sales()
    clean_sales, skipped_sales = convert_rows(raw_sales)

    # Calculate revenue breakdowns
    total = total_revenue(clean_sales)
    product_totals = revenue_by(clean_sales, "product")
    store_totals = revenue_by(clean_sales, "store")
    payment_totals = revenue_by(clean_sales, "payment_method")
    top_products = top_n(product_totals, 3)

    # Identify high-value transactions
    threshold = 50_000
    high_sales = high_value(clean_sales, threshold)

    high_value_counts = {
        store: sum(1 for sale in high_sales if sale["store"] == store)
        for store in sorted({row["store"] for row in clean_sales})
    }

    # Calculate transaction revenue statistics
    revenues = [sale["revenue"] for sale in clean_sales]
    average_revenue = mean(revenues)
    median_revenue = median(revenues)
    lowest_revenue, highest_revenue = minimum_maximum(revenues)

    # Collect results for pandas verification
    my_results = {
        "total_revenue": total,
        "product_totals": product_totals,
        "store_totals": store_totals,
        "payment_totals": payment_totals,
        "top_products": top_products,
        "high_value_count": len(high_sales),
        "mean": average_revenue,
        "median": median_revenue,
        "minimum": lowest_revenue,
        "maximum": highest_revenue,
    }

    # Format skipped transaction details
    skipped_details = ", ".join(
        f"{sale['sale_id']}: {sale['reason']}"
        for sale in skipped_sales
    )

    skipped_line = f"Rows skipped       : {len(skipped_sales)}"
    if skipped_details:
        skipped_line += f"   ({skipped_details})"

    # Build the report
    report = [
        "=== Sales report: September 2026 ===",
        f"Rows read          : {len(raw_sales)}",
        f"Rows used          : {len(clean_sales)}",
        skipped_line,
        "",
        f"Total revenue (KES): {total:,.2f}",
        "",
        "Revenue by product (KES)",
    ]

    for product, amount in sorted(
        product_totals.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        report.append(f"  {product:<26} {amount:>12,.2f}")

    report.extend(["", "Top 3 products"])

    for rank, (product, amount) in enumerate(top_products, start=1):
        report.append(f"  {rank}. {product} - KES {amount:,.2f}")

    report.extend([
        "",
        f"High-value transactions (>= KES {threshold:,.0f}): "
        f"{len(high_sales)}",
    ])

    for sale in high_sales:
        report.append(
            f"  {sale['sale_id']}  {sale['sale_date']}  "
            f"{sale['store']}  {sale['product']}  "
            f"KES {sale['revenue']:,.2f}"
        )

    report.extend(["", "High-value transaction count by store"])

    for store, count in high_value_counts.items():
        report.append(f"  {store}: {count}")

    report.extend([
        "",
        "Transaction revenue statistics",
        f"  mean   : {average_revenue:,.2f}",
        f"  median : {median_revenue:,.2f}",
        f"  min    : {lowest_revenue:,.2f}",
        f"  max    : {highest_revenue:,.2f}",
        "",
        "=== pandas verification ===",
    ])

    report.extend(verify_with_pandas(DATA_PATH, my_results))

    # Save and display the report
    output_path = Path("output") / "sales_report.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report_text = "\n".join(report) + "\n"
    output_path.write_text(report_text, encoding="utf-8")

    print(report_text)
    print(f"Report saved to: {output_path}")




