import unittest

from devrelay.crew import DEFAULT_MODEL, Delivery, build_crew, prepare_delivery, syntax_report
from devrelay.references import lookup_cards


class CoreTests(unittest.TestCase):
    def test_reference_lookup_is_limited_and_cited(self):
        matches = lookup_cards("slug unicode punctuation regex")
        self.assertTrue(matches)
        self.assertTrue(all(x["url"].startswith("https://docs.python.org/3/library/") for x in matches))
        self.assertLessEqual(len(matches), 3)

    def test_syntax_report_does_not_execute_code(self):
        report = syntax_report("raise RuntimeError('must not execute')\n")
        self.assertTrue(report["ok"])
        self.assertFalse(syntax_report("def broken(\n")["ok"])

    def test_crew_has_manager_and_three_specialists(self):
        crew = build_crew("Create a URL-safe slug function", "test-key-value", DEFAULT_MODEL, lambda event: None)
        self.assertEqual(crew.process.value, "hierarchical")
        self.assertEqual(crew.manager_agent.role, "Engineering Manager")
        self.assertEqual(len(crew.agents), 3)
        self.assertEqual(len(crew.tasks), 3)
        self.assertEqual([agent.role for agent in crew.agents],
                         ["Python Reference Researcher", "Python Utility Coder", "Code Reviewer"])

    def test_delivery_drops_unretrieved_citations_and_flags_unexecuted_tests(self):
        delivery = Delivery(
            summary="example", python_code="def f(): return 1", test_code="assert True",
            research_notes=[], source_urls=["https://docs.python.org/3/library/re.html",
                                             "https://example.com/unretrieved"],
            review_notes=[], verdict="review_ready",
        )
        result = prepare_delivery(delivery, {"https://docs.python.org/3/library/re.html"})
        self.assertEqual(result["source_urls"], ["https://docs.python.org/3/library/re.html"])
        self.assertFalse(result["code_executed"])
        self.assertIn("not executed", " ".join(result["review_notes"]))


if __name__ == "__main__":
    unittest.main()
