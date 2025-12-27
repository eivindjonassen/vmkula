#!/usr/bin/env python3
"""Quick manual test for T017 scrape_and_store"""

import sys
sys.path.insert(0, '/Users/ejonassen/Documents/GitHub/vmkula/backend')

from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.fifa_ranking_scraper import FIFARankingScraper

def test_scrape_and_store_success():
    """Test complete scrape-and-store workflow."""
    
    # Mock firestore.Client BEFORE creating scraper
    with patch('src.firestore_manager.firestore.Client'):
        scraper = FIFARankingScraper()
        
        # Mock all the methods
        with patch.object(scraper.firestore_manager, 'get_fifa_rankings', return_value=None), \
             patch.object(scraper, 'fetch_rankings_page', return_value="<html>Rankings</html>"), \
             patch.object(scraper, 'parse_rankings', return_value=[{'rank': i} for i in range(1, 212)]), \
             patch.object(scraper.firestore_manager, 'update_fifa_rankings'), \
             patch.object(scraper.firestore_manager.db.collection('raw_api_responses').document('test'), 'set'):
            
            # Execute
            result = scraper.scrape_and_store()
            
            # Verify
            print("Result:", result)
            assert result['success'] is True
            assert result['teams_scraped'] == 211
            print("✅ Test passed!")

if __name__ == '__main__':
    test_scrape_and_store_success()
