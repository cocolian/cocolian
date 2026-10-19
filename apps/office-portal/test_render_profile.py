import unittest
from render_profile import discovery_url, DEFAULT_DISCOVERY, WORD_MAC_DISCOVERY

class RenderingProfileTest(unittest.TestCase):
    def test_explicit_document_routing(self):
        self.assertEqual(discovery_url('sample', ' sample,another '), WORD_MAC_DISCOVERY)
        self.assertEqual(discovery_url('samples', 'sample,another'), DEFAULT_DISCOVERY)
        self.assertEqual(discovery_url('sample', ''), DEFAULT_DISCOVERY)
        self.assertEqual(discovery_url('1', ', ,'), DEFAULT_DISCOVERY)

if __name__ == '__main__':
    unittest.main()
