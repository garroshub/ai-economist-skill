import numpy as np


class TaylorRuleModels:
    def __init__(self, pi_target=2.0):
        self.pi_target = pi_target

    def taylor_1993(self, r_star, pi, output_gap):
        """Taylor 1993: i = r* + pi + 0.5(pi - pi*) + 0.5(gap)"""
        return r_star + pi + 0.5 * (pi - self.pi_target) + 0.5 * output_gap

    def taylor_1999(self, r_star, pi, output_gap):
        """Taylor 1999: higher gap weight. i = r* + pi + 0.5(pi - pi*) + 1.0(gap)"""
        return r_star + pi + 0.5 * (pi - self.pi_target) + 1.0 * output_gap

    def taylor_nonlinear(
        self, r_star, pi, output_gap, threshold=2.5, stress_multiplier=1.5
    ):
        """Non-linear Taylor: steeper reaction above inflation threshold."""
        base_pi_gap = pi - self.pi_target

        # Apply multiplier above threshold
        if pi > threshold:
            # Steeper reaction for high inflation
            adjusted_pi_gap = base_pi_gap * stress_multiplier
        else:
            adjusted_pi_gap = base_pi_gap

        # Base: Taylor 1999 weights
        return r_star + pi + 0.5 * adjusted_pi_gap + 1.0 * output_gap

    def post_08_adjusted(self, r_star, pi, output_gap, financial_stress=0.0):
        """Post-2008: subtracts financial stress premium."""
        base_rate = self.taylor_1999(r_star, pi, output_gap)
        # lambda = 0.25 typical stress coefficient
        return base_rate - 0.25 * financial_stress

    def apply_smoothing(self, current_rule_rate, previous_actual_rate, rho=0.8):
        """Interest rate smoothing: i_t = rho * i_{t-1} + (1 - rho) * i_rule"""
        return rho * previous_actual_rate + (1 - rho) * current_rule_rate


class PolicyOracle:
    def __init__(self):
        self.models = TaylorRuleModels()

    def generate_matrix(self, r_star_range, pi_range, gap_scenarios):
        """Generate 3D results matrix."""
        results = {}
        for r_star in r_star_range:
            results[r_star] = {}
            for gap in gap_scenarios:
                results[r_star][gap] = []
                for pi in pi_range:
                    rate = self.models.taylor_1999(r_star, pi, gap)
                    results[r_star][gap].append(rate)
        return results


if __name__ == "__main__":
    oracle = PolicyOracle()

    # Mock Data for Testing
    r_star_baseline = 2.75
    current_pi = 2.5
    actual_gap = -0.8
    prev_rate = 2.25

    print("--- Model Core Test (BoC Scenario) ---")
    t93 = oracle.models.taylor_1993(r_star_baseline, current_pi, actual_gap)
    t99 = oracle.models.taylor_1999(r_star_baseline, current_pi, actual_gap)
    smoothed = oracle.models.apply_smoothing(t99, prev_rate)

    print(f"Taylor 1993 Recommendation: {t93:.2f}%")
    print(f"Taylor 1999 Recommendation: {t99:.2f}%")
    print(f"Smoothed (rho=0.8) Recommendation: {smoothed:.2f}%")
    print(f"Basis Points Gap (Actual 2.25% vs T99): {(t99 - 2.25) * 100:.0f} bps")
