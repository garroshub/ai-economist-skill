import matplotlib.pyplot as plt
import numpy as np
from modeling_core import PolicyOracle


def plot_taylor_sensitivity(
    country_name,
    current_pi,
    gap_scenarios,
    r_star_mid,
    r_star_range,
    actual_rate,
    output_filename="taylor_chart.png",
):
    """Taylor Rule chart with output gap scenarios."""
    oracle = PolicyOracle()

    # 1. X-axis: inflation range
    pi_min = current_pi - 0.4
    pi_max = current_pi + 0.4
    pi_range = np.linspace(pi_min, pi_max, 100)

    # 2. Figure setup
    plt.figure(figsize=(10, 6))
    plt.style.use("bmh")

    # 3. Non-linear Taylor model
    threshold_val = 2.5

    def get_rate_vectorized(r, gap):
        rates = []
        for pi in pi_range:
            val = oracle.models.taylor_nonlinear(
                r, pi, gap, threshold=threshold_val, stress_multiplier=1.5
            )
            rates.append(val)
        return np.array(rates)

    # Plot curves for each output gap scenario

    # Plot scenarios
    custom_colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]  # Blue, Orange, Green

    # Track plotted gaps to handle overlaps
    plotted_gaps = {}

    for i, (label, gap_val) in enumerate(gap_scenarios.items()):
        rates = get_rate_vectorized(r_star_mid, gap_val)
        col = custom_colors[i % len(custom_colors)]

        # Handle overlapping lines with different widths
        if gap_val in plotted_gaps:
            # Duplicate value - draw thinner
            lw = 2.5
            z_ord = 5  # Draw on top
        else:
            # First occurrence - draw thicker
            lw = 6.0
            z_ord = 4  # Draw behind
            plotted_gaps[gap_val] = True

        # Plot lines
        plt.plot(
            pi_range,
            rates,
            color=col,
            linewidth=lw,
            linestyle="-",
            alpha=1.0,
            label=label,
            zorder=z_ord,
        )

    # 5. Current rate anchor
    plt.axhline(
        y=actual_rate,
        color="black",
        linestyle="--",
        linewidth=1.5,
        label=f"Current policy rate: {actual_rate}%",
    )

    # Plot Point
    plt.scatter([current_pi], [actual_rate], color="black", s=80, zorder=10)

    # Ticks and limits
    plt.xticks(
        np.arange(np.floor(pi_min * 10) / 10, np.ceil(pi_max * 10) / 10 + 0.05, 0.1)
    )

    # Dynamic Y-axis
    all_rates = [actual_rate]
    for g in gap_scenarios.values():
        all_rates.extend(get_rate_vectorized(r_star_mid, g))
    y_min = min(all_rates) - 0.25
    y_max = max(all_rates) + 0.25
    plt.ylim(y_min, y_max)

    # Legend
    plt.legend(loc="upper left", frameon=False, title="Output Gap", fontsize=10)

    # Labels
    plt.title(f"{country_name}: Taylor Rule Scenarios", fontsize=12, fontweight="bold")
    plt.xlabel("Inflation, %", fontsize=11)
    plt.ylabel("Implied policy rate, %", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.6)

    # Save
    plt.savefig(output_filename, dpi=120, bbox_inches="tight")
    print(f"Chart generated: {output_filename}")
