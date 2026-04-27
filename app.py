import streamlit as st
import pandas as pd
from models import Seat, Purchase
from layout import generate_layout, generate_purchases
from algorithms import (
    greedy_by_order, greedy_by_group_size, greedy_compact,
    ilp_pulp, local_search, get_free_seats
)
from visualization import plot_initial, plot_assignment, plot_comparison

st.set_page_config(page_title="Take-a-Sit", page_icon="🪑", layout="wide")

st.title("🪑 Take-a-Sit")
st.subheader("Seat Assignment Optimization System")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Configuration")

    st.subheader("Venue Layout")
    total_seats = st.slider("Total seats", min_value=20, max_value=300, value=80, step=5)
    num_rows = st.slider("Rows", min_value=3, max_value=20, value=0, step=1,
                          help="0 = auto")
    num_cols = st.slider("Columns", min_value=5, max_value=30, value=0, step=1,
                          help="0 = auto")
    num_aisles = st.slider("Aisles", min_value=0, max_value=4, value=2)
    gap_prob = st.slider("Gap probability", min_value=0.0, max_value=0.3, value=0.05, step=0.01)
    occupied_ratio = st.slider("Pre-occupied seats %", min_value=0.0, max_value=0.5, value=0.15, step=0.01,
                               help="Percentage of seats already taken before optimization")

    st.subheader("Purchases / Groups")
    num_purchases = st.slider("Number of purchases", min_value=3, max_value=60, value=15)

    st.subheader("Random Seed")
    seed = st.number_input("Seed", min_value=0, max_value=9999, value=42)

    st.markdown("---")
    if st.button("🎲 Generate Layout & Purchases", use_container_width=True, type="primary"):
        layout_data = generate_layout(
            total_seats=total_seats,
            num_rows=num_rows if num_rows > 0 else None,
            num_cols=num_cols if num_cols > 0 else None,
            num_aisles=num_aisles,
            gap_probability=gap_prob,
            occupied_ratio=occupied_ratio,
            seed=seed
        )
        seats_actual, rows_actual, cols_actual, aisles_actual = layout_data

        free_count = len(get_free_seats(seats_actual))
        purchases = generate_purchases(free_count, num_purchases=num_purchases, seed=seed)

        st.session_state['seats'] = seats_actual
        st.session_state['purchases'] = purchases
        st.session_state['rows'] = rows_actual
        st.session_state['cols'] = cols_actual
        st.session_state['aisles'] = aisles_actual
        st.session_state['results'] = {}
        occupied_count = len([s for s in seats_actual if s.occupied])
        st.success(f"Generated {len(seats_actual)} seats ({occupied_count} occupied, {free_count} free) and {len(purchases)} purchases")

if 'seats' not in st.session_state:
    st.info("👈 Configure the parameters and generate the layout to start.")
    st.stop()

seats = st.session_state['seats']
purchases = st.session_state['purchases']
num_rows_v = st.session_state['rows']
num_cols_v = st.session_state['cols']
aisle_cols = st.session_state['aisles']
results = st.session_state.get('results', {})

free_seats = get_free_seats(seats)
occupied_count = len([s for s in seats if s.occupied])
free_count = len(free_seats)

st.markdown("---")
st.header("1️⃣ Initial Configuration")

col_info, col_map = st.columns([1, 2])

with col_info:
    st.subheader("📋 Purchases")
    p_data = []
    for p in purchases:
        p_data.append({
            "ID": p.id,
            "Seats": p.num_seats,
            "Order": p.order,
            "Type": "Individual" if p.num_seats == 1 else
                    f"Couple" if p.num_seats == 2 else
                    f"Group ({p.num_seats})"
        })
    st.dataframe(pd.DataFrame(p_data), use_container_width=True, hide_index=True)

    st.markdown("#### Layout Summary")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total seats", len(seats))
    with m2:
        st.metric("Occupied", occupied_count)
    with m3:
        st.metric("Free", free_count)

    st.metric("Seats requested", sum(p.num_seats for p in purchases))

with col_map:
    st.subheader("🗺️ Venue Layout")
    fig_initial = plot_initial(seats, num_rows_v, num_cols_v, aisle_cols,
                               title="Initial Configuration (grey=occupied, pink=free)")
    st.pyplot(fig_initial)

st.markdown("---")
st.header("2️⃣ Optimization Algorithms")

algo_cols = st.columns(5)
algo_options = {
    "Greedy by\nOrder": "order",
    "Greedy by\nGroup Size": "group",
    "Greedy\nCompact": "compact",
    "ILP\n(PuLP)": "ilp",
    "Local\nSearch": "local"
}

