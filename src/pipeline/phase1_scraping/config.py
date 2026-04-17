"""
Configuration for Phase 1 Scraping Service.
"""

# Canonical Groww Mutual Fund URLs (as per Architecture Docs)
TARGET_URLS = [
    "https://groww.in/mutual-funds/sbi-magnum-multiplier-fund-direct-growth",
    "https://groww.in/mutual-funds/sbi-small-midcap-fund-direct-growth",
    "https://groww.in/mutual-funds/sbi-flexicap-fund-direct-growth",
    "https://groww.in/mutual-funds/sbi-large-cap-direct-plan-growth",
    "https://groww.in/mutual-funds/sbi-elss-tax-saver-fund-direct-growth"
]

# HTTP Client configurations
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

# Rate limiting
REQUEST_DELAY_SECONDS = 2.0

# Paths
OUTPUT_DIR = "output/raw_markdown"
