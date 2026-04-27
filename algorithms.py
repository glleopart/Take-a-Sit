import math
import random
import time
from models import Seat, Purchase, AssignmentResult


def euclidean(s1, s2):
    return math.sqrt((s1.row - s2.row) ** 2 + (s1.col - s2.col) ** 2)


def manhattan(s1, s2):
    return abs(s1.row - s2.row) + abs(s1.col - s2.col)


def compute_spread(seat_ids, seat_map):
    if len(seat_ids) <= 1:
        return 0
    rows = [seat_map[s].row for s in seat_ids]
    cols = [seat_map[s].col for s in seat_ids]
    return (max(rows) - min(rows)) + (max(cols) - min(cols))


def get_free_seats(seats):
    return [s for s in seats if not s.occupied]


def find_best_group(available_ids, seat_map, n, seed_limit=50):
    if n <= 0 or not available_ids:
        return []
    if n == 1:
        return [min(available_ids, key=lambda s: (seat_map[s].row, seat_map[s].col))]

    available_list = list(available_ids)
    if len(available_list) <= seed_limit:
        seeds = available_list
    else:
        seeds = random.sample(available_list, seed_limit)

    best_group = None
    best_score = float('inf')

    for seed in seeds:
        group = [seed]
        remaining = set(available_ids) - {seed}

        for _ in range(n - 1):
            if not remaining:
                break
            closest = None
            closest_dist = float('inf')
            for s in remaining:
                d = min(euclidean(seat_map[s], seat_map[g]) for g in group)
                if d < closest_dist:
                    closest_dist = d
                    closest = s
            if closest is not None:
                group.append(closest)
                remaining.remove(closest)

        if len(group) < n:
            continue

        score = compute_spread(group, seat_map)
        if score < best_score:
            best_score = score
            best_group = list(group)

    return best_group if best_group else []


def greedy_assign(seats, purchases, sort_key, seed_limit=50, name="Greedy"):
    start = time.time()
    free_seats = get_free_seats(seats)
    seat_map = {s.id: s for s in seats}
    available = set(s.id for s in free_seats)
    assignments = {}

    for purchase in sorted(purchases, key=sort_key):
        group = find_best_group(available, seat_map, purchase.num_seats, seed_limit=seed_limit)
        if group:
            assignments[purchase.id] = group
            for s_id in group:
                available.remove(s_id)

    elapsed = time.time() - start
    metrics = compute_metrics(seats, purchases, assignments)
    return AssignmentResult(
        algorithm_name=name,
        assignments=assignments,
        metrics=metrics,
        elapsed_time=elapsed
    )


def greedy_by_order(seats, purchases):
    return greedy_assign(
        seats, purchases,
        sort_key=lambda p: p.order,
        seed_limit=30,
        name="Greedy by Order"
    )


def greedy_by_group_size(seats, purchases):
    return greedy_assign(
        seats, purchases,
        sort_key=lambda p: (-p.num_seats, p.order),
        seed_limit=30,
        name="Greedy by Group Size"
    )


def greedy_compact(seats, purchases):
    return greedy_assign(
        seats, purchases,
        sort_key=lambda p: (-p.num_seats, p.order),
        seed_limit=300,
        name="Greedy Compact"
    )


