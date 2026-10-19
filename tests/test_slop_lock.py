import json, os, subprocess, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import slop_lock as sl


def rd(name):
    with open(os.path.join(ROOT, "examples", name), encoding="utf-8") as f:
        return f.read()


with open(os.path.join(HERE, "upstream_expected.json"), encoding="utf-8") as f:
    EXPECTED = json.load(f)


class SameAsUpstream(unittest.TestCase):
    """Expected output recorded by running phuryn/work-humanizer check.py and heise3/academic-deai content_lock.py."""

    def test_check_matches_work_humanizer(self):
        for name, lines in EXPECTED["check"].items():
            with self.subTest(name):
                self.assertEqual(sl.check(rd(name)), lines)

    def test_lock_matches_academic_deai(self):
        for name, exp in EXPECTED["lock"].items():
            with self.subTest(name):
                rep = sl.lock(rd("before.md"), rd(name))
                self.assertEqual(rep["status"], exp["status"])
                self.assertEqual(rep["categories"], exp["categories"])


class Check(unittest.TestCase):
    """Cases ported from work-humanizer tests/test_check.py (MIT)."""

    def flags(self, text):
        return "\n".join(sl.check(text))

    def test_dashes_and_semicolons(self):
        out = self.flags("The release — finally — shipped; users noticed.")
        self.assertIn("em/en dashes: 2", out)
        self.assertIn("semicolons: 1", out)

    def test_stock_vocabulary_and_marketing(self):
        out = self.flags("We delve into a vibrant tapestry that will seamlessly empower your team.")
        self.assertIn("delve", out)
        self.assertIn("marketing words", out)

    def test_pause_and_point(self):
        out = self.flags("Here's the thing: it's not just a tool, but a partner. The bottom line is speed. Thoughts?")
        self.assertIn("Here's the thing", out)
        self.assertIn("not just a tool, but", out)
        self.assertIn("Thoughts?", out)

    def test_uniform_short_rhythm(self):
        out = self.flags("It works. It ships. It scales. It sells. It wins. It lasts.")
        self.assertIn("uniform: merge short ones", out)
        self.assertIn("openers", out)

    def test_plain_text_is_quiet(self):
        text = "We cut no-shows from 18% to 7% in six months. Patients reschedule by replying. Sopot only got to 12%."
        self.assertEqual(self.flags(text), f"words: {len(text.split())}")


class Lock(unittest.TestCase):
    def test_identical_text_passes(self):
        self.assertEqual(sl.lock(rd("after.md"), rd("after.md"))["status"], "pass")

    def test_doi_url_and_code_are_locked(self):
        rep = sl.lock("See 10.1000/xyz123 and https://a.io/x. Run `make`.", "See https://a.io/x. Run `make test`.")
        self.assertEqual(rep["categories"]["identifiers"]["removed"], ["10.1000/xyz123"])
        self.assertEqual(rep["categories"]["protected_spans"]["added"], ["`make test`"])
        self.assertEqual(rep["status"], "fail")

    def test_strict_cli_exits_1_on_changed_number(self):
        p = subprocess.run([sys.executable, os.path.join(ROOT, "slop_lock.py"), "diff", "--strict",
                            os.path.join(ROOT, "examples", "before.md"), os.path.join(ROOT, "examples", "tampered.md")],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 1)
        self.assertIn("P=0.02", p.stdout)


if __name__ == "__main__":
    unittest.main()
