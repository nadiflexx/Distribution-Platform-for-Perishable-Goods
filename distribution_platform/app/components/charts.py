"""
Chart components using Plotly for rich visualizations.
"""

import time
from typing import Any
import uuid

import plotly.graph_objects as go
import streamlit as st


class AlgorithmVisualizer:
    """Visualize algorithm execution step by step."""

    @staticmethod
    def render_graph_animation(trace: Any, container_key: str = "algo_viz"):
        """Render animated graph visualization of algorithm progression."""
        if not trace or not trace.snapshots:
            st.info("No algorithm trace available for this route.")
            return

        st.markdown(
            f"""
            <div class="algo-viz-header">
                <span class="algo-name">🧬 {trace.algorithm_name}</span>
                <span class="algo-stats">{trace.total_iterations} iterations • Final: {trace.final_cost:.1f} km</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Controls row
        col_slider, col_play, col_speed = st.columns([3, 1, 1])

        with col_slider:
            current_step = st.slider(
                "Algorithm Step",
                min_value=0,
                max_value=len(trace.snapshots) - 1,
                value=0,
                key=f"step_slider_{container_key}",
                label_visibility="collapsed",
            )

        with col_speed:
            speed = st.selectbox(
                "Speed",
                options=["🐢 Slow", "🚶 Normal", "🚀 Fast"],
                index=1,
                key=f"speed_{container_key}",
                label_visibility="collapsed",
            )

        with col_play:
            play_clicked = st.button(
                "▶️ Play",
                key=f"play_{container_key}",
                use_container_width=True,
            )

        # Current snapshot info
        snapshot = trace.snapshots[current_step]

        st.markdown(
            f"""
            <div class="step-info">
                <span class="step-num">Step {snapshot.iteration + 1}/{len(trace.snapshots)}</span>
                <span class="step-desc">{snapshot.description}</span>
                <span class="step-cost">Cost: {snapshot.current_best_cost:.1f} km</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Auto-play animation
        if play_clicked:
            AlgorithmVisualizer._run_animation(trace, container_key, speed)
        else:
            # Static render of current step
            AlgorithmVisualizer._render_graph(snapshot, container_key, current_step)

    @staticmethod
    def _run_animation(trace: Any, container_key: str, speed: str):
        """Run the auto-play animation."""
        speed_map = {"🐢 Slow": 1.0, "🚶 Normal": 0.5, "🚀 Fast": 0.2}
        delay = speed_map.get(speed, 0.5)

        # Create placeholders
        progress_bar = st.progress(0)
        info_placeholder = st.empty()
        graph_placeholder = st.empty()

        for i, snap in enumerate(trace.snapshots):
            # Update progress
            progress_bar.progress((i + 1) / len(trace.snapshots))

            # Update info
            with info_placeholder.container():
                st.markdown(
                    f"""
                    <div class="step-info animated">
                        <span class="step-num">Step {snap.iteration + 1}/{len(trace.snapshots)}</span>
                        <span class="step-desc">{snap.description}</span>
                        <span class="step-cost">Cost: {snap.current_best_cost:.1f} km</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Update graph
            with graph_placeholder.container():
                AlgorithmVisualizer._render_graph(snap, f"{container_key}_anim", i)

            time.sleep(delay)

        # Clear progress bar when done
        progress_bar.empty()

        # Show completion message
        st.success("✅ Animation complete! Use the slider to review any step.")

    @staticmethod
    def _render_graph(snapshot: Any, container_key: str, step_index: int):
        """Render a single graph state using Plotly."""
        if not snapshot.nodes:
            return

        fig = go.Figure()

        # Add edges first (so they're behind nodes)
        for _, edge in enumerate(snapshot.edges):
            from_node = snapshot.nodes[edge["from_id"]]
            to_node = snapshot.nodes[edge["to_id"]]

            fig.add_trace(
                go.Scatter(
                    x=[from_node["lon"], to_node["lon"]],
                    y=[from_node["lat"], to_node["lat"]],
                    mode="lines",
                    line={
                        "color": edge["color"],
                        "width": edge["weight"] * 2,
                    },
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        # Add nodes
        node_x = [n["lon"] for n in snapshot.nodes]
        node_y = [n["lat"] for n in snapshot.nodes]
        node_text = [n["name"] for n in snapshot.nodes]
        node_colors = [
            "#10b981" if n["type"] == "origin" else "#6366f1" for n in snapshot.nodes
        ]
        node_sizes = [20 if n["type"] == "origin" else 12 for n in snapshot.nodes]

        fig.add_trace(
            go.Scatter(
                x=node_x,
                y=node_y,
                mode="markers+text",
                marker={
                    "size": node_sizes,
                    "color": node_colors,
                    "line": {"width": 2, "color": "white"},
                },
                text=node_text,
                textposition="top center",
                textfont={"size": 9, "color": "#ffffff"},
                hoverinfo="text",
                hovertext=node_text,
                showlegend=False,
            )
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(14,14,17,1)",
            font_color="#a1a1aa",
            xaxis={
                "showgrid": True,
                "gridcolor": "rgba(255,255,255,0.03)",
                "zeroline": False,
                "showticklabels": False,
            },
            yaxis={
                "showgrid": True,
                "gridcolor": "rgba(255,255,255,0.03)",
                "zeroline": False,
                "showticklabels": False,
            },
            margin={"t": 10, "b": 10, "l": 10, "r": 10},
            height=350,
        )

        # Unique key combining container, step, and a random suffix for animation frames
        unique_key = f"graph_{container_key}_{step_index}_{uuid.uuid4().hex[:6]}"
        st.plotly_chart(fig, use_container_width=True, key=unique_key)