for i, (name, key) in enumerate(algo_options.items()):
    with algo_cols[i]:
        if st.button(name.replace('\n', ' '), use_container_width=True, key=f"btn_{key}"):
            with st.spinner(f"Running {name.replace(chr(10), ' ')}..."):
                if key == "order":
                    result = greedy_by_order(seats, purchases)
                elif key == "group":
                    result = greedy_by_group_size(seats, purchases)
                elif key == "compact":
                    result = greedy_compact(seats, purchases)
                elif key == "ilp":
                    result = ilp_pulp(seats, purchases)
                elif key == "local":
                    base_key = "group"
                    if base_key not in results:
                        base_result = greedy_by_group_size(seats, purchases)
                        results[base_key] = base_result
                    result = local_search(seats, purchases,
                                          initial_result=results.get("group"))
                results[key] = result
                st.session_state['results'] = results

if results:
    st.markdown("---")
    st.header("3️⃣ Results")
    tab_names = [r.algorithm_name for r in results.values()]
    tabs = st.tabs(tab_names) if len(tab_names) > 1 else [st.container()]

    for i, (key, result) in enumerate(results.items()):
        with tabs[i] if len(tab_names) > 1 else tabs[0]:
            m = result.metrics
            if "error" in m:
                st.error(m["error"])
                continue

            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                st.metric("Avg Spread", m.get("avg_spread", "N/A"))
                st.metric("Total Spread", m.get("total_spread", "N/A"))
            with m_col2:
                st.metric("% Compact Groups", f"{m.get('pct_compact', 0)}%")
                st.metric("Compact Groups", f"{m.get('groups_compact', 0)}/{m.get('groups_total', 0)}")
            with m_col3:
                st.metric("Avg Intra-group Dist.", m.get("avg_pairwise_dist", "N/A"))
                st.metric("Seats Assigned", f"{m.get('seats_assigned', 0)}/{m.get('seats_free', 0)} free")
            with m_col4:
                st.metric("Time", f"{result.elapsed_time:.3f}s")
                if "solver_status" in m:
                    st.metric("ILP Status", m["solver_status"])
                if "note" in m:
                    st.info(m["note"])

            fig = plot_assignment(seats, purchases, result.assignments,
                                  num_rows_v, num_cols_v, aisle_cols,
                                  title=f"Assignment: {result.algorithm_name}")
            st.pyplot(fig)

            with st.expander("📊 Group Details"):
                if "group_details" in m:
                    detail_df = pd.DataFrame(m["group_details"])
                    detail_df = detail_df.rename(columns={
                        "purchase_id": "Purchase",
                        "num_seats": "Seats",
                        "order": "Order",
                        "spread": "Spread",
                        "avg_pairwise": "Avg Dist.",
                        "is_compact": "Compact"
                    })
                    detail_df["Compact"] = detail_df["Compact"].map({True: "✅", False: "❌"})
                    st.dataframe(detail_df, use_container_width=True, hide_index=True)

    if len(results) > 1:
        st.markdown("---")
        st.subheader("📈 Algorithm Comparison")

        comp_data = []
        for key, result in results.items():
            m = result.metrics
            if "error" not in m:
                comp_data.append({
                    "Algorithm": result.algorithm_name,
                    "Avg Spread": m.get("avg_spread", 0),
                    "Total Spread": m.get("total_spread", 0),
                    "% Compact": m.get("pct_compact", 0),
                    "Avg Intra-dist": m.get("avg_pairwise_dist", 0),
                    "Time (s)": round(result.elapsed_time, 3),
                    "Assigned": f"{m.get('seats_assigned', 0)}/{m.get('seats_free', 0)}"
                })

        if comp_data:
            st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

            fig_comp = plot_comparison(list(results.values()), seats, purchases)
            st.pyplot(fig_comp)

st.markdown("---")
with st.expander("ℹ️ Algorithm Descriptions"):
    st.markdown("""
    **1. Greedy by Order**: Processes purchases in order of arrival.
    For each purchase, finds the most compact block of available seats.
    Prioritizes early buyers.

    **2. Greedy by Group Size**: Sorts purchases from largest to smallest group.
    Large groups get the best contiguous blocks first, individuals last.

    **3. Greedy Compact**: Same order as #2 but exhaustively searches more
    seed positions for tighter group placement.

    **4. ILP (PuLP)**: Integer Linear Programming — globally minimizes total
    bounding-box spread using the CBC solver. Falls back to Greedy if the
    instance is too large or the ILP solution is worse.

    **5. Local Search**: Starts from the Greedy by Group Size solution and
    iteratively swaps seats between groups to reduce total spread.

    **Metrics:**
    - **Spread**: (max_row - min_row) + (max_col - min_col) per group.
    - **Compact**: Group with spread ≤ 1 (all seats adjacent).
    - **Intra-group dist.**: Mean Euclidean distance between seat pairs within a group.

    **Visual encoding:**
    - **Grey** (X): Pre-occupied seats (not available for optimization)
    - **Pink**: Free seats (available for assignment)
    - **Colours with ID**: Assigned groups after optimization
    """)