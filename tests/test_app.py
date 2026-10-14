"""Exercise user-facing state changes with Streamlit's application test runner."""

from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20)

    def test_demo_and_clean_example_show_correct_totals(self):
        self.app.run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual([m.value for m in self.app.metric], ["20", "5", "2", "3"])
        self.app.sidebar.radio[0].set_value("Clean example").run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual([m.value for m in self.app.metric], ["20", "5", "0", "0"])
        self.assertIn("scientific accuracy", self.app.success[0].value)

    def test_filters_search_without_changing_full_audit(self):
        self.app.run()
        self.app.selectbox[0].set_value("Data errors").run()
        self.assertEqual(len(self.app.dataframe[0].value), 2)
        self.app.text_input[0].set_value("INVALID").run()
        self.assertEqual(len(self.app.dataframe[0].value), 1)
        self.assertEqual([m.value for m in self.app.metric], ["20", "5", "2", "3"])

    def test_upload_empty_state_has_no_stale_audit(self):
        self.app.run()
        self.app.sidebar.radio[0].set_value("Upload a file").run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(len(self.app.metric), 0)
        self.assertIn("Choose a CSV or Excel file", self.app.info[0].value)


if __name__ == "__main__":
    unittest.main()
