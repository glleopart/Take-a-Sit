import streamlit as st
import pandas as pd
from models import Seat, Purchase
from layout import generate_layout, generate_purchases
from algorithms import (
    greedy_by_order, greedy_by_group_size, greedy_compact,
    ilp_pulp, local_search
)
from visualization import plot_assignment, plot_comparison

st.set_page_config(page_title="Take-a-Sit", page_icon="🪑", layout="wide")

st.title("🪑 Take-a-Sit")
st.subheader("Sistema de Optimización de Asignación de Asientos")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Configuración")

    st.subheader("Layout del Venue")
    total_seats = st.slider("Total de asientos", min_value=20, max_value=300, value=80, step=5)
    num_rows = st.slider("Número de filas", min_value=3, max_value=20, value=0, step=1,
                          help="0 = automático")
    num_cols = st.slider("Número de columnas", min_value=5, max_value=30, value=0, step=1,
                          help="0 = automático")
    num_aisles = st.slider("Número de pasillos", min_value=0, max_value=4, value=2)
    gap_prob = st.slider("Probabilidad de huecos", min_value=0.0, max_value=0.3, value=0.05, step=0.01)

    st.subheader("Compras / Grupos")
    num_purchases = st.slider("Número de compras", min_value=3, max_value=60, value=15)

    st.subheader("Semilla")
    seed = st.number_input("Semilla aleatoria", min_value=0, max_value=9999, value=42)

    st.markdown("---")
    if st.button("🎲 Generar Layout y Compras", use_container_width=True, type="primary"):
        layout_data = generate_layout(
            total_seats=total_seats,
            num_rows=num_rows if num_rows > 0 else None,
            num_cols=num_cols if num_cols > 0 else None,
            num_aisles=num_aisles,
            gap_probability=gap_prob,
            seed=seed
        )
        seats_actual, rows_actual, cols_actual, aisles_actual = layout_data

        purchases = generate_purchases(len(seats_actual), num_purchases=num_purchases, seed=seed + 100)

        st.session_state['seats'] = seats_actual
        st.session_state['purchases'] = purchases
        st.session_state['rows'] = rows_actual
        st.session_state['cols'] = cols_actual
        st.session_state['aisles'] = aisles_actual
        st.session_state['results'] = {}
        st.success(f"Generados {len(seats_actual)} asientos y {len(purchases)} compras")

if 'seats' not in st.session_state:
    st.info("👈 Configura los parámetros y genera el layout para comenzar.")
    st.stop()

seats = st.session_state['seats']
purchases = st.session_state['purchases']
num_rows_v = st.session_state['rows']
num_cols_v = st.session_state['cols']
aisle_cols = st.session_state['aisles']
results = st.session_state.get('results', {})

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 Compras")
    p_data = []
    seat_map = {s.id: s for s in seats}
    for p in purchases:
        p_data.append({
            "ID": p.id,
            "Asientos": p.num_seats,
            "Orden": p.order,
            "Tipo": "Individual" if p.num_seats == 1 else
                    f"Pareja" if p.num_seats == 2 else
                    f"Grupo ({p.num_seats})"
        })
    st.dataframe(pd.DataFrame(p_data), use_container_width=True, hide_index=True)

    st.metric("Asientos totales", len(seats))
    st.metric("Compras totales", len(purchases))
    st.metric("Asientos solicitados", sum(p.num_seats for p in purchases))

with col2:
    st.subheader("🗺️ Layout Vacío")
    fig_empty = plot_assignment(seats, purchases, {}, num_rows_v, num_cols_v, aisle_cols,
                                title="Layout del Venue (Sin asignar)")
    st.pyplot(fig_empty)

st.markdown("---")
st.header("🔧 Algoritmos de Asignación")

algo_cols = st.columns(5)
algo_options = {
    "Voraz por\nOrden": "order",
    "Voraz por\nGrupo": "group",
    "Voraz\nCompacto": "compact",
    "ILP\n(PuLP)": "ilp",
    "Búsqueda\nLocal": "local"
}

