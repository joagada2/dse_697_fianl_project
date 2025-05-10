import nest_asyncio
nest_asyncio.apply()

import os
import re
import hashlib
import urllib.parse
from collections import deque
import asyncio

import requests
import boto3
import botocore.exceptions
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import pdfplumber
import certifi

from prefect import flow  # Prefect 2.x

###############################################
# DynamoDB Helper Functions                   #
###############################################

def get_dynamodb_table(table_name: str):
    """
    Returns a DynamoDB table resource.
    Ensure that you have created a table (e.g., "ScrapedPages") with a primary key "url" (String)
    in the AWS Console.
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    return table

def store_result_dynamodb(table, url: str, scraped_text: str):
    """
    Stores or updates the scraped result in DynamoDB.
    """
    try:
        table.put_item(Item={"url": url, "scraped_text": scraped_text})
        print(f"Stored result for {url} in DynamoDB")
    except Exception as e:
        print(f"Error storing {url} in DynamoDB: {e}")

def fetch_all_results_dynamodb(table) -> list:
    """
    Fetches all items from the DynamoDB table.
    """
    try:
        response = table.scan()
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))
        return items
    except Exception as e:
        print(f"Error fetching items from DynamoDB: {e}")
        return []

###############################################
# Async Crawler Functions (Store in DynamoDB)  #
###############################################

def domain_allowed(url: str, allowed_domains: list) -> bool:
    if not allowed_domains:
        return True
    netloc = urllib.parse.urlparse(url).netloc.lower()
    for domain in allowed_domains:
        domain = domain.lower()
        if netloc == domain or netloc.endswith(f".{domain}"):
            return True
    return False

async def async_infinite_crawl_no_limit_collect(
    start_urls: list,
    allowed_domains: list,
    dynamodb_table
) -> None:
    """
    Asynchronously crawl starting from start_urls and store scraped text (for HTML pages or PDFs)
    in DynamoDB. Pages with non-text content (e.g. images, CSS, RSS) are skipped.
    """
    visited = set()
    to_visit = deque(start_urls)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        while to_visit:
            url = to_visit.popleft().strip()
            if url in visited:
                continue
            visited.add(url)

            try:
                content_type = get_content_type(url)
                if not content_type:
                    print(f"[SKIP] Cannot determine Content-Type for {url}")
                    continue
                ctype_lower = content_type.lower()

                # Skip non-text types (images, videos, CSS, RSS, etc.)
                if (ctype_lower.startswith("image/") or ctype_lower.startswith("video/") or
                    "text/css" in ctype_lower or "application/rss+xml" in ctype_lower):
                    print(f"[SKIP] {url} ({content_type})")
                    continue

                if "text/html" in ctype_lower:
                    print(f"[HTML PAGE] {url}")
                    text_data, links = await async_extract_text_from_html_no_hdr_ftr(url, page)
                    if text_data.strip():
                        store_result_dynamodb(dynamodb_table, url, text_data)
                        print(f"Scraped and stored {url}")
                    for link in links:
                        if link not in visited and domain_allowed(link, allowed_domains):
                            to_visit.append(link)

                elif "application/pdf" in ctype_lower:
                    print(f"[PDF FILE] {url}")
                    pdf_text = extract_text_from_pdf_no_hdr_ftr(url)
                    if pdf_text.strip():
                        store_result_dynamodb(dynamodb_table, url, pdf_text)
                        print(f"Scraped and stored {url}")
                else:
                    print(f"[SKIP] {url} ({content_type})")
                    continue

            except Exception as e:
                print(f"Error processing {url}: {e}")

        await browser.close()

# commment this and uncomment below to enable SSL in production
def get_content_type(url: str) -> str:
    """
    Attempts to get the Content-Type for the URL.
    For development, SSL verification is disabled (verify=False).
    First tries a HEAD request with a 20-second timeout.
    If that fails, falls back to a GET request with a Range header
    to download only a few bytes.
    Returns the Content-Type string, or None if both methods fail.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.head(url, allow_redirects=True, timeout=20, verify=False, headers=headers)
        if "Content-Type" in resp.headers:
            return resp.headers["Content-Type"]
    except Exception as e:
        print(f"HEAD request failed for {url}: {e}")
    
    try:
        headers["Range"] = "bytes=0-1023"  # Only download the first 1KB
        resp = requests.get(url, allow_redirects=True, timeout=20, verify=False, headers=headers)
        if "Content-Type" in resp.headers:
            return resp.headers["Content-Type"]
    except Exception as e:
        print(f"Fallback GET request failed for {url}: {e}")
    
    return None

