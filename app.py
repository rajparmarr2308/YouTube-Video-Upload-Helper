import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import requests
from dotenv import load_dotenv
import json
import tempfile
import logging
import nltk
from services.video_processor import extract_video_content
from services.content_discovery import get_related_youtube_videos, search_related_blogs
from services.content_generator import generate_description, generate_tags

# Set NLTK data path to match the one in Dockerfile
nltk.data.path.append('/app/nltk_data')

# Load environment variables (optional now)
load_dotenv()

# Download NLTK data at startup to avoid runtime errors
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    # This should not be needed since we've pre-downloaded in Dockerfile
    # but keeping as fallback for local development
    nltk.download('punkt')
    nltk.download('stopwords')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload
app.config['DEFAULT_DESCRIPTION'] = """
👉 If you liked the video, Please Like, Share & Subscribe to my channel!
🔔 Don't forget to turn on notifications for more such content!

Tags:
"""

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# API keys are optional now
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
SERPAPI_KEY = os.getenv('SERPAPI_API_KEY')

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv'}

@app.route('/')
def index():
    return render_template('index.html', default_description=app.config['DEFAULT_DESCRIPTION'])

@app.route('/process_video', methods=['POST'])
def process_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({'error': 'No video selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Save the uploaded file to a temporary location
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract content from video
            video_summary = extract_video_content(filepath)
            
            # Get related content (API keys are optional now)
            youtube_videos = get_related_youtube_videos(video_summary, YOUTUBE_API_KEY)
            blog_posts = search_related_blogs(video_summary, SERPAPI_KEY)
            
            # Generate tags first
            tags = generate_tags(video_summary, youtube_videos, blog_posts)
            
            # Add short tags to default description
            enhanced_default_description = app.config['DEFAULT_DESCRIPTION']
            for tag in tags['short_tags']:
                enhanced_default_description += f"{tag}\n"
            
            # Generate description with the enhanced default description
            description_data = generate_description(
                video_summary, 
                youtube_videos, 
                blog_posts, 
                enhanced_default_description
            )
            
            # Clean up the uploaded file
            os.remove(filepath)
            
            return jsonify({
                'video_summary': video_summary,
                'youtube_videos': youtube_videos,
                'blog_posts': blog_posts,
                'description_data': description_data,
                'default_description': app.config['DEFAULT_DESCRIPTION'],
                'tags': tags
            })
        
        except Exception as e:
            logger.exception("Error processing video")
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file format'}), 400

@app.route('/update_default_description', methods=['POST'])
def update_default_description():
    data = request.json
    if 'default_description' in data:
        app.config['DEFAULT_DESCRIPTION'] = data['default_description']
        return jsonify({'success': True, 'default_description': app.config['DEFAULT_DESCRIPTION']})
    return jsonify({'error': 'No description provided'}), 400

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Choreo"""
    return jsonify({'status': 'healthy'}), 200

# For Choreo deployment
port = int(os.environ.get('PORT', 8080))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=False) 