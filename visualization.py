import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from models import Seat, Purchase


def generate_colors(n):
    if n <= 10:
        cmap = plt.cm.tab10
    elif n <= 20:
        cmap = plt.cm.tab20
    else:
        cmap = plt.cm.hsv

    colors = [cmap(i / max(n, 1)) for i in range(n)]
    np.random.seed(42)
    np.random.shuffle(colors)
    return colors


COLOR_OCCUPIED = (0.55, 0.55, 0.55)
COLOR_FREE = (1.0, 0.75, 0.80)
COLOR_FREE_LABEL = (0.7, 0.2, 0.3)


def plot_initial(seats, num_rows, num_cols, aisle_cols,
                 title="Venue Layout", figsize=None):
    if figsize is None:
        w = max(10, num_cols * 0.55)
        h = max(5, num_rows * 0.7)
        figsize = (w, h)

    fig, ax = plt.subplots(1, 1, figsize=figsize)
    seat_w = 0.8
    seat_h = 0.6

    for s in seats:
        if s.occupied:
            color = COLOR_OCCUPIED
            ec = '#444444'
            lw = 0.8
            alpha = 0.9
            label = "X"
            label_color = 'white'
        else:
            color = COLOR_FREE
            ec = (0.85, 0.4, 0.5)
            lw = 0.6
            alpha = 0.85
            label = ""
            label_color = COLOR_FREE_LABEL

        rect = patches.FancyBboxPatch(
            (s.col - seat_w / 2, s.row - seat_h / 2),
            seat_w, seat_h,
            boxstyle="round,pad=0.05",
            facecolor=color,
            edgecolor=ec,
            linewidth=lw,
            alpha=alpha
        )
        ax.add_patch(rect)

        if label:
            fontsize = max(4, min(7, int(100 / max(num_rows, 1))))
            ax.text(s.col, s.row, label, ha='center', va='center',
                    fontsize=fontsize, color=label_color, fontweight='bold')

    stages = [num_cols / 2]
    ax.text(stages[0], -1.2, "STAGE", ha='center', va='center',
            fontsize=11, fontweight='bold', color='#333333',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#f0e68c', edgecolor='#333'))

    for ac in aisle_cols:
        ax.axvline(x=ac, color='gray', linestyle='--', alpha=0.4, linewidth=0.8)

    for r in range(num_rows + 1):
        if any(s.row == r for s in seats):
            ax.text(-1.5, r, f"R{r + 1}", ha='center', va='center', fontsize=6, color='#666')

    occupied_count = len([s for s in seats if s.occupied])
    free_count = len([s for s in seats if not s.occupied])

    legend_elements = [
        patches.Patch(facecolor=COLOR_FREE, edgecolor=(0.85, 0.4, 0.5),
                       label=f"Free ({free_count})"),
        patches.Patch(facecolor=COLOR_OCCUPIED, edgecolor='#444444',
                       label=f"Occupied ({occupied_count})"),
    ]
    ax.legend(handles=legend_elements, loc='lower center',
              bbox_to_anchor=(0.5, -0.10), ncol=2, fontsize=8,
              framealpha=0.9)

    ax.set_xlim(-2.5, num_cols + 1)
    ax.set_ylim(num_rows + 0.5, -2)
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
    ax.axis('off')

    plt.tight_layout()
    return fig


def plot_assignment(seats, purchases, assignments, num_rows, num_cols,
                    aisle_cols, title="Seat Assignment", figsize=None):
    purchase_map = {p.id: p for p in purchases}

    seat_to_purchase = {}
    for p_id, seat_ids in assignments.items():
        for s_id in seat_ids:
            seat_to_purchase[s_id] = p_id

    num_groups = len(assignments)
    colors = generate_colors(max(num_groups, 1))
    color_map = {}
    sorted_pids = sorted(assignments.keys())
    for i, p_id in enumerate(sorted_pids):
        color_map[p_id] = colors[i]

    if figsize is None:
        w = max(10, num_cols * 0.55)
        h = max(5, num_rows * 0.7)
        figsize = (w, h)

    fig, ax = plt.subplots(1, 1, figsize=figsize)
    seat_w = 0.8
    seat_h = 0.6

    for s in seats:
        if s.occupied:
            color = COLOR_OCCUPIED
            ec = '#444444'
            lw = 0.8
            alpha = 0.9
            label = "X"
            label_color = 'white'
        elif s.id in seat_to_purchase:
            p_id = seat_to_purchase[s.id]
            color = color_map[p_id]
            ec = 'black'
            lw = 0.8
            alpha = 0.9
            label = str(p_id)
            label_color = 'white'
        else:
            color = COLOR_FREE
            ec = (0.85, 0.4, 0.5)
            lw = 0.6
            alpha = 0.5
            label = ""
            label_color = COLOR_FREE_LABEL

        rect = patches.FancyBboxPatch(
            (s.col - seat_w / 2, s.row - seat_h / 2),
            seat_w, seat_h,
            boxstyle="round,pad=0.05",
            facecolor=color,
            edgecolor=ec,
            linewidth=lw,
            alpha=alpha
        )
        ax.add_patch(rect)

        if label:
            fontsize = max(4, min(8, int(120 / max(num_rows, 1))))
            ax.text(s.col, s.row, label, ha='center', va='center',
                    fontsize=fontsize, color=label_color, fontweight='bold')

    stages = [num_cols / 2]
    ax.text(stages[0], -1.2, "STAGE", ha='center', va='center',
            fontsize=11, fontweight='bold', color='#333333',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#f0e68c', edgecolor='#333'))

    for ac in aisle_cols:
        ax.axvline(x=ac, color='gray', linestyle='--', alpha=0.4, linewidth=0.8)

    for r in range(num_rows + 1):
        if any(s.row == r for s in seats):
            ax.text(-1.5, r, f"R{r + 1}", ha='center', va='center', fontsize=6, color='#666')

    legend_elements = []
    for p_id in sorted_pids:
        p = purchase_map.get(p_id)
        n = p.num_seats if p else '?'
        color = color_map[p_id]
        legend_elements.append(
            patches.Patch(facecolor=color, edgecolor='black', linewidth=0.5,
                          label=f"P{p_id} ({n} seat{'s' if n > 1 else ''})")
        )

    free_remaining = len([s for s in seats if not s.occupied and s.id not in seat_to_purchase])
    occupied_count = len([s for s in seats if s.occupied])

    if free_remaining > 0:
        legend_elements.append(
            patches.Patch(facecolor=COLOR_FREE, edgecolor=(0.85, 0.4, 0.5),
                          label=f"Free ({free_remaining})")
        )
    if occupied_count > 0:
        legend_elements.append(
            patches.Patch(facecolor=COLOR_OCCUPIED, edgecolor='#444444',
                          label=f"Occupied ({occupied_count})")
        )

    ncol = max(1, min(5, len(legend_elements) // (num_rows // 3 + 1) + 1))
    ax.legend(handles=legend_elements, loc='lower center',
              bbox_to_anchor=(0.5, -0.12), ncol=ncol, fontsize=6,
              framealpha=0.9)

    ax.set_xlim(-2.5, num_cols + 1)
    ax.set_ylim(num_rows + 0.5, -2)
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
    ax.axis('off')

    plt.tight_layout()
    return fig


def plot_comparison(results, seats, purchases):
    names = [r.algorithm_name for r in results]
    avg_spreads = [r.metrics.get("avg_spread", 0) for r in results]
    pct_compacts = [r.metrics.get("pct_compact", 0) for r in results]
    avg_pairwise = [r.metrics.get("avg_pairwise_dist", 0) for r in results]
    times = [r.elapsed_time for r in results]

    fig, axes = plt.subplots(1, 4, figsize=(18, 5))

    short_names = [n[:18] + '...' if len(n) > 20 else n for n in names]
    colors_bar = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0'][:len(names)]

    axes[0].barh(short_names, avg_spreads, color=colors_bar[:len(names)])
    axes[0].set_xlabel('Avg Spread')
    axes[0].set_title('Avg Spread\n(lower = better)')
    axes[0].invert_yaxis()

    axes[1].barh(short_names, pct_compacts, color=colors_bar[:len(names)])
    axes[1].set_xlabel('% Compact Groups')
    axes[1].set_title('Compact Groups\n(higher = better)')
    axes[1].invert_yaxis()

    axes[2].barh(short_names, avg_pairwise, color=colors_bar[:len(names)])
    axes[2].set_xlabel('Avg Intra-group Dist.')
    axes[2].set_title('Intra-group Distance\n(lower = better)')
    axes[2].invert_yaxis()

    axes[3].barh(short_names, times, color=colors_bar[:len(names)])
    axes[3].set_xlabel('Time (s)')
    axes[3].set_title('Execution Time')
    axes[3].invert_yaxis()

    for ax in axes:
        ax.tick_params(axis='y', labelsize=8)

    plt.suptitle('Algorithm Comparison', fontsize=14, fontweight='bold')
    plt.tight_layout()
    return fig