# uncomment this and comment above to enable SSL
""""
def get_content_type(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.head(url, allow_redirects=True, timeout=20, verify=certifi.where(), headers=headers)
        if "Content-Type" in resp.headers:
            return resp.headers["Content-Type"]
    except Exception as e:
        print(f"HEAD request failed for {url}: {e}")
    try:
        headers["Range"] = "bytes=0-1023"  # Only download the first 1KB
        resp = requests.get(url, allow_redirects=True, timeout=20, verify=certifi.where(), headers=headers)
        if "Content-Type" in resp.headers:
            return resp.headers["Content-Type"]
    except Exception as e:
        print(f"Fallback GET request failed for {url}: {e}")
    return None
"""

async def async_extract_text_from_html_no_hdr_ftr(url: str, page) -> (str, list):
    await page.goto(url, wait_until="networkidle")
    html_content = await page.content()

    soup = BeautifulSoup(html_content, "html.parser")
    for tag in ["header", "footer", "nav", "script", "style", "img", "video", "svg", "noscript"]:
        for t in soup.find_all(tag):
            t.decompose()

    text_data = "\n".join([line.strip() for line in soup.get_text(separator="\n").splitlines() if line.strip()])
    hrefs = re.findall(r'href=[\"\']([^\"\']+)[\"\']', html_content)
    found_links = [urllib.parse.urljoin(url, link) for link in hrefs if urllib.parse.urljoin(url, link).startswith("http")]

    return text_data, found_links

def extract_text_from_pdf_no_hdr_ftr(url: str) -> str:
    temp_pdf = "temp.pdf"
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        with open(temp_pdf, "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"Failed to download PDF {url}: {e}")
        return ""
    all_pages_text = []
    try:
        with pdfplumber.open(temp_pdf) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    all_pages_text.append([ln.strip() for ln in page_text.splitlines() if ln.strip()])
    except Exception as e:
        print(f"Failed to parse PDF {url}: {e}")
        all_pages_text = []
    finally:
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)
    if not all_pages_text:
        return ""
    num_pages = len(all_pages_text)
    first_lines = [p[0] for p in all_pages_text if p]
    if len(first_lines) == num_pages and len(set(first_lines)) == 1:
        for p in all_pages_text:
            if p:
                p.pop(0)
    last_lines = [p[-1] for p in all_pages_text if p]
    if len(last_lines) == num_pages and len(set(last_lines)) == 1:
        for p in all_pages_text:
            if p:
                p.pop()
    final_text = "\n\n".join(["\n".join(p) for p in all_pages_text]).strip()
    return final_text

###############################################
# Synchronous Wrapper for .serve Deployment    #
###############################################

@flow(name="crawler_flow_sync")
def run_crawler_flow_sync():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Initialize the DynamoDB table (ensure that the "ScrapedPages" table exists with 'url' as primary key)
    dynamodb_table = get_dynamodb_table("ScrapedPages")
    loop.run_until_complete(async_infinite_crawl_no_limit_collect(
        start_urls=["https://utk.edu"],
        allowed_domains=["utk.edu"],
        dynamodb_table=dynamodb_table
    ))
    results = fetch_all_results_dynamodb(dynamodb_table)
    loop.close()
    print(f"Collected {len(results)} pages from DynamoDB. Ready for RAG workflow.")
    # At this point, your RAG workflow can query DynamoDB directly to load scraped text.

###############################################
# Deployment via .serve                        #
###############################################

if __name__ == "__main__":
    run_crawler_flow_sync.serve(name="crawler_flow_deployment", cron="* * * * *", limit=10)
    # Alternatively, to run once locally:
    # run_crawler_flow_sync()
