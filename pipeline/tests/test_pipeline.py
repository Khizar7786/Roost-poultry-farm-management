import csv
import importlib.util
from pathlib import Path
import os
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np
import yaml

from behavior.classifier import Behavior, BehaviorClassifier
from behavior.logger import BehaviorLogger
from tracker.track_manager import TrackManager
from train.train import train
from utils.config import DEFAULT_CONFIG, PROJECT_ROOT, load_config, validate_dataset
from utils.trajectory import TrajectoryBuffer


class ConfigurationTests(unittest.TestCase):
    def test_committed_configuration_is_portable_and_cpu_first(self):
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                config = load_config()
            finally:
                os.chdir(previous)
        self.assertEqual(config["model"]["device"], "cpu")
        self.assertEqual(config["training"]["data_yaml"], str(PROJECT_ROOT / "dataset/data.yaml"))
        self.assertTrue(Path(config["training"]["data_yaml"]).is_file())
        self.assertTrue(Path(config["tracker"]["config"]).is_file())
        self.assertEqual(config["model"]["pretrained_base"], "yolov8s.pt")

    def test_cli_trainers_default_to_cpu(self):
        for filename in ("train.py", "trainRTDETR.py"):
            spec = importlib.util.spec_from_file_location("trainer_under_test", PROJECT_ROOT / filename)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            with patch("sys.argv", [filename]):
                args = module.parse_args()
            self.assertEqual(args.device, "cpu")
            self.assertEqual(args.data, str(PROJECT_ROOT / "dataset/data.yaml"))

    def test_device_check_handles_cpu_only_computer(self):
        import check
        with patch("check.torch.cuda.is_available", return_value=False), \
             patch("check.torch.cuda.get_device_name") as gpu_name, \
             patch("builtins.print"):
            check.main()
        gpu_name.assert_not_called()

    def test_invalid_config_reports_mapping_error(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.yaml"
            config.write_text("- item", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "mapping"):
                load_config(config)


class DatasetAndTrainingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "data.yaml"
        self.data.write_text("train: train/images\nval: valid/images\nnames: [chicken]\n", encoding="utf-8")

    def populate(self):
        for split in ("train", "valid"):
            images = self.root / split / "images"
            images.mkdir(parents=True)
            (images / "sample.jpg").write_bytes(b"test image placeholder")

    def test_missing_yaml_is_not_created(self):
        missing = self.root / "missing" / "data.yaml"
        with self.assertRaisesRegex(FileNotFoundError, "Dataset YAML not found"):
            validate_dataset(missing)
        self.assertFalse(missing.parent.exists())

    def test_empty_dataset_is_rejected(self):
        for split in ("train", "valid"):
            (self.root / split / "images").mkdir(parents=True)
        with self.assertRaisesRegex(FileNotFoundError, "No train images"):
            validate_dataset(self.data)

    def test_validation_split_is_required(self):
        (self.root / "train/images").mkdir(parents=True)
        (self.root / "train/images/chicken.jpg").write_bytes(b"sample")
        with self.assertRaisesRegex(FileNotFoundError, "No val images"):
            validate_dataset(self.data)

    def test_relative_dataset_paths_resolve_beside_yaml(self):
        self.populate()
        self.assertEqual(validate_dataset(self.data), str(self.data))

    def test_training_passes_cpu_and_configured_parameters(self):
        self.populate()
        config = load_config()
        config["training"].update(data_yaml=str(self.data), epochs=2, batch=1, name="custom")
        fake_model = Mock()
        # Real Ultralytics may increment the run directory; report its actual save_dir.
        fake_model.trainer.save_dir = self.root / "runs/custom2"
        with patch("ultralytics.YOLO", return_value=fake_model) as constructor:
            best = train(config)
        constructor.assert_called_once_with("yolov8s.pt")
        kwargs = fake_model.train.call_args.kwargs
        self.assertEqual(kwargs["device"], "cpu")
        self.assertEqual(kwargs["epochs"], 2)
        self.assertEqual(kwargs["batch"], 1)
        self.assertEqual(kwargs["workers"], 0)
        self.assertEqual(kwargs["name"], "custom")
        self.assertEqual(kwargs["data"], str(self.data))
        self.assertEqual(best, self.root / "runs/custom2/weights/best.pt")

    def test_missing_dataset_does_not_load_or_download_model(self):
        config = load_config()
        config["training"]["data_yaml"] = str(self.root / "absent.yaml")
        with patch("ultralytics.YOLO") as constructor:
            with self.assertRaises(FileNotFoundError):
                train(config)
        constructor.assert_not_called()


class TrackingTests(unittest.TestCase):
    def setUp(self):
        from ultralytics.engine.results import Boxes
        self.Boxes = Boxes
        self.frame = np.zeros((100, 100, 3), dtype=np.uint8)

    def detection(self, x=10):
        return SimpleNamespace(boxes=self.Boxes(np.array([[x, 10, x + 20, 30, 0.95, 0]], dtype=np.float32), (100, 100)))

    def test_real_bytetrack_preserves_id_and_normalizes_geometry(self):
        tracker = TrackManager()
        first = tracker.update(self.detection(), self.frame)
        second = tracker.update(self.detection(11), self.frame)
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 1)
        self.assertEqual(first[0]["id"], second[0]["id"])
        self.assertEqual(first[0]["cx"], 20.0)
        self.assertEqual(first[0]["w"], 20.0)
        self.assertEqual(first[0]["cls"], 0)

    def test_empty_frames_age_tracker(self):
        tracker = TrackManager()
        tracker.update(self.detection(), self.frame)
        self.assertEqual(tracker.update(SimpleNamespace(boxes=None), self.frame), [])
        self.assertEqual(tracker._tracker.frame_id, 2)

    def test_custom_threshold_configuration_is_used(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tracker.yaml"
            config = yaml.safe_load((PROJECT_ROOT / "tracker/bytetrack.yaml").read_text())
            config["track_high_thresh"] = 0.99
            path.write_text(yaml.safe_dump(config), encoding="utf-8")
            tracker = TrackManager(config_path=path)
            self.assertEqual(tracker.update(self.detection(), self.frame), [])

    def test_unknown_tracker_fails_explicitly(self):
        with self.assertRaisesRegex(ValueError, "Supported tracker"):
            TrackManager("misspelled")


class BehaviorTests(unittest.TestCase):
    def classify(self, count, *, step=0, classifier=None):
        classifier = classifier or BehaviorClassifier(fps=2, ill_window_sec=30, dead_window_sec=160, dead_velocity_px=0)
        history = TrajectoryBuffer(max_frames=1000)
        for frame in range(count):
            history.update(1, frame, frame * step, 0)
        return classifier.classify_all(history, [1], {1: ((count - 1) * step, 0)})[1]

    def test_thirty_frames_do_not_mean_thirty_seconds(self):
        self.assertEqual(self.classify(30), Behavior.NORMAL)

    def test_illness_waits_for_full_configured_window(self):
        self.assertEqual(self.classify(60), Behavior.NORMAL)
        self.assertEqual(self.classify(61), Behavior.POSSIBLY_ILL)

    def test_dead_waits_for_full_window_and_has_priority(self):
        self.assertEqual(self.classify(320), Behavior.POSSIBLY_ILL)
        self.assertEqual(self.classify(321), Behavior.POSSIBLY_DEAD)

    def test_moving_chicken_stays_normal(self):
        self.assertEqual(self.classify(400, step=10), Behavior.NORMAL)

    def test_huddling_excludes_self_but_includes_colocated_neighbor(self):
        classifier = BehaviorClassifier(fps=30)
        history = TrajectoryBuffer()
        labels = classifier.classify_all(history, [1, 2], {1: (10, 10), 2: (10, 10)})
        self.assertEqual(labels, {1: Behavior.HUDDLING, 2: Behavior.HUDDLING})

    def test_history_capacity_covers_longest_configured_window(self):
        config = load_config()["behavior"]
        classifier = BehaviorClassifier(fps=30, ill_window_sec=config["ill_window_sec"], dead_window_sec=config["dead_window_sec"])
        self.assertEqual(classifier.history_frames, 4801)


class TrajectoryAndLoggingTests(unittest.TestCase):
    def test_buffer_eviction_displacement_and_removal(self):
        history = TrajectoryBuffer(max_frames=3)
        for frame in range(5):
            history.update(7, frame, frame * 3, frame * 4)
        self.assertEqual([p[0] for p in history.get_positions(7)], [2, 3, 4])
        self.assertEqual(history.average_displacement(7, 3), 5.0)
        history.remove(7)
        self.assertEqual(history.all_ids(), [])
        self.assertEqual(history.average_displacement(7, 3), 0.0)

    def test_csv_interval_is_per_track_and_uses_video_timestamp(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested/behavior.csv"
            with BehaviorLogger(output, fps=10, log_interval_sec=1) as logger:
                for frame, track in ((0, 1), (1, 1), (1, 2), (10, 1)):
                    logger.log(frame, track, 1, 2, Behavior.NORMAL, 3)
            with output.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 3)
        self.assertEqual([row["track_id"] for row in rows], ["1", "2", "1"])
        self.assertEqual(rows[-1]["timestamp_sec"], "1.0")
        self.assertEqual(rows[-1]["behavior"], "normal")


if __name__ == "__main__":
    unittest.main()