for i, (name, key) in enumerate(algo_options.items()):
    with algo_cols[i]:
        if st.button(name.replace('\n', ' '), use_container_width=True, key=f"btn_{key}"):
            with st.spinner(f"Ejecutando {name.replace(chr(10), ' ')}..."):
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
    st.header("📊 Resultados")
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
                st.metric("Dispersión Prom.", m.get("avg_spread", "N/A"))
                st.metric("Dispersión Total", m.get("total_spread", "N/A"))
            with m_col2:
                st.metric("% Grupos Compactos", f"{m.get('pct_compact', 0)}%")
                st.metric("Grupos Compactos", f"{m.get('groups_compact', 0)}/{m.get('groups_total', 0)}")
            with m_col3:
                st.metric("Dist. Intra-grupo Prom.", m.get("avg_pairwise_dist", "N/A"))
                st.metric("Asientos Asignados", f"{m.get('seats_assigned', 0)}/{m.get('seats_total', 0)}")
            with m_col4:
                st.metric("Tiempo", f"{result.elapsed_time:.3f}s")
                if "solver_status" in m:
                    st.metric("Estado ILP", m["solver_status"])

            fig = plot_assignment(seats, purchases, result.assignments,
                                  num_rows_v, num_cols_v, aisle_cols,
                                  title=f"Asignación: {result.algorithm_name}")
            st.pyplot(fig)

            with st.expander("📊 Detalle por grupo"):
                if "group_details" in m:
                    detail_df = pd.DataFrame(m["group_details"])
                    detail_df = detail_df.rename(columns={
                        "purchase_id": "Compra",
                        "num_seats": "Asientos",
                        "order": "Orden",
                        "spread": "Dispersión",
                        "avg_pairwise": "Dist. Prom.",
                        "is_compact": "Compacto"
                    })
                    detail_df["Compacto"] = detail_df["Compacto"].map({True: "✅", False: "❌"})
                    st.dataframe(detail_df, use_container_width=True, hide_index=True)

    if len(results) > 1:
        st.markdown("---")
        st.subheader("📈 Comparación de Algoritmos")

        comp_data = []
        for key, result in results.items():
            m = result.metrics
            if "error" not in m:
                comp_data.append({
                    "Algoritmo": result.algorithm_name,
                    "Dispersión Prom.": m.get("avg_spread", 0),
                    "Dispersión Total": m.get("total_spread", 0),
                    "% Compactos": m.get("pct_compact", 0),
                    "Dist. Intra-grupo": m.get("avg_pairwise_dist", 0),
                    "Tiempo (s)": round(result.elapsed_time, 3),
                    "Asignados": f"{m.get('seats_assigned', 0)}/{m.get('seats_total', 0)}"
                })

        if comp_data:
            st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

            fig_comp = plot_comparison(list(results.values()), seats, purchases)
            st.pyplot(fig_comp)

st.markdown("---")
with st.expander("ℹ️ Descripción de Algoritmos"):
    st.markdown("""
    **1. Voraz por Orden de Compra**: Procesa las compras en orden de llegada.
    Para cada compra, busca el bloque de asientos contiguos más compacto disponible.
    Prioriza a los primeros compradores.

    **2. Voraz por Tamaño de Grupo**: Ordena las compras de mayor a menor grupo.
    Los grupos grandes se asignan primero, obteniendo los mejores bloques contiguos.
    Individuales al final.

    **3. Voraz Compacto**: Igual que el algoritmo 2 pero con búsqueda exhaustiva
    de la mejor posición inicial (semilla) para cada grupo, evaluando más
    combinaciones para maximizar la compacidad.

    **4. ILP (PuLP)**: Optimización mediante Programación Lineal Entera.
    Minimiza la dispersión total (bounding box) de todos los grupos simultáneamente.
    Resuelve el problema global de forma óptima usando el solver CBC.
    Puede ser lento para instancias grandes (>15000 variables).

    **5. Búsqueda Local**: Parte de la solución del algoritmo 2 e intenta
    mejorarla intercambiando asientos entre grupos para reducir la dispersión.
    Heurística que puede mejorar soluciones greedy significativamente.

    **Métricas:**
    - **Dispersión**: (fila_max - fila_min) + (col_max - col_min) por grupo.
    - **Compacto**: Grupo con dispersión ≤ 1 (asientos adyacentes).
    - **Dist. Intra-grupo**: Promedio de distancia euclídea entre pares dentro del grupo.
    """)