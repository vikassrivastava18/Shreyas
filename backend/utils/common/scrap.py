#!/usr/bin/env python3
"""
    Web Scraper for Open textbooks
    This script extracts the complete book structure with chapters and subchapters
    and saves it to a JSON file.
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import re
from urllib.parse import urljoin


class BookScraper:
    def __init__(self, book_url, delay=2):
        """
        Initialize the book scraper
        
        Args:
            book_url (str): URL to the book's main page
            delay (int): Delay between requests in seconds
        """
        self.book_url = book_url
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def fetch_page(self, url):
        """Fetch a page and return BeautifulSoup object"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def extract_content(self, url):
        """
        Extract main content from a subchapter URL
        
        Args:
            url (str): URL of the subchapter
            
        Returns:
            str: Extracted content text
        """
        print(f"  Scraping content from: {url}")
        soup = self.fetch_page(url)
        
        if not soup:
            return "Error: Could not fetch content"
        
        # Try different content selectors
        content_selectors = [
            'main',
            '.entry-content',
            'article',
            '.post-content',
            '.chapter-content',
            '#content'
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.find('body')
        
        if not main_content:
            return "Error: Could not extract content"
        
        # Remove unwanted elements
        for element in main_content.find_all(['nav', 'header', 'footer', 'aside', 
                                               'script', 'style', '.navigation', 
                                               '.sidebar']):
            element.decompose()
        
        # Extract text
        content_text = main_content.get_text(separator=' ', strip=True)
        return self.clean_text(content_text)
    
    def scrape_book_structure(self):
        """
        Scrape the complete book structure with chapters and subchapters
        Note: All the chapters including Front Matter are in the same HTML list
        Returns:
            dict: Book data in the specified JSON structure
        """
        print(f"Fetching book structure from: {self.book_url}")
        soup = self.fetch_page(self.book_url)
        
        if not soup:
            return None
        
        # Extract book name
        book_name = "Unknown Book"
        title_elem = soup.find('h1', class_='reading-header__title')
        if title_elem:
            book_name = self.clean_text(title_elem.get_text())
        else:
            title_elem = soup.find('title')
            if title_elem:
                book_name = self.clean_text(title_elem.get_text())
        
        print(f"Book Name: {book_name}")
        
        # Find the main TOC
        toc = soup.find('ol', class_='toc')
        
        if not toc:
            print("Error: Could not find table of contents")
            return None
        
        book_data = {
            "bookName": book_name,
            "chapters": []
        }
        
        # Find all parts (chapters)
        parts = toc.find_all('li', class_='toc__part toc__part--full')
        
        print(f"Found {len(parts)} chapters")
        
        for part_index, part in enumerate(parts, 1):
            # Extract chapter name
            chapter_title_container = part.find('div', class_='toc__title__container')
            if not chapter_title_container:
                continue
            print("Title: \n", chapter_title_container)
            
            # Find the outer <a> tag
            anchor = chapter_title_container.find('a')

            if anchor:
                # Extract text after the nested span inside <a>
                try:
                    chapter_name = anchor.find('span', class_='toc__title__number').next_sibling.strip()
                except AttributeError:
                    chapter_name = anchor.get_text(strip=True)
            else:
                # If no <a> tag, extract from the span (Case 2)
                outer_span = chapter_title_container.find('span', class_='toc__title__number')
                chapter_name = outer_span.next_sibling.strip()

            print(f"\nChapter {part_index}: {chapter_name}")
            
            chapter_data = {
                "name": chapter_name,
                "subchapters": []
            }
            
            # Find subchapters within this chapter
            subchapters_ol = part.find('ol', class_='toc__chapters')
            
            if subchapters_ol:
                subchapter_items = subchapters_ol.find_all('li', class_='toc__chapter')
                print(f"Found {len(subchapter_items)} subchapters")
                
                for subchapter_index, subchapter in enumerate(subchapter_items, 1):
                    # Extract subchapter name and URL
                    subchapter_link = subchapter.find('a', href=True)
                    
                    if not subchapter_link:
                        continue
                    
                    subchapter_name = self.clean_text(subchapter_link.get_text())
                    subchapter_url = urljoin(self.book_url, subchapter_link['href'])
                    
                    print(f"  Subchapter {subchapter_index}: {subchapter_name}")
                    
                    # If (#) in the link, find the subchapter content without loading url
                    # if "#" in subchapter_url:

                    # Extract content from subchapter URL
                    content = self.extract_content(subchapter_url)
                    
                    subchapter_data = {
                        "name": subchapter_name,
                        "url": subchapter_url,
                        "content": content
                    }
                    
                    chapter_data["subchapters"].append(subchapter_data)
                    
                    # Be respectful with delays
                    if subchapter_index < len(subchapter_items):
                        time.sleep(self.delay)
            
            book_data["chapters"].append(chapter_data)
        
        # Also check for front-matter items (Introduction, Preface, etc.)
        front_matter_items = toc.find_all('li', class_='toc__front-matter')
        
        if front_matter_items:
            print(f"\nFound {len(front_matter_items)} front-matter items")
            
            front_matter_chapter = {
                "name": "Front Matter",
                "subchapters": []
            }
            
            for fm_index, fm_item in enumerate(front_matter_items, 1):
                fm_link = fm_item.find('a', href=True)
                
                if not fm_link:
                    continue
                
                fm_name = self.clean_text(fm_link.get_text())
                fm_url = urljoin(self.book_url, fm_link['href'])
                
                print(f"  Front Matter {fm_index}: {fm_name}")
                
                content = self.extract_content(fm_url)
                
                fm_data = {
                    "name": fm_name,
                    "url": fm_url,
                    "content": content
                }
                
                front_matter_chapter["subchapters"].append(fm_data)
                
                if fm_index < len(front_matter_items):
                    time.sleep(self.delay)
            
            # Insert front matter at the beginning
            if front_matter_chapter["subchapters"]:
                book_data["chapters"].insert(0, front_matter_chapter)
        
        return book_data
    
    def scrape_book_structure_alt(self):
        """
        Scrape the complete book structure with chapters and subchapters
        Note: Chapter Front Matter is in main list and remaining in another
        Returns:
            dict: Book data in the specified JSON structure
        """
        soup = self.fetch_page(self.book_url)
        
        if not soup:
            return None
        
        # Extract book name
        book_name = "Unknown Book"
        title_elem = soup.find('h1', class_='reading-header__title')
        if title_elem:
            book_name = self.clean_text(title_elem.get_text())
        else:
            title_elem = soup.find('title')
            if title_elem:
                book_name = self.clean_text(title_elem.get_text())
        
        print(f"Book Name: {book_name}")
        
        # Find the main TOC
        toc = soup.find('ol', class_='toc__chapters')
        
        if not toc:
            print("Error: Could not find table of contents")
            return None
        
        book_data = {
            "bookName": book_name,
            "chapters": []
        }
        
        # Find all parts (chapters)
        parts = toc.find_all('li', class_='toc__chapter numberless toc__chapter--full')
        
        print(f"Found {len(parts)} chapters")
        
        for part_index, part in enumerate(parts, 1):
            # Extract chapter name
            chapter_title_container = part.find('div', class_='toc__title__container')
            if not chapter_title_container:
                continue
            print("Title: \n", chapter_title_container)
            
            # Find the outer <a> tag
            anchor = chapter_title_container.find('a')

            if anchor:
                # Extract text after the nested span inside <a>
                try:
                    chapter_name = anchor.find('span', class_='toc__title__number').next_sibling.strip()
                except AttributeError:
                    chapter_name = anchor.get_text(strip=True)
            else:
                # If no <a> tag, extract from the span (Case 2)
                outer_span = chapter_title_container.find('span', class_='toc__title__number')
                chapter_name = outer_span.next_sibling.strip()

            print(f"\nChapter {part_index}: {chapter_name}")
            
            chapter_data = {
                "name": chapter_name,
                "subchapters": []
            }
            
            # Find subchapters within this chapter
            subchapters_ol = part.find('ol', class_='toc__subsections')
            
            if subchapters_ol:
                subchapter_items = subchapters_ol.find_all('li', class_='toc__subsection')
                print(f"Found {len(subchapter_items)} subchapters")
                
                for subchapter_index, subchapter in enumerate(subchapter_items, 1):
                    # Extract subchapter name and URL
                    subchapter_link = subchapter.find('a', href=True)
                    
                    if not subchapter_link:
                        continue
                    
                    subchapter_name = self.clean_text(subchapter_link.get_text())
                    subchapter_url = urljoin(self.book_url, subchapter_link['href'])
                    
                    print(f"  Subchapter {subchapter_index}: {subchapter_name}")
                    
                    # If (#) in the link, find the subchapter content without loading url
                    # if "#" in subchapter_url:

                    # Extract content from subchapter URL
                    content = self.extract_content(subchapter_url)
                    
                    subchapter_data = {
                        "name": subchapter_name,
                        "url": subchapter_url,
                        "content": content
                    }
                    
                    chapter_data["subchapters"].append(subchapter_data)
                    
                    # Be respectful with delays
                    if subchapter_index < len(subchapter_items):
                        time.sleep(self.delay)
            
            book_data["chapters"].append(chapter_data)
        
        # Also check for front-matter items (Introduction, Preface, etc.)
        front_matter_items = toc.find_all('li', class_='toc__front-matter')
        
        if front_matter_items:
            print(f"\nFound {len(front_matter_items)} front-matter items")
            
            front_matter_chapter = {
                "name": "Front Matter",
                "subchapters": []
            }
            
            for fm_index, fm_item in enumerate(front_matter_items, 1):
                fm_link = fm_item.find('a', href=True)
                
                if not fm_link:
                    continue
                
                fm_name = self.clean_text(fm_link.get_text())
                fm_url = urljoin(self.book_url, fm_link['href'])
                
                print(f"  Front Matter {fm_index}: {fm_name}")
                
                content = self.extract_content(fm_url)
                
                fm_data = {
                    "name": fm_name,
                    "url": fm_url,
                    "content": content
                }
                
                front_matter_chapter["subchapters"].append(fm_data)
                
                if fm_index < len(front_matter_items):
                    time.sleep(self.delay)
            
            # Insert front matter at the beginning
            if front_matter_chapter["subchapters"]:
                book_data["chapters"].insert(0, front_matter_chapter)
        
        return book_data
    

    def save_to_json(self, data, filename='output.json'):
        """Save the book data to a JSON file"""
        if not data:
            print("No data to save")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"Data successfully saved to {filename}")
        print(f"{'='*60}")
    
    def print_summary(self, data):
        """Print a summary of the scraped data"""
        if not data:
            return
        
        total_chapters = len(data['chapters'])
        total_subchapters = sum(len(ch['subchapters']) for ch in data['chapters'])
        total_words = 0
        
        for chapter in data['chapters']:
            for subchapter in chapter['subchapters']:
                if 'content' in subchapter:
                    total_words += len(subchapter['content'].split())
        
        print(f"\n{'='*60}")
        print("SCRAPING SUMMARY")
        print(f"{'='*60}")
        print(f"Book: {data['bookName']}")
        print(f"Total Chapters: {total_chapters}")
        print(f"Total Subchapters: {total_subchapters}")
        print(f"Total Words Extracted: {total_words:,}")
        print(f"Average Words per Subchapter: {total_words//total_subchapters if total_subchapters > 0 else 0:,}")
        print(f"{'='*60}")

def main():
    """Main function to run the book scraper"""
    # Book URL
    book_url = "https://wtcs.pressbooks.pub/oralinterpersonalcomm/front-matter/introduction/"
    
    # Create scraper instance with 2-second delay between requests
    scraper = BookScraper(book_url, delay=2)
    
    try:
        print("Starting book scraper...")
        print(f"{'='*60}\n")
        
        # Scrape the book structure
        book_data = scraper.scrape_book_structure()
        
        if book_data:
            # Save to JSON file
            scraper.save_to_json(book_data, 'books/books/json/foundatioralinterpersonalcommonsofece.json')            
            # Print summary
            scraper.print_summary(book_data)
        else:
            print("Failed to scrape book data")
    
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