def ilp_pulp(seats, purchases, time_limit=60):
    start = time.time()
    try:
        import pulp
    except ImportError:
        return AssignmentResult(
            algorithm_name="ILP (PuLP)",
            assignments={},
            metrics={"error": "PuLP not installed. Run: pip install pulp"},
            elapsed_time=0
        )

    seat_map = {s.id: s for s in seats}
    free_seats = get_free_seats(seats)
    P = len(purchases)
    S = len(free_seats)

    total_x_vars = P * S
    if total_x_vars > 10000:
        fallback = greedy_by_group_size(seats, purchases)
        fallback.metrics["solver_status"] = "Skipped"
        fallback.metrics["note"] = f"Instance too large ({total_x_vars} vars). Greedy used instead."
        return AssignmentResult(
            algorithm_name="ILP (PuLP)",
            assignments=fallback.assignments,
            metrics=fallback.metrics,
            elapsed_time=time.time() - start
        )

    greedy_init = greedy_by_group_size(seats, purchases)

    prob = pulp.LpProblem("SeatAssignment", pulp.LpMinimize)

    x = {}
    for p in purchases:
        for s in free_seats:
            x[p.id, s.id] = pulp.LpVariable(f"x_{p.id}_{s.id}", cat='Binary')

    for p in purchases:
        prob += pulp.lpSum(x[p.id, s.id] for s in free_seats) == p.num_seats

    for s in free_seats:
        prob += pulp.lpSum(x[p.id, s.id] for p in purchases) <= 1

    r_min = {p.id: pulp.LpVariable(f"rmin_{p.id}", lowBound=0) for p in purchases}
    r_max = {p.id: pulp.LpVariable(f"rmax_{p.id}", lowBound=0) for p in purchases}
    c_min = {p.id: pulp.LpVariable(f"cmin_{p.id}", lowBound=0) for p in purchases}
    c_max = {p.id: pulp.LpVariable(f"cmax_{p.id}", lowBound=0) for p in purchases}

    max_row_val = max(s.row for s in free_seats)
    max_col_val = max(s.col for s in free_seats)
    big_M = max(max_row_val, max_col_val) + 1

    for p in purchases:
        r_min[p.id].upBound = max_row_val
        r_max[p.id].upBound = max_row_val
        c_min[p.id].upBound = max_col_val
        c_max[p.id].upBound = max_col_val

    for p in purchases:
        for s in free_seats:
            prob += r_min[p.id] <= s.row + big_M * (1 - x[p.id, s.id])
            prob += r_max[p.id] >= s.row - big_M * (1 - x[p.id, s.id])
            prob += c_min[p.id] <= s.col + big_M * (1 - x[p.id, s.id])
            prob += c_max[p.id] >= s.col - big_M * (1 - x[p.id, s.id])

    spread_obj = pulp.lpSum(
        (r_max[p.id] - r_min[p.id]) + (c_max[p.id] - c_min[p.id])
        for p in purchases
    )

    epsilon = 0.01 / max(P, 1)
    front_obj = pulp.lpSum(
        s.row * x[p.id, s.id]
        for p in purchases for s in free_seats
    )
    prob += spread_obj + epsilon * front_obj

    solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit)
    prob.solve(solver)

    status = pulp.LpStatus[prob.status]

    assignments = {}
    all_correct = True
    for p in purchases:
        assigned = [
            s.id for s in free_seats
            if pulp.value(x[p.id, s.id]) is not None
            and pulp.value(x[p.id, s.id]) > 0.5
        ]
        if len(assigned) == p.num_seats:
            assignments[p.id] = assigned
        else:
            all_correct = False

    if not all_correct or len(assignments) != P:
        assignments = {k: list(v) for k, v in greedy_init.assignments.items()}

    ilp_metrics = compute_metrics(seats, purchases, assignments)
    greedy_metrics = greedy_init.metrics

    if ilp_metrics.get("total_spread", float('inf')) > greedy_metrics.get("total_spread", float('inf')):
        assignments = {k: list(v) for k, v in greedy_init.assignments.items()}
        ilp_metrics = dict(greedy_metrics)
        ilp_metrics["note"] = "Greedy solution (better than ILP)"

    elapsed = time.time() - start
    ilp_metrics["solver_status"] = status
    ilp_metrics["objective_value"] = round(pulp.value(prob.objective), 4) if prob.objective else None

    return AssignmentResult(
        algorithm_name="ILP (PuLP)",
        assignments=assignments,
        metrics=ilp_metrics,
        elapsed_time=elapsed
    )


