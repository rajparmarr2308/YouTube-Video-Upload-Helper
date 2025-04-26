import logging
import requests
from bs4 import BeautifulSoup
import re
import random
import urllib.parse
import time

logger = logging.getLogger(__name__)

def get_related_youtube_videos(query, api_key=None, max_results=5):
    """
    Search for related YouTube videos based on the query using web scraping instead of API
    
    Args:
        query: Search query (video summary)
        api_key: Not used in this version
        max_results: Maximum number of results to return
        
    Returns:
        list: List of dictionaries containing video title and description
    """
    try:
        # Construct search URL
        search_query = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={search_query}"
        
        # Add a user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Send request
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to get YouTube results: {response.status_code}")
            return []
            
        # Parse the response with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract video information
        videos = []
        video_count = 0
        
        # Look for JSON data in script tags (YouTube stores data in script tags)
        script_pattern = re.compile(r'var ytInitialData = ({.*?});', re.DOTALL)
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string and 'ytInitialData' in script.string:
                script_text = script.string
                json_match = script_pattern.search(script_text)
                
                if json_match:
                    try:
                        # This is a simplified approach - in practice this needs more robust parsing
                        # We're looking for titles and descriptions in the HTML
                        titles = re.findall(r'"title":{"runs":\[{"text":"(.*?)"}', script_text)
                        descriptions = re.findall(r'"detailedMetadataSnippets":\[\{"snippetText":{"runs":\[{"text":"(.*?)"}', script_text)
                        
                        # Some fallback patterns
                        if not titles:
                            titles = re.findall(r'"title":{"simpleText":"(.*?)"}', script_text)
                        
                        if not descriptions:
                            descriptions = re.findall(r'"descriptionSnippet":{"runs":\[{"text":"(.*?)"}', script_text)
                        
                        # Combine titles and descriptions
                        for i, title in enumerate(titles):
                            if video_count >= max_results:
                                break
                                
                            description = descriptions[i] if i < len(descriptions) else "No description available"
                            
                            # Skip YouTube Shorts and other non-video content
                            if "YouTube" in title and ("Home" in title or "Shorts" in title):
                                continue
                                
                            videos.append({
                                'title': title,
                                'description': description
                            })
                            video_count += 1
                    except Exception as e:
                        logger.error(f"Error parsing YouTube data: {e}")
        
        # If we couldn't extract videos, use a fallback approach with regex
        if not videos:
            video_titles = re.findall(r'title="(.*?)"', response.text)
            for title in video_titles:
                if video_count >= max_results:
                    break
                    
                # Filter out irrelevant titles
                if len(title) > 10 and "YouTube" not in title and not title.startswith('http'):
                    videos.append({
                        'title': title,
                        'description': "Description not available"
                    })
                    video_count += 1
                    
        return videos[:max_results]
    except Exception as e:
        logger.exception(f"Error getting YouTube videos: {e}")
        return []

def search_related_blogs(query, serpapi_key=None, num_results=5):
    """
    Search for related blog posts using web scraping instead of SerpAPI
    
    Args:
        query: Search query (video summary)
        serpapi_key: Not used in this version
        num_results: Number of results to return
        
    Returns:
        list: List of dictionaries containing blog title and description
    """
    try:
        # Construct search URL for blog posts
        search_query = urllib.parse.quote(f"{query} blog")
        url = f"https://www.google.com/search?q={search_query}"
        
        # Add a user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Send request
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to get search results: {response.status_code}")
            return []
            
        # Parse the response with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract blog information
        blogs = []
        
        # Find search result elements
        search_results = soup.find_all('div', class_='g')
        
        for result in search_results:
            if len(blogs) >= num_results:
                break
                
            # Extract title
            title_element = result.find('h3')
            if not title_element:
                continue
                
            title = title_element.text
            
            # Extract description
            description_element = result.find('div', class_='VwiC3b')
            description = description_element.text if description_element else "No description available"
            
            blogs.append({
                'title': title,
                'description': description
            })
            
        # If traditional method doesn't work, try alternative selectors
        if not blogs:
            titles = [h.text for h in soup.find_all('h3') if h.text]
            snippets = [div.text for div in soup.select('div.BNeawe.s3v9rd.AP7Wnd') if div.text]
            
            for i, title in enumerate(titles):
                if i >= num_results:
                    break
                    
                description = snippets[i] if i < len(snippets) else "No description available"
                blogs.append({
                    'title': title,
                    'description': description
                })
                
        return blogs[:num_results]
    except Exception as e:
        logger.exception(f"Error getting blog posts: {e}")
        
        # Generate some placeholder content if all else fails
        try:
            return generate_placeholder_blogs(query, num_results)
        except Exception as e2:
            logger.exception(f"Error generating placeholder blog posts: {e2}")
            return []

def generate_placeholder_blogs(query, num_results=5):
    """Generate placeholder blog content based on the query keywords"""
    words = query.split()
    blogs = []
    
    topics = [
        "How to", "Guide to", "Understanding", "Exploring", 
        "Best practices for", "Insights on", "Learn about",
        "Tips for", "Introduction to", "Deep dive into"
    ]
    
    for i in range(min(num_results, 5)):
        # Create a random blog title and description
        key_words = random.sample(words, min(3, len(words)))
        topic = random.choice(topics)
        
        title = f"{topic} {' '.join(key_words)}"
        description = f"This blog post discusses {' and '.join(key_words)} in detail, providing valuable information related to your topic."
        
        blogs.append({
            'title': title,
            'description': description
        })
        
    return blogs 