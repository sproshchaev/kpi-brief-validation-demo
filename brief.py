import argparse
import csv
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPORT_WEEK = "2026-11-16"
REPORT_CHANNEL = "web"
METRICS = {"orders": "Оплаченные заказы", "conversion": "Конверсия"}
UNIT_LABEL = {"orders": "заказов", "percent": "%"}


@dataclass(frozen=True)
class Fact:
    week: str
    channel: str
    metric: str
    unit: str
    value: Decimal

    @property
    def id(self):
        return f"{self.week}/{self.channel}/{self.metric}"


def load_facts(source):
    with source.open(newline="", encoding="utf-8") as data, closing(sqlite3.connect(":memory:")) as db:
        db.execute(
            """
            CREATE TABLE daily_totals (
                day TEXT NOT NULL,
                channel TEXT NOT NULL,
                sessions INTEGER NOT NULL CHECK (sessions >= 0),
                orders INTEGER NOT NULL CHECK (orders BETWEEN 0 AND sessions),
                PRIMARY KEY (day, channel)
            )
            """
        )
        # The fixture defines orders as sessions with one paid order at most.
        rows = (
            (date.fromisoformat(row["day"]).isoformat(), row["channel"],
             int(row["sessions"]), int(row["orders"]))
            for row in csv.DictReader(data)
        )
        db.executemany("INSERT INTO daily_totals VALUES (?, ?, ?, ?)", rows)
        facts = {}
        for week, channel, sessions, orders in db.execute((ROOT / "metrics.sql").read_text()):
            count = Fact(week, channel, "orders", "orders", Decimal(orders))
            facts[count.id] = count
            if sessions:
                rate = (Decimal(orders) * 100 / sessions).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                conversion = Fact(week, channel, "conversion", "percent", rate)
                facts[conversion.id] = conversion
        return facts


def validate_and_render(items, facts, week, channel):
    if not isinstance(items, list):
        raise ValueError("invalid response")
    allowed = {}
    for item in items:
        if not isinstance(item, dict) or item.keys() != {"kind", "metric", "unit", "fact_id"}:
            raise ValueError("invalid fields")
        if any(not isinstance(value, str) for value in item.values()):
            raise ValueError("invalid field type")
        if item["kind"] != "observation":
            raise ValueError("unsupported claim")
        metric = item["metric"]
        fact = facts.get(item["fact_id"])
        if fact is None:
            raise ValueError("unknown fact")
        if fact.week != week or fact.channel != channel:
            raise ValueError("wrong scope")
        if metric != fact.metric or item["unit"] != fact.unit:
            raise ValueError("wrong metric or unit")
        if metric in allowed:
            raise ValueError("duplicate metric")
        allowed[metric] = fact
    if allowed.keys() != METRICS.keys():
        raise ValueError("missing required metric")

    lines = [f"Неделя с {week}, канал {channel}"]
    for metric, label in METRICS.items():
        fact = allowed[metric]
        value = str(fact.value).replace(".", ",")
        lines.append(f"- {label}: {value} {UNIT_LABEL[fact.unit]} [{fact.id}]")
    return "\n".join(lines)


def run_cases(cases, facts):
    known_values = {fact.value for fact in facts.values()}
    for case in cases:
        # Intentionally weak baseline: it checks only the numeric values listed
        # in the draft, over both weeks and channels.
        numbers_ok = all(Decimal(value) in known_values for value in case["numbers"])
        try:
            report = validate_and_render(case["items"], facts, REPORT_WEEK, REPORT_CHANNEL)
        except ValueError as error:
            outcome = f"reject ({error})"
        else:
            outcome = "accept"
        print(f"{case['name']} | {'accept' if numbers_ok else 'reject'} | {outcome}")
        if outcome == "accept":
            print(report)


def main():
    parser = argparse.ArgumentParser(description="Compare KPI brief validation policies")
    parser.add_argument("data", type=Path)
    parser.add_argument("cases", type=Path)
    args = parser.parse_args()
    facts = load_facts(args.data)
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    print("source facts")
    for fact in facts.values():
        print(f"{fact.id} | {fact.value} | {fact.unit}")
    print("case | values only | scoped facts")
    run_cases(cases, facts)


if __name__ == "__main__":
    main()
