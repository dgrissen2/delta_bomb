"""Publication-format recovery must not admit later or conflicting information."""
import unittest

from provenance import assign_cohort, publication_timing


class TimingTests(unittest.TestCase):
    def test_original_format(self) -> None:
        text = '# January 15, 2025 at 7:00 AM EST\n**Date:** Wednesday, January 15, 2025 at 07:00 AM'
        self.assertTrue(publication_timing(text, '2025-01-15')['preopen'])

    def test_published_format_with_preopen_heading_revision(self) -> None:
        text = ('# Wednesday, January 15, 2025 at 3:02 am EST\n\n'
                '**Published:** Wednesday, January 15, 2025 at 02:49 AM\n'
                '**Scraped:** 2025-09-08 01:27:42\n\n---\n\n'
                "# Founder's Note: Wed, January 15, 2025 at 2:49 AM ET")
        r = publication_timing(text, '2025-01-15')
        self.assertTrue(r['preopen'])
        self.assertTrue(r['time_labels_differ'])
        self.assertIn('03:02:00-05:00', r['latest_labeled_time'])

    def test_after_open_revision_rejected(self) -> None:
        text = '# January 15, 2025 at 9:31 AM EST\n**Published:** Wednesday, January 15, 2025 at 07:00 AM'
        self.assertFalse(publication_timing(text, '2025-01-15')['preopen'])

    def test_at_open_rejected(self) -> None:
        self.assertFalse(publication_timing('# January 15, 2025 at 9:30 AM EST', '2025-01-15')['preopen'])

    def test_wrong_day_rejected(self) -> None:
        self.assertFalse(publication_timing('# January 16, 2025 at 7:00 AM EST', '2025-01-15')['preopen'])

    def test_metadata_conflicting_day_rejected(self) -> None:
        text = '# January 15, 2025 at 7:00 AM EST\n**Published:** Tuesday, January 14, 2025 at 07:00 AM'
        self.assertFalse(publication_timing(text, '2025-01-15')['preopen'])

    def test_wrong_dst_rejected(self) -> None:
        self.assertFalse(publication_timing('# July 15, 2025 at 7:00 AM EST', '2025-07-15')['preopen'])

    def test_no_explicit_eastern_header_rejected(self) -> None:
        self.assertFalse(publication_timing('**Published:** Wednesday, January 15, 2025 at 07:00 AM', '2025-01-15')['preopen'])

    def test_later_article_body_dates_do_not_define_publication(self) -> None:
        text = '# January 15, 2025 at 7:00 AM EST\n\n# Macro Theme:\nJanuary 16, 2025 at 4:00 PM ET'
        self.assertTrue(publication_timing(text, '2025-01-15')['preopen'])

    def test_malformed_metadata_rejected(self) -> None:
        text = '# January 15, 2025 at 7:00 AM EST\n**Published:** unavailable'
        self.assertFalse(publication_timing(text, '2025-01-15')['preopen'])


class CohortTests(unittest.TestCase):
    def test_old_days_and_development_are_not_new_evidence(self) -> None:
        a, b, d = {'2025-01-02'}, {'2025-01-03'}, {'2025-01-06'}
        self.assertEqual(assign_cohort('2025-01-02', a, b, d), 'original_50')
        self.assertEqual(assign_cohort('2025-01-03', a, b, d), 'additional_100')
        self.assertEqual(assign_cohort('2025-01-06', a, b, d), 'development_10')
        self.assertEqual(assign_cohort('2025-01-07', a, b, d), 'third_tranche')

    def test_overlapping_prior_sets_rejected(self) -> None:
        with self.assertRaises(ValueError):
            assign_cohort('2025-01-02', {'2025-01-02'}, {'2025-01-02'}, set())


if __name__ == '__main__':
    unittest.main()
