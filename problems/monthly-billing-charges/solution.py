"""Solution for: Monthly Billing Charges"""

from __future__ import annotations

from collections import defaultdict


class Solution:
    def calculateMonthlyCharges(
        self,
        subscriptions: list[str],
        changes: list[str],
        pricing: list[str],
        usage: list[str],
    ) -> list[list[str]]:
        CYCLE_DAYS = 30

        # user -> scaled subscription cents * 30 (i.e. sum of cost * days_active)
        sub_scaled: dict[str, int] = defaultdict(int)
        users: set[str] = set()

        # Active subscription versions: sub_id -> (user_id, monthly_cost, start_day)
        active: dict[str, tuple[str, int, int]] = {}

        for row in subscriptions:
            user_id, sub_id, cost_s = row.split(",")
            cost = int(cost_s)
            users.add(user_id)
            active[sub_id] = (user_id, cost, 1)

        parsed_changes: list[tuple[int, str, str, str, int]] = []
        for row in changes:
            user_id, old_id, new_id, cost_s, day_s = row.split(",")
            parsed_changes.append((int(day_s), user_id, old_id, new_id, int(cost_s)))
            users.add(user_id)

        # Apply chronologically; independent chains may share a day.
        parsed_changes.sort(key=lambda c: c[0])

        for day, user_id, old_id, new_id, new_cost in parsed_changes:
            if old_id != "-":
                old_user, old_cost, start_day = active.pop(old_id)
                # Active from start_day through day-1 inclusive
                end_day = day - 1
                if end_day >= start_day:
                    sub_scaled[old_user] += old_cost * (end_day - start_day + 1)
            active[new_id] = (user_id, new_cost, day)

        # Close remaining active versions through day 30
        for user_id, cost, start_day in active.values():
            sub_scaled[user_id] += cost * (CYCLE_DAYS - start_day + 1)
            users.add(user_id)

        # Pricing tiers per product: list of (upper_bound or None, unit_price)
        tiers_by_product: dict[str, list[tuple[int | None, int]]] = defaultdict(list)
        for row in pricing:
            product_id, bound_s, price_s = row.split(",")
            bound = int(bound_s)
            price = int(price_s)
            tiers_by_product[product_id].append(
                (None if bound == -1 else bound, price)
            )

        def sorted_tiers(tiers: list[tuple[int | None, int]]) -> list[tuple[int | None, int]]:
            finite = sorted(((b, p) for b, p in tiers if b is not None), key=lambda x: x[0])
            unlimited = [(b, p) for b, p in tiers if b is None]
            return finite + unlimited

        product_tiers = {
            pid: sorted_tiers(tiers) for pid, tiers in tiers_by_product.items()
        }

        # Aggregate usage quantities per (user, product)
        qty: dict[tuple[str, str], int] = defaultdict(int)
        for row in usage:
            user_id, product_id, quantity_s = row.split(",")
            qty[(user_id, product_id)] += int(quantity_s)
            users.add(user_id)

        def usage_charge(product_id: str, quantity: int) -> int:
            if quantity == 0:
                return 0
            tiers = product_tiers[product_id]
            remaining = quantity
            prev_bound = 0
            total = 0
            for bound, price in tiers:
                if remaining <= 0:
                    break
                if bound is None:
                    total += remaining * price
                    remaining = 0
                    break
                # Units in (prev_bound, bound]
                capacity = bound - prev_bound
                take = min(remaining, capacity)
                total += take * price
                remaining -= take
                prev_bound = bound
            return total

        usage_cents: dict[str, int] = defaultdict(int)
        for (user_id, product_id), quantity in qty.items():
            usage_cents[user_id] += usage_charge(product_id, quantity)

        result: list[list[str]] = []
        for user_id in sorted(users):
            # floor(sub_scaled/30 + usage) = floor((sub_scaled + 30*usage) / 30)
            total = (sub_scaled[user_id] + CYCLE_DAYS * usage_cents[user_id]) // CYCLE_DAYS
            result.append([user_id, str(total)])
        return result