def local_search(seats, purchases, initial_result=None, max_no_improve=3, seed=None):
    start = time.time()
    if seed is not None:
        random.seed(seed)

    seat_map = {s.id: s for s in seats}

    if initial_result is not None:
        assignments = {k: list(v) for k, v in initial_result.assignments.items()}
    else:
        base = greedy_by_group_size(seats, purchases)
        assignments = {k: list(v) for k, v in base.assignments.items()}

    no_improve_count = 0
    total_iterations = 0
    total_improvements = 0

    purchase_ids = list(assignments.keys())

    while no_improve_count < max_no_improve and time.time() - start < 60:
        improved_round = False
        total_iterations += 1

        for i in range(len(purchase_ids)):
            for j in range(i + 1, len(purchase_ids)):
                p_a = purchase_ids[i]
                p_b = purchase_ids[j]

                group_a = list(assignments[p_a])
                group_b = list(assignments[p_b])

                best_improvement = 0
                best_swap = None

                for s_a in group_a:
                    for s_b in group_b:
                        new_a = [s for s in group_a if s != s_a] + [s_b]
                        new_b = [s for s in group_b if s != s_b] + [s_a]

                        old_sp = compute_spread(group_a, seat_map) + compute_spread(group_b, seat_map)
                        new_sp = compute_spread(new_a, seat_map) + compute_spread(new_b, seat_map)

                        improvement = old_sp - new_sp
                        if improvement > best_improvement:
                            best_improvement = improvement
                            best_swap = (s_a, s_b)

                if best_swap is not None and best_improvement > 0:
                    s_a, s_b = best_swap
                    assignments[p_a] = [s for s in assignments[p_a] if s != s_a] + [s_b]
                    assignments[p_b] = [s for s in assignments[p_b] if s != s_b] + [s_a]
                    improved_round = True
                    total_improvements += 1

        if not improved_round:
            no_improve_count += 1
        else:
            no_improve_count = 0

    elapsed = time.time() - start
    metrics = compute_metrics(seats, purchases, assignments)
    metrics["iterations"] = total_iterations
    metrics["improvements"] = total_improvements

    base_name = initial_result.algorithm_name if initial_result else "Greedy by Group Size"
    return AssignmentResult(
        algorithm_name=f"Local Search (from {base_name})",
        assignments=assignments,
        metrics=metrics,
        elapsed_time=elapsed
    )


def compute_metrics(seats, purchases, assignments):
    seat_map = {s.id: s for s in seats}
    purchase_map = {p.id: p for p in purchases}

    total_spread = 0
    total_avg_pairwise = 0
    groups_compact = 0
    groups_total = len(assignments)
    group_details = []

    for p_id, seat_ids in assignments.items():
        p = purchase_map.get(p_id)
        if len(seat_ids) <= 1:
            spread = 0
            avg_pairwise = 0
            groups_compact += 1
        else:
            rows = [seat_map[s].row for s in seat_ids]
            cols = [seat_map[s].col for s in seat_ids]
            spread = (max(rows) - min(rows)) + (max(cols) - min(cols))
            if spread <= 1:
                groups_compact += 1

            pairwise_sum = 0
            count = 0
            for i in range(len(seat_ids)):
                for j in range(i + 1, len(seat_ids)):
                    pairwise_sum += euclidean(seat_map[seat_ids[i]], seat_map[seat_ids[j]])
                    count += 1
            avg_pairwise = pairwise_sum / count if count > 0 else 0

        total_spread += spread
        total_avg_pairwise += avg_pairwise

        group_details.append({
            "purchase_id": p_id,
            "num_seats": p.num_seats if p else len(seat_ids),
            "order": p.order if p else -1,
            "spread": spread,
            "avg_pairwise": round(avg_pairwise, 2),
            "is_compact": spread <= 1
        })

    assigned_seats = sum(len(v) for v in assignments.values())
    free_seats = len([s for s in seats if not s.occupied])
    total_seats = len(seats)

    return {
        "avg_spread": round(total_spread / groups_total, 2) if groups_total > 0 else 0,
        "total_spread": round(total_spread, 2),
        "avg_pairwise_dist": round(total_avg_pairwise / groups_total, 2) if groups_total > 0 else 0,
        "groups_compact": groups_compact,
        "groups_total": groups_total,
        "pct_compact": round(groups_compact / groups_total * 100, 1) if groups_total > 0 else 0,
        "seats_assigned": assigned_seats,
        "seats_free": free_seats,
        "seats_occupied": total_seats - free_seats,
        "seats_total": total_seats,
        "fill_rate": round(assigned_seats / free_seats * 100, 1) if free_seats > 0 else 0,
        "group_details": group_details
    }