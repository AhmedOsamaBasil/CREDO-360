import unittest
import numpy as np
from feasibility_recovery.run import make_plan, simulate, summarize, SCENARIOS
from feasibility_recovery.core import partition, POLICIES


def synthetic_model():
    contexts = [(name, t) for name in ("ParkFountains01", "River01", "Train01") for t in range(6)]
    predicted = np.tile(np.linspace(1.8, 4.8, 6), (18, 1))
    model = {"split": partition(list(range(1, 29))), "contexts": contexts, "predicted": predicted,
             "sizes": np.tile(np.array([50, 100, 200, 400, 800, 1600])*1000, (18, 1)), "radius": .2}
    psnr = np.broadcast_to(18 + (predicted - 1) * 6, (19, 18, 6)).copy()
    return model, psnr, np.ones_like(psnr) * .95


class RunnerTests(unittest.TestCase):
    def test_first_action_uses_fixed_forecast_not_future_capacity(self):
        model, psnr, ssim = synthetic_model()
        plan = make_plan(0, model["split"]["test"])
        shifted = dict(plan, capacities_mbps=list(plan["capacities_mbps"]))
        shifted["capacities_mbps"][0] *= .1
        a = simulate(model, psnr, ssim, plan, "feasible_recovery", "capacity_only")
        b = simulate(model, psnr, ssim, shifted, "feasible_recovery", "capacity_only")
        self.assertEqual([r["action"] for r in a[:5]], [r["action"] for r in b[:5]])
        self.assertTrue(all(r["forecast_capacity_mbps"] == 3 for r in a[:5]))

    def test_future_test_outcomes_cannot_change_initial_action(self):
        model, psnr, ssim = synthetic_model()
        plan = make_plan(0, model["split"]["test"])
        a = simulate(model, psnr, ssim, plan, "feasible_recovery", "capacity_only")
        b = simulate(model, psnr + 3, ssim, plan, "feasible_recovery", "capacity_only")
        self.assertEqual([r["action"] for r in a[:5]], [r["action"] for r in b[:5]])
        self.assertNotEqual(a[0]["quality"], b[0]["quality"])

    def test_all_policies_scenarios_clock_and_reference_invariants(self):
        model, psnr, ssim = synthetic_model()
        plan = make_plan(0, model["split"]["test"])
        for policy in POLICIES:
            for scenario in SCENARIOS:
                with self.subTest(policy=policy, scenario=scenario):
                    rows = simulate(model, psnr, ssim, plan, policy, scenario)
                    self.assertEqual(len(rows), 450)
                    for row in rows:
                        self.assertAlmostEqual(row["buffer_before_s"] + 10 + row["stall_s"], row["round_duration_s"] + row["buffer_after_s"])
                        self.assertLessEqual(row["feasible_floor"], row["individual_ceiling"])
                    metrics = summarize(rows, 0)
                    self.assertTrue(all(np.isfinite(v) for v in metrics.values() if isinstance(v, (int, float))))
                    if scenario == "known_ceiling":
                        self.assertEqual(rows[30*5]["observed_cap"], 1)
                        self.assertEqual(rows[60*5]["observed_cap"], 5)
                    if scenario == "delayed_ceiling":
                        self.assertEqual(rows[30*5]["observed_cap"], 5)
                        self.assertEqual(rows[60*5]["observed_cap"], 1)

    def test_right_censor_not_fictitious_recovery(self):
        model, psnr, ssim = synthetic_model()
        rows = simulate(model, np.full_like(psnr, 24), ssim, make_plan(0, model["split"]["test"]), "fixed_debt", "known_ceiling")
        result = summarize(rows, 0)
        self.assertEqual(result["recovery_event_observed"], 0)
        self.assertEqual(result["recovery_wait_capped30"], 30)


if __name__ == "__main__":
    unittest.main()
