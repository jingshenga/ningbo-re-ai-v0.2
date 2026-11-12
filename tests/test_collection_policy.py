import unittest

from app.collectors.policy import may_fetch_online


class OnlinePolicyTests(unittest.TestCase):
    def test_online_gate_requires_both_switches_approved_status_and_reference(self):
        cases = [
            (False, True, 'approved', 'real-document-id', False),
            (True, False, 'approved', 'real-document-id', False),
            (True, True, 'not_reviewed', 'real-document-id', False),
            (True, True, 'approved', None, False),
            (True, True, 'approved', '    ', False),
            (True, True, 'approved', 'real-document-id', True),
        ]
        for global_on, source_on, status, reference, expected in cases:
            with self.subTest(global_on=global_on, source_on=source_on,
                              status=status, reference=reference):
                self.assertIs(
                    may_fetch_online(
                        global_enabled=global_on,
                        source_enabled=source_on,
                        policy_status=status,
                        policy_reference=reference,
                    ),
                    expected,
                )


if __name__ == '__main__':
    unittest.main()
