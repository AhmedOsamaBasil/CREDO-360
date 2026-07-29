"""Dependency-light checks for the exported model and allocation constraints."""

from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from portable_qoe import PortableEnsemble, conformal_radius, select_action


class PortableModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        artifact = Path(__file__).resolve().parent / "artifacts" / "qoe_ensemble.json"
        cls.model = PortableEnsemble(artifact)

    def test_export_matches_pytorch_reference(self):
        self.assertLessEqual(self.model.verify_export(), 2e-5)

    def test_finite_conformal_radius(self):
        calibration = self.model.payload["calibration"]
        radius = conformal_radius(
            calibration["one_sided_residuals"], calibration["alpha"]
        )
        self.assertTrue(np.isfinite(radius))
        self.assertGreaterEqual(radius, 0)

    def test_selected_action_respects_shared_capacity(self):
        payload = self.model.payload
        ladder = np.asarray(payload["ladder_mbps"])
        users = 5
        capacity = 1.4
        action, _ = select_action(
            "risk_debt",
            self.model,
            np.asarray(payload["template_median"]),
            ladder,
            capacity,
            np.full(users, capacity / users),
            np.full(users, 4.0),
            np.full(users, ladder[1]),
            np.full(users, 0.02),
            np.arange(users, dtype=float),
            conformal_radius(
                payload["calibration"]["one_sided_residuals"],
                payload["calibration"]["alpha"],
            ),
        )
        self.assertLessEqual(float(action.sum()), capacity + 1e-9)
        self.assertTrue(np.all(np.isin(action, ladder)))


if __name__ == "__main__":
    unittest.main()
