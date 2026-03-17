import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


def load_module():
    root = Path(__file__).resolve().parents[3]
    module_path = (
        root
        / "skills"
        / "plotting"
        / "plot-types"
        / "lightcurve-residuals"
        / "scripts"
        / "roman_plot.py"
    )
    spec = importlib.util.spec_from_file_location("roman_plot_module", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RomanPlotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module()

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.tmp_path = Path(self.tmpdir.name)
        self.csv_path = self.tmp_path / "test.csv"
        self._write_dataset(self.csv_path)

    def _write_dataset(self, path: Path):
        t = np.linspace(0.0, 100.0, 401)
        model = 18.2 - 0.6 * np.exp(-((t - 50.0) ** 2) / (2.0 * 7.5**2))
        data = model + 0.01 * np.sin(t / 3.0)
        err = np.full_like(t, 0.02)
        df = pd.DataFrame(
            {
                "time": t,
                "magnitude": data,
                "magnitude_err": err,
                "model_magnitude": model,
                "mag_band_h": data + 0.23,
                "mag_band_h_err": err * 1.1,
                "model_mag_h": model + 0.23,
            }
        )
        df.to_csv(path, index=False)

    def _base_argv(self):
        return [
            "--input",
            str(self.csv_path),
            "--output",
            str(self.tmp_path / "out"),
            "--x-col",
            "time",
            "--y-col",
            "magnitude",
            "--err-col",
            "magnitude_err",
            "--model-x-col",
            "time",
            "--model-col",
            "model_magnitude",
            "--y-kind",
            "magnitude",
            "--no-tex",
        ]

    def test_render_returns_figure_and_manifest(self):
        args = self.mod.parse_args(self._base_argv())
        fig, manifest = self.mod.render_lightcurve(args)
        self.assertGreaterEqual(len(fig.axes), 1)
        self.assertEqual(manifest["figure"]["policy_profile"], "strict")
        self.assertFalse(manifest["figure"]["postprocess_customized"])
        self.assertEqual(manifest["figure"]["y_kind"], "magnitude")
        fig.axes[0].grid(True)

    def test_auto_zoom_trim_baseline_sets_zoom_metadata(self):
        argv = self._base_argv() + ["--auto-x-zoom", "trim-baseline"]
        args = self.mod.parse_args(argv)
        _, manifest = self.mod.render_lightcurve(args)
        self.assertEqual(manifest["figure"]["x_zoom_source"], "auto-trim-baseline")
        zoom = manifest["figure"]["x_zoom_range"]
        self.assertIsNotNone(zoom)
        self.assertLess(zoom[0], 50.0)
        self.assertGreater(zoom[1], 50.0)

    def test_multiband_additive_normalization(self):
        argv = self._base_argv() + [
            "--band-label",
            "W146",
            "--band-spec",
            "H158,mag_band_h,mag_band_h_err,,model_mag_h,magnitude",
            "--normalize-mode",
            "additive",
            "--normalize-reference-band",
            "W146",
            "--normalize-source",
            "model",
        ]
        args = self.mod.parse_args(argv)
        _, manifest = self.mod.render_lightcurve(args)
        self.assertTrue(manifest["figure"]["multi_band"])
        h_norm = manifest["figure"]["normalization"]["H158"]
        self.assertAlmostEqual(h_norm["scale"], 1.0, places=8)
        self.assertAlmostEqual(h_norm["offset"], -0.23, places=3)

    def test_affine_normalization_rejected_for_magnitude(self):
        argv = self._base_argv() + [
            "--band-label",
            "W146",
            "--band-spec",
            "H158,mag_band_h,mag_band_h_err,,model_mag_h,magnitude",
            "--normalize-mode",
            "affine",
            "--normalize-reference-band",
            "W146",
        ]
        args = self.mod.parse_args(argv)
        with self.assertRaises(SystemExit) as ctx:
            self.mod.render_lightcurve(args)
        self.assertIn("invalid for y-kind='magnitude'", str(ctx.exception))

    def test_mixed_y_kind_rejected(self):
        argv = self._base_argv() + [
            "--band-label",
            "W146",
            "--band-spec",
            "H158,mag_band_h,mag_band_h_err,,model_mag_h,flux",
        ]
        args = self.mod.parse_args(argv)
        with self.assertRaises(SystemExit) as ctx:
            self.mod.render_lightcurve(args)
        self.assertIn("Mixed y-kind values", str(ctx.exception))

    def test_baseline_mode_column_requires_baseline_col(self):
        argv = self._base_argv() + [
            "--auto-x-zoom",
            "trim-baseline",
            "--baseline-mode",
            "column",
        ]
        args = self.mod.parse_args(argv)
        with self.assertRaises(SystemExit) as ctx:
            self.mod.render_lightcurve(args)
        self.assertIn("requires --baseline-col", str(ctx.exception))

    def test_auto_zoom_requires_model(self):
        argv = [
            "--input",
            str(self.csv_path),
            "--output",
            str(self.tmp_path / "out2"),
            "--x-col",
            "time",
            "--y-col",
            "magnitude",
            "--y-kind",
            "magnitude",
            "--auto-x-zoom",
            "trim-baseline",
            "--no-tex",
        ]
        args = self.mod.parse_args(argv)
        with self.assertRaises(SystemExit) as ctx:
            self.mod.render_lightcurve(args)
        self.assertIn("requires at least one model series", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
