import csv
import sys
from datetime import date, timedelta


def main():
    first_week = date(2026, 11, 9)
    # Deliberate collisions in counts across weeks and channels.
    daily_totals = (
        (0, "web", 180, 9),
        (1, "web", 220, 11),
        (0, "app", 100, 6),
        (1, "app", 100, 9),
        (7, "web", 200, 8),
        (8, "web", 300, 12),
        (7, "app", 100, 11),
        (8, "app", 150, 9),
    )
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(("day", "channel", "sessions", "orders"))
    for offset, channel, sessions, orders in daily_totals:
        writer.writerow((first_week + timedelta(days=offset), channel, sessions, orders))


if __name__ == "__main__":
    main()
