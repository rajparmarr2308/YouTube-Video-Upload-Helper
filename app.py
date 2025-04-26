import os
from flask import Flask, render_template, request, jsonify, Response
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
from flask_cors import CORS
import io

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
CORS(app)  # Enable CORS for all routes

# Increase max content length to 500MB
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
# Use the system's temp directory instead of a fixed uploads folder
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['DEFAULT_DESCRIPTION'] = """
👉 If you liked the video, Please Like, Share & Subscribe to my channel!
🔔 Don't forget to turn on notifications for more such content!

Tags:
"""

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log the temp directory we're using
logger.info(f"Using temporary directory for uploads: {app.config['UPLOAD_FOLDER']}")

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
    try:
        logger.info("Video upload request received")
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Request form keys: {list(request.form.keys())}")
        logger.info(f"Request files keys: {list(request.files.keys())}")
        
        if 'video' not in request.files:
            logger.warning("No video file in request")
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        logger.info(f"Received file: {file.filename}, size: {file.content_length if hasattr(file, 'content_length') else 'unknown'}")
        
        if file.filename == '':
            return jsonify({'error': 'No video selected'}), 400
        
        if file and allowed_file(file.filename):
            try:
                # Create a unique temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
                    temp_file_path = temp_file.name
                    # Read and write in chunks to handle large files
                    chunk_size = 4096  # 4KB chunks
                    while True:
                        chunk = file.read(chunk_size)
                        if not chunk:
                            break
                        temp_file.write(chunk)
                
                logger.info(f"Successfully saved uploaded file to: {temp_file_path}")
                logger.info(f"File size on disk: {os.path.getsize(temp_file_path)} bytes")
                
                # Extract content from video
                video_summary = extract_video_content(temp_file_path)
                
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
                
                # Clean up the temporary file
                try:
                    os.unlink(temp_file_path)
                    logger.info(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary file: {str(cleanup_error)}")
                
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
                return jsonify({'error': str(e), 'error_type': type(e).__name__}), 500
        
        return jsonify({'error': 'Invalid file format'}), 400
    except Exception as e:
        logger.exception("Unexpected error in process_video endpoint")
        return jsonify({'error': str(e), 'error_type': type(e).__name__, 'route': 'process_video'}), 500
        
@app.route('/chunk_upload', methods=['POST'])
def chunk_upload():
    """Alternative endpoint for handling chunked file uploads"""
    try:
        chunk = request.files.get('chunk')
        chunk_number = int(request.form.get('chunk_number', 0))
        total_chunks = int(request.form.get('total_chunks', 1))
        filename = request.form.get('filename', '')
        
        if not chunk or not filename:
            return jsonify({'error': 'Missing chunk or filename'}), 400
            
        temp_dir = os.path.join(tempfile.gettempdir(), 'video_chunks')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate a unique session ID based on filename if not provided
        session_id = request.form.get('session_id', secure_filename(filename))
        chunk_path = os.path.join(temp_dir, f"{session_id}_{chunk_number}")
        
        # Save this chunk
        chunk.save(chunk_path)
        
        # If this is the last chunk, combine all chunks
        if chunk_number == total_chunks - 1:
            final_path = os.path.join(tempfile.gettempdir(), secure_filename(filename))
            with open(final_path, 'wb') as outfile:
                # Combine all chunks
                for i in range(total_chunks):
                    chunk_file = os.path.join(temp_dir, f"{session_id}_{i}")
                    if os.path.exists(chunk_file):
                        with open(chunk_file, 'rb') as infile:
                            outfile.write(infile.read())
                        # Clean up chunk
                        os.unlink(chunk_file)
            
            # Now process the complete file (implement the processing logic here)
            # For now, just return success
            return jsonify({
                'success': True,
                'message': 'File uploaded successfully',
                'path': final_path
            })
        
        # Not the last chunk, just acknowledge receipt
        return jsonify({
            'success': True,
            'message': f'Chunk {chunk_number + 1}/{total_chunks} received'
        })
        
    except Exception as e:
        logger.exception("Error in chunk upload")
        return jsonify({'error': str(e)}), 500

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