import logging
import re
from collections import Counter
import random
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist

logger = logging.getLogger(__name__)

def generate_description(video_summary, youtube_videos, blog_posts, default_description):
    """
    Generate a detailed description for the YouTube video using NLP techniques
    
    Args:
        video_summary: Summary of the video content
        youtube_videos: List of related YouTube videos
        blog_posts: List of related blog posts
        default_description: Default description to append
        
    Returns:
        dict: Contains main description, short description options, and validation info
    """
    try:
        # Ensure NLTK resources are downloaded
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
            
        # Get important keywords
        stop_words = set(stopwords.words('english'))
        all_words = word_tokenize(video_summary.lower())
        filtered_words = [word for word in all_words if word.isalnum() and word not in stop_words]
        word_freq = FreqDist(filtered_words)
        top_keywords = [word for word, _ in word_freq.most_common(20)]
        
        # Create a simpler intro using top keywords
        intro_templates = [
            "Discover how to {keyword1} and {keyword2} in this guide.",
            "Learn about {keyword1} and {keyword2} in this video.",
            "Everything you need to know about {keyword1} and {keyword2}.",
            "A complete guide to {keyword1} and {keyword2}.",
        ]
        
        # Select template and fill with keywords
        intro_template = random.choice(intro_templates)
        keyword_dict = {f"keyword{i+1}": keyword for i, keyword in enumerate(random.sample(top_keywords, min(2, len(top_keywords))))}
        intro = intro_template.format(**keyword_dict)
        
        # Create a concise description using the summary
        summary_sentences = sent_tokenize(video_summary)
        short_description = intro + " " + " ".join(summary_sentences[:min(3, len(summary_sentences))])
        
        # Ensure it's not too long (4-5 lines, about 300-400 chars)
        if len(short_description) > 400:
            short_description = short_description[:397] + "..."
            
        # Validate the description
        validation_issues = validate_description(short_description)
        
        # Generate alternative short description options
        short_description_options = [short_description]
        
        # Option 2: Based on YouTube videos
        if youtube_videos:
            youtube_option = generate_option_from_youtube(youtube_videos, top_keywords)
            if youtube_option:
                short_description_options.append(youtube_option)
                
        # Option 3: Based on blog posts
        if blog_posts:
            blog_option = generate_option_from_blogs(blog_posts, top_keywords)
            if blog_option:
                short_description_options.append(blog_option)
                
        # Option 4: Statistical approach using most frequent terms
        stat_option = generate_statistical_option(video_summary, top_keywords)
        if stat_option:
            short_description_options.append(stat_option)
            
        # Ensure we have at least 3 options
        while len(short_description_options) < 3:
            extra_option = generate_extra_option(video_summary, top_keywords)
            if extra_option and extra_option not in short_description_options:
                short_description_options.append(extra_option)
                
        # Combine everything into the full description with default_description
        full_description = f"{short_description}\n\n{default_description}"
        
        return {
            'full_description': full_description,
            'short_description': short_description,
            'short_description_options': short_description_options[:4],  # Limit to 4 options
            'validation_issues': validation_issues
        }
    except Exception as e:
        logger.exception(f"Error generating description: {e}")
        # Fallback to a simple description using the video summary
        return {
            'full_description': f"{video_summary}\n\n{default_description}",
            'short_description': video_summary[:300] + "..." if len(video_summary) > 300 else video_summary,
            'short_description_options': [video_summary[:300] + "..." if len(video_summary) > 300 else video_summary],
            'validation_issues': []
        }

def validate_description(description):
    """Validate description for common issues"""
    issues = []
    
    # Check for common issues
    if len(description) < 100:
        issues.append("Description is too short")
        
    if len(description) > 500:
        issues.append("Description is too long")
        
    # Check for excessive capitalization (SHOUTING)
    caps_ratio = sum(1 for c in description if c.isupper()) / max(1, len([c for c in description if c.isalpha()]))
    if caps_ratio > 0.3:
        issues.append("Too many capital letters")
        
    # Check for excessive punctuation
    punct_ratio = sum(1 for c in description if c in '!?.') / max(1, len(description))
    if punct_ratio > 0.1:
        issues.append("Too much punctuation")
        
    # Check for URLs or emails that might be unwanted
    if re.search(r'https?://|www\.|@[a-zA-Z0-9]+\.[a-zA-Z]', description):
        issues.append("Contains URLs or email addresses")
        
    # Check for common spam phrases
    spam_phrases = ['buy now', 'click here', 'subscribe now', 'free gift', 'limited time', 'act now']
    if any(phrase in description.lower() for phrase in spam_phrases):
        issues.append("Contains promotional language")
        
    return issues

