import random
import math
from models import Seat, Purchase


def generate_layout(total_seats=None, num_rows=None, num_cols=None,
                    num_aisles=2, gap_probability=0.05,
                    occupied_ratio=0.15, seed=None):
    if seed is not None:
        random.seed(seed)

    if total_seats is None:
        total_seats = random.randint(40, 200)

    if num_rows is None and num_cols is None:
        ratio = random.uniform(1.4, 2.2)
        num_cols = max(6, int(math.sqrt(total_seats * ratio)))
        num_rows = max(4, math.ceil(total_seats / num_cols))

    actual_cols = num_cols
    aisle_cols = set()
    if num_aisles > 0 and actual_cols > 6:
        step = actual_cols / (num_aisles + 1)
        for i in range(1, num_aisles + 1):
            aisle_cols.add(int(step * i))

    candidates = []
    for r in range(num_rows):
        for c in range(actual_cols):
            if c in aisle_cols:
                continue
            if random.random() < gap_probability:
                continue
            candidates.append((r, c))

    if len(candidates) < total_seats:
        extra_needed = total_seats - len(candidates)
        r = num_rows
        while extra_needed > 0:
            for c in range(actual_cols):
                if c not in aisle_cols:
                    candidates.append((r, c))
                    extra_needed -= 1
                    if extra_needed <= 0:
                        break
            r += 1
        num_rows = r

    if len(candidates) > total_seats:
        random.shuffle(candidates)
        candidates = candidates[:total_seats]

    candidates.sort(key=lambda x: (x[0], x[1]))

    num_occupied = max(1, int(total_seats * occupied_ratio)) if occupied_ratio > 0 else 0
    occupied_indices = set(random.sample(range(len(candidates)), num_occupied))

    seats = []
    for i, (r, c) in enumerate(candidates):
        seats.append(Seat(id=i, row=r, col=c, occupied=(i in occupied_indices)))

    actual_max_col = max(s.col for s in seats) if seats else num_cols
    actual_max_row = max(s.row for s in seats) if seats else num_rows

    return seats, actual_max_row + 1, actual_max_col + 1, aisle_cols


def generate_purchases(available_seats, num_purchases=None, seed=None):
    if seed is not None:
        random.seed(seed + 100)

    if num_purchases is None:
        num_purchases = random.randint(
            max(5, available_seats // 10),
            max(8, available_seats // 4)
        )
    num_purchases = max(1, min(num_purchases, available_seats))

    sizes = [1] * num_purchases
    remaining = available_seats - num_purchases

    if remaining < 0:
        num_purchases = available_seats
        sizes = [1] * num_purchases
        remaining = 0

    max_group = max(2, available_seats // num_purchases + 2)

    attempts = 0
    while remaining > 0 and attempts < available_seats * 10:
        attempts += 1
        idx = random.randint(0, num_purchases - 1)

        roll = random.random()
        if roll < 0.5:
            add = 1
        elif roll < 0.75:
            add = random.randint(1, 2)
        elif roll < 0.9:
            add = random.randint(2, min(4, max_group))
        else:
            add = random.randint(3, min(8, max_group))

        add = min(add, remaining)
        sizes[idx] += add
        remaining -= add

    random.shuffle(sizes)

    purchases = [Purchase(id=i, num_seats=s, order=i) for i, s in enumerate(sizes)]
    return purchases