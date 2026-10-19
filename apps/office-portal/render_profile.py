"""Select an isolated renderer for documents using Word for Mac font fallback."""
import os

DEFAULT_DISCOVERY = 'http://collabora:9980/hosting/discovery'
WORD_MAC_DISCOVERY = 'http://collabora-wordmac:9980/word-mac/hosting/discovery'


def discovery_url(file_id, configured_ids=None):
    if configured_ids is None:
        configured_ids = os.environ.get('WORD_MAC_DOCUMENT_IDS', '')
    enabled = {value.strip() for value in configured_ids.split(',') if value.strip()}
    return WORD_MAC_DISCOVERY if file_id in enabled else DEFAULT_DISCOVERY