def generate_option_from_youtube(youtube_videos, keywords):
    """Generate a description option based on YouTube video titles and descriptions"""
    try:
        if not youtube_videos:
            return None
            
        # Get title and description from the most relevant video
        video = youtube_videos[0]
        title = video.get('title', '')
        
        # Create a template
        templates = [
            "Similar to popular videos on this topic, this video covers {keywords}. {title}",
            "Following the trend of top YouTube content, this video explains {keywords}. {title}",
            "Based on what's popular on YouTube, this video demonstrates {keywords}. {title}"
        ]
        
        template = random.choice(templates)
        keyword_str = " and ".join(random.sample(keywords, min(2, len(keywords))))
        
        description = template.format(keywords=keyword_str, title=title)
        
        # Ensure it's not too long
        if len(description) > 400:
            description = description[:397] + "..."
            
        return description
    except Exception as e:
        logger.exception(f"Error generating YouTube option: {e}")
        return None

def generate_option_from_blogs(blog_posts, keywords):
    """Generate a description option based on blog post titles"""
    try:
        if not blog_posts:
            return None
            
        # Get titles from top 2 blogs
        blog_titles = [blog.get('title', '') for blog in blog_posts[:2] if blog.get('title')]
        
        if not blog_titles:
            return None
            
        # Create a template
        templates = [
            "As discussed in popular blogs like '{blog}', this video explores {keywords}.",
            "This video covers {keywords}, a topic that's trending in blogs like '{blog}'.",
            "Inspired by blog posts such as '{blog}', this video delves into {keywords}."
        ]
        
        template = random.choice(templates)
        keyword_str = " and ".join(random.sample(keywords, min(2, len(keywords))))
        blog = random.choice(blog_titles)
        
        description = template.format(keywords=keyword_str, blog=blog)
        
        # Ensure it's not too long
        if len(description) > 400:
            description = description[:397] + "..."
            
        return description
    except Exception as e:
        logger.exception(f"Error generating blog option: {e}")
        return None

def generate_statistical_option(summary, keywords):
    """Generate a description option using statistical NLP approach"""
    try:
        if not summary or not keywords:
            return None
            
        # Extract key sentences containing most keywords
        sentences = sent_tokenize(summary)
        if not sentences:
            return None
            
        # Score sentences by keyword presence
        scored_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            score = sum(1 for kw in keywords if kw in sentence_lower)
            scored_sentences.append((sentence, score))
            
        # Get top 2 sentences
        top_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)[:2]
        
        if not top_sentences:
            return None
            
        # Combine into a description
        description = " ".join([s[0] for s in top_sentences])
        
        # Add an intro
        intros = [
            "This video focuses on ",
            "This content covers ",
            "Learn about ",
            "Discover "
        ]
        
        intro = random.choice(intros)
        keyword_str = " and ".join(random.sample(keywords[:5], min(2, len(keywords[:5]))))
        
        description = intro + keyword_str + ". " + description
        
        # Ensure it's not too long
        if len(description) > 400:
            description = description[:397] + "..."
            
        return description
    except Exception as e:
        logger.exception(f"Error generating statistical option: {e}")
        return None

def generate_extra_option(summary, keywords):
    """Generate an additional description option as fallback"""
    try:
        if not summary or not keywords:
            return None
            
        templates = [
            "This video provides a comprehensive guide to {keywords}. {summary}",
            "Looking to learn about {keywords}? This video has you covered. {summary}",
            "A complete walkthrough of {keywords}. {summary}",
            "Master {keywords} with this informative video. {summary}"
        ]
        
        template = random.choice(templates)
        keyword_str = " and ".join(random.sample(keywords[:10], min(2, len(keywords[:10]))))
        
        # Use just the first sentence of the summary
        first_sentence = sent_tokenize(summary)[0] if sent_tokenize(summary) else summary[:100]
        
        description = template.format(keywords=keyword_str, summary=first_sentence)
        
        # Ensure it's not too long
        if len(description) > 400:
            description = description[:397] + "..."
            
        return description
    except Exception as e:
        logger.exception(f"Error generating extra option: {e}")
        return None

