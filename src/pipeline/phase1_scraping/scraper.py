import os
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import html2text
from tenacity import retry, wait_exponential, stop_after_attempt
import logging
from urllib.parse import urlparse

# Import phase 1 configuration
from pipeline.phase1_scraping.config import TARGET_URLS, HEADERS, REQUEST_DELAY_SECONDS, OUTPUT_DIR

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Pre-configure html2text to act optimally for RAG Data extraction
text_maker = html2text.HTML2Text()
text_maker.ignore_links = False
text_maker.ignore_images = True
text_maker.body_width = 0 # Don't wrap text, better for chunking
text_maker.protect_links = True
text_maker.mark_code = True

# Removed fetch_url in favor of Playwright page.goto

def clean_html(raw_html: str) -> str:
    """
    Cleans raw HTML by aggressively stripping out noisy elements 
    like navbars, footers, scripts, and styles.
    """
    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove script and style elements
    for element in soup(["script", "style", "noscript", "iframe", "svg", "nav", "footer", "header"]):
        element.decompose()

    # Sometimes headers/footers use classes/ids
    for element in soup.find_all(class_=["footer", "navbar", "nav", "menu", "sidebar", "ad"]):
        element.decompose()

    # Extract the body or main content if available
    main_content = soup.find("main") or soup.find("body") or soup
    
    return str(main_content)

def html_to_markdown(cleaned_html: str) -> str:
    """
    Converts cleaned HTML into structured Markdown, preserving tables.
    """
    return text_maker.handle(cleaned_html)

def extract_slug(url: str) -> str:
    """
    Extracts a filename-friendly slug from the URL.
    """
    path = urlparse(url).path
    return path.strip("/").split("/")[-1]

def run_scraper():
    """
    Main orchestration function for Phase 1 Scraping Service.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        # Configure context
        user_agent = HEADERS.get('User-Agent', "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        context = browser.new_context(user_agent=user_agent)
        page = context.new_page()
        
        success_count = 0
        failure_count = 0
        
        for url in TARGET_URLS:
            try:
                # 1. Fetch via Playwright
                logger.info(f"Fetching: {url}")
                page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Wait for fund category tags to potentially render (Groww uses 'pill' classes like pill12Pill)
                try:
                    page.wait_for_selector('div[class*="pill"], span[class*="pill"], div[class*="tag"], span[class*="tag"]', timeout=3000)
                except Exception:
                    pass # Timeout means no such tags found or page doesn't have them
                
                raw_html = page.content()
                
                # Extract Tags
                soup = BeautifulSoup(raw_html, "html.parser")
                tags = []
                for element in soup.find_all(lambda tag: tag.name in ['div', 'span', 'a'] and tag.has_attr('class') and any('pill' in c.lower() or 'tag' in c.lower() or 'chip' in c.lower() for c in tag['class'])):
                    text = element.get_text(strip=True)
                    if text and len(text) < 40 and text not in tags:
                        tags.append(text)
                
                # 2. Clean HTML
                cleaned_html = clean_html(raw_html)
                
                # 3. Convert to Markdown
                markdown_content = html_to_markdown(cleaned_html)
                
                # 4. Save to Disk (handoff to down-stream normalization phase)
                slug = extract_slug(url)
                file_path = os.path.join(OUTPUT_DIR, f"{slug}.md")
                
                with open(file_path, "w", encoding="utf-8") as f:
                    # Injecting YAML-style frontmatter for downstream use
                    f.write("---\n")
                    f.write(f"source_url: {url}\n")
                    f.write(f"fund_tags: {tags}\n")
                    f.write("---\n\n")
                    f.write(markdown_content)
                    
                logger.info(f"Successfully processed and saved to {file_path}")
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to process {url}: {str(e)}")
                failure_count += 1
            
            # Rate Limiting Logic
            time.sleep(REQUEST_DELAY_SECONDS)
            
        browser.close()
        return {"scraped_count": success_count, "failed_count": failure_count}

if __name__ == "__main__":
    logger.info("Starting Phase 1 Scraping Job...")
    run_scraper()
    logger.info("Phase 1 Scraping Job Completed.")
