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


def plot_assignment(seats, purchases, assignments, num_rows, num_cols,
                    aisle_cols, title="Asignación de Asientos", figsize=None):
    purchase_map = {p.id: p for p in purchases}

    seat_to_purchase = {}
    for p_id, seat_ids in assignments.items():
        for s_id in seat_ids:
            seat_to_purchase[s_id] = p_id

    num_groups = len(assignments)
    colors = generate_colors(num_groups)
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
        if s.id in seat_to_purchase:
            p_id = seat_to_purchase[s.id]
            color = color_map[p_id]
            ec = 'black'
            lw = 0.8
            alpha = 0.85
        else:
            color = (0.88, 0.88, 0.88)
            ec = 'gray'
            lw = 0.4
            alpha = 0.5

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

        fontsize = max(4, min(7, int(100 / max(num_rows, 1))))

        if s.id in seat_to_purchase:
            p = purchase_map.get(seat_to_purchase[s.id])
            label = f"C{seat_to_purchase[s.id]}"
            if p and p.num_seats > 1:
                label = f"G{seat_to_purchase[s.id]}"
            ax.text(s.col, s.row, label, ha='center', va='center',
                    fontsize=fontsize, color='white', fontweight='bold')

    for ac in aisle_cols:
        ax.axvline(x=ac, color='gray', linestyle='--', alpha=0.4, linewidth=0.8)

    stages = [num_cols / 2]
    ax.text(stages[0], -1.2, "ESCENARIO", ha='center', va='center',
            fontsize=11, fontweight='bold', color='#333333',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#f0e68c', edgecolor='#333'))

    for r in range(num_rows + 1):
        if any(s.row == r for s in seats):
            ax.text(-1.5, r, f"F{r + 1}", ha='center', va='center', fontsize=6, color='#666')

    ax.set_xlim(-2.5, num_cols + 1)
    ax.set_ylim(num_rows + 0.5, -2)
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
    ax.axis('off')

    legend_elements = []
    for p_id in sorted_pids:
        p = purchase_map.get(p_id)
        n = p.num_seats if p else '?'
        color = color_map[p_id]
        legend_elements.append(
            patches.Patch(facecolor=color, edgecolor='black', linewidth=0.5,
                          label=f"Compra {p_id} ({n} as.)")
        )
    if any(s.id not in seat_to_purchase for s in seats):
        legend_elements.append(
            patches.Patch(facecolor=(0.88, 0.88, 0.88), edgecolor='gray',
                          label="Libre")
        )

    ncol = max(1, min(4, len(legend_elements) // (num_rows // 2 + 1) + 1))
    ax.legend(handles=legend_elements, loc='lower center',
              bbox_to_anchor=(0.5, -0.12), ncol=ncol, fontsize=6,
              framealpha=0.9)

    plt.tight_layout()
    return fig


def plot_comparison(results, seats, purchases):
    names = [r.algorithm_name for r in results]
    avg_spreads = [r.metrics.get("avg_spread", 0) for r in results]
    pct_compacts = [r.metrics.get("pct_compact", 0) for r in results]
    avg_pairwise = [r.metrics.get("avg_pairwise_dist", 0) for r in results]
    times = [r.elapsed_time for r in results]

    fig, axes = plt.subplots(1, 4, figsize=(18, 5))

    short_names = [n[:15] + '...' if len(n) > 18 else n for n in names]
    colors_bar = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0'][:len(names)]

    axes[0].barh(short_names, avg_spreads, color=colors_bar[:len(names)])
    axes[0].set_xlabel('Dispersión Promedio')
    axes[0].set_title('Dispersión Promedio\n(menor = mejor)')
    axes[0].invert_yaxis()

    axes[1].barh(short_names, pct_compacts, color=colors_bar[:len(names)])
    axes[1].set_xlabel('% Grupos Compactos')
    axes[1].set_title('Grupos Compactos\n(mayor = mejor)')
    axes[1].invert_yaxis()

    axes[2].barh(short_names, avg_pairwise, color=colors_bar[:len(names)])
    axes[2].set_xlabel('Dist. Intra-grupo Prom.')
    axes[2].set_title('Distancia Intra-grupo\n(menor = mejor)')
    axes[2].invert_yaxis()

    axes[3].barh(short_names, times, color=colors_bar[:len(names)])
    axes[3].set_xlabel('Tiempo (s)')
    axes[3].set_title('Tiempo de Ejecución')
    axes[3].invert_yaxis()

    for ax in axes:
        ax.tick_params(axis='y', labelsize=8)

    plt.suptitle('Comparación de Algoritmos', fontsize=14, fontweight='bold')
    plt.tight_layout()
    return fig