def generate_tags(video_summary, youtube_videos, blog_posts):
    """
    Generate relevant tags for the YouTube video using NLP instead of OpenAI
    
    Args:
        video_summary: Summary of the video content
        youtube_videos: List of related YouTube videos
        blog_posts: List of related blog posts
        
    Returns:
        dict: Dictionary containing short_tags and hashtag_tags
    """
    try:
        # Ensure NLTK resources are downloaded
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
            
        # Collect all text for keyword extraction
        all_text = video_summary
        
        # Add titles from YouTube videos
        for video in youtube_videos:
            all_text += " " + video.get('title', '')
            
        # Add titles from blog posts
        for blog in blog_posts:
            all_text += " " + blog.get('title', '')
            
        # Extract n-grams (1, 2, and 3 words) to find common phrases
        stop_words = set(stopwords.words('english'))
        words = [word.lower() for word in word_tokenize(all_text) 
                if word.isalnum() and word.lower() not in stop_words and len(word) > 2]
        
        # Get word frequency
        unigrams = FreqDist(words)
        
        # Get bigrams (2-word phrases)
        bigrams = []
        for i in range(len(words) - 1):
            bigrams.append(words[i] + " " + words[i+1])
        bigram_freq = FreqDist(bigrams)
        
        # Get trigrams (3-word phrases)
        trigrams = []
        for i in range(len(words) - 2):
            trigrams.append(words[i] + " " + words[i+1] + " " + words[i+2])
        trigram_freq = FreqDist(trigrams)
        
        # Select top phrases for tags
        top_unigrams = [word for word, _ in unigrams.most_common(10)]
        top_bigrams = [phrase for phrase, _ in bigram_freq.most_common(5)]
        top_trigrams = [phrase for phrase, _ in trigram_freq.most_common(3)]
        
        # Combine for short tags, ensuring no duplicates
        short_tags = []
        for tag in top_trigrams + top_bigrams + top_unigrams:
            # Check for duplicates
            is_duplicate = False
            for existing_tag in short_tags:
                if tag in existing_tag or existing_tag in tag:
                    is_duplicate = True
                    break
                    
            if not is_duplicate and len(short_tags) < 10:
                # Capitalize first letter of each word
                short_tags.append(' '.join(word.capitalize() for word in tag.split()))
                
        # Fill any remaining slots with single words if needed
        while len(short_tags) < 10 and len(top_unigrams) > 0:
            word = top_unigrams.pop(0).capitalize()
            if word not in short_tags:
                short_tags.append(word)
                
        # Generate hashtag tags (combination of words without spaces, with # prefix)
        hashtag_tags = []
        for tag in short_tags[:5]:  # Use top 5 from short tags
            # Remove spaces and add # prefix
            hashtag = "#" + ''.join(word.capitalize() for word in tag.split())
            hashtag_tags.append(hashtag)
            
        # Add some common YouTube tags
        common_youtube_tags = ["#Tutorial", "#HowTo", "#Tips", "#Guide", "#Explained"]
        hashtag_tags.extend(random.sample(common_youtube_tags, min(3, len(common_youtube_tags))))
        
        return {
            'short_tags': short_tags,
            'hashtag_tags': ', '.join(hashtag_tags)
        }
    except Exception as e:
        logger.exception(f"Error generating tags: {e}")
        # Fallback to extracting keywords from the summary
        words = re.findall(r'\b\w+\b', video_summary.lower())
        common_words = [word for word in words if len(word) > 3 and word not in ['with', 'that', 'this', 'from', 'have', 'what', 'were', 'when', 'your', 'which', 'their']]
        
        word_counts = Counter(common_words)
        top_words = [word.capitalize() for word, _ in word_counts.most_common(10)]
        
        return {
            'short_tags': top_words,
            'hashtag_tags': ', '.join(['#' + word for word in top_words[:5]])
        } 