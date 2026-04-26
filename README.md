# Take-a-Sit

Seat assignment optimization system with multiple algorithms and an interactive Streamlit dashboard.

## Overview

Take-a-Sit generates a random venue layout with seats, aisles, and gaps, then assigns groups of seats to purchases using different optimization strategies. Each algorithm minimizes group dispersion (how spread out a group's seats are) while respecting different priorities.

### Metrics

- **Spread** — Bounding box per group: `(max_row - min_row) + (max_col - min_col)`. Lower is better.
- **Compact group** — A group with spread ≤ 1 (all seats adjacent).
- **Average pairwise distance** — Mean Euclidean distance between all seat pairs within a group.

## Algorithms

| # | Algorithm | Priority |
|---|-----------|----------|
| 1 | **Greedy by Purchase Order** | First-come-first-served; assigns the most compact block available to each purchase in order |
| 2 | **Greedy by Group Size** | Largest groups first, then smaller groups, individuals last |
| 3 | **Greedy Compact** | Same order as #2 but exhaustively searches more seed positions for tighter blocks |
| 4 | **ILP (PuLP)** | Integer Linear Programming — minimizes total bounding-box spread globally using CBC solver. Falls back to Greedy if the instance is too large or the ILP solution is worse |
| 5 | **Local Search** | Starts from algorithm #2 and iteratively swaps seats between groups to reduce total spread |

## Project Structure

```
Take-a-Sit/
├── app.py              Streamlit dashboard
├── models.py           Seat, Purchase, AssignmentResult dataclasses
├── layout.py           Random venue and purchase generation
├── algorithms.py       All five assignment algorithms
├── visualization.py    Matplotlib seat-map and comparison charts
└── requirements.txt    Python dependencies
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

The dashboard opens in your browser with the following workflow:

1. **Configure** — Use the sidebar to set the number of seats, rows, columns, aisles, purchase count, and random seed.
2. **Generate** — Click **Generate Layout & Purchases** to create a random venue and purchase list.
3. **View** — The empty seat map and purchase table are displayed.
4. **Run algorithms** — Click any algorithm button to execute it. Results are stored and can be compared.
5. **Compare** — When two or more algorithms have been run, a comparison table and bar charts appear automatically.

### Programmatic usage

```python
from layout import generate_layout, generate_purchases
from algorithms import greedy_by_order, greedy_by_group_size, greedy_compact, local_search

seats, num_rows, num_cols, aisle_cols = generate_layout(total_seats=60, seed=42)
purchases = generate_purchases(len(seats), num_purchases=12, seed=42)

result = greedy_by_group_size(seats, purchases)
print(f"Avg spread: {result.metrics['avg_spread']}")
print(f"Compact groups: {result.metrics['pct_compact']}%")

for purchase_id, seat_ids in result.assignments.items():
    print(f"Purchase {purchase_id}: seats {seat_ids}")
```

For the ILP solver:

```python
from algorithms import ilp_pulp

result = ilp_pulp(seats, purchases, time_limit=60)
print(f"Solver status: {result.metrics.get('solver_status')}")
```

> **Note:** The ILP solver uses big-M constraints with CBC. For instances larger than ~100 seats with 10+ purchases it may time out. The function automatically falls back to the Greedy by Group Size solution if the ILP fails or produces a worse result.

## Dependencies

- **streamlit** ≥ 1.28 — Interactive dashboard
- **pulp** ≥ 2.7 — Integer Linear Programming solver (CBC)
- **matplotlib** ≥ 3.7 — Seat-map visualization
- **numpy** ≥ 1.24 — Numerical operations