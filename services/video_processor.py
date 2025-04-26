import os
import tempfile
import logging
import speech_recognition as sr
from pydub import AudioSegment
from moviepy.editor import VideoFileClip
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize

logger = logging.getLogger(__name__)

def extract_video_content(video_path):
    """
    Extract content from video file using speech recognition
    
    Args:
        video_path: Path to the video file
        
    Returns:
        str: Summary of the video content
    """
    try:
        # Extract audio from video
        audio_path = extract_audio(video_path)
        
        # Transcribe audio
        transcript = transcribe_audio(audio_path)
        
        # Clean up temporary audio file
        os.remove(audio_path)
        
        # Summarize transcript with NLTK
        summary = summarize_with_nltk(transcript)
        
        return summary
    except Exception as e:
        logger.exception(f"Error processing video: {e}")
        raise

def extract_audio(video_path):
    """Extract audio from video file"""
    try:
        # Create temporary file for audio
        temp_audio = tempfile.mktemp(suffix=".wav")
        
        # Extract audio using moviepy
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(temp_audio, logger=None)
        
        return temp_audio
    except Exception as e:
        logger.exception(f"Error extracting audio: {e}")
        raise

def transcribe_audio(audio_path):
    """Transcribe audio file to text using Google's free speech recognition"""
    try:
        # Use Google's free speech recognition
        recognizer = sr.Recognizer()
        audio_file = sr.AudioFile(audio_path)
        
        # Process in chunks to handle longer files
        transcript = ""
        with audio_file as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source)
            
            # Calculate audio length
            audio_length = source.DURATION
            if audio_length is None:
                # If duration is not available, process the whole file
                audio_data = recognizer.record(source)
                transcript = recognizer.recognize_google(audio_data)
            else:
                # Process in 30-second chunks
                chunk_duration = 30  # seconds
                offset = 0
                
                while offset < audio_length:
                    chunk_data = recognizer.record(source, duration=min(chunk_duration, audio_length - offset))
                    try:
                        chunk_text = recognizer.recognize_google(chunk_data)
                        transcript += " " + chunk_text
                    except sr.UnknownValueError:
                        # Speech wasn't understandable
                        pass
                    except Exception as e:
                        logger.error(f"Error in transcription chunk: {e}")
                    
                    offset += chunk_duration
        
        return transcript
    except Exception as e:
        logger.exception(f"Error with speech recognition: {e}")
        return "Unable to transcribe audio. The video may not contain clear speech or may be too long."

def summarize_with_nltk(transcript):
    """Summarize transcript using NLTK extractive summarization"""
    try:
        # Download NLTK resources if not already downloaded
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        # Tokenize the transcript into sentences
        sentences = sent_tokenize(transcript)
        
        # Skip summarization if transcript is too short
        if len(sentences) <= 5:
            return transcript
        
        # Tokenize words and remove stopwords
        stop_words = set(stopwords.words('english'))
        words = word_tokenize(transcript.lower())
        filtered_words = [word for word in words if word.isalnum() and word not in stop_words]
        
        # Get word frequency
        word_freq = FreqDist(filtered_words)
        
        # Score sentences based on word frequency
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            sentence_words = word_tokenize(sentence.lower())
            score = sum([word_freq[word] for word in sentence_words if word in word_freq])
            # Normalize by sentence length
            sentence_scores[i] = score / max(1, len(sentence_words))
        
        # Select top 30% of sentences
        num_sentences = max(3, int(len(sentences) * 0.3))
        top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:num_sentences]
        
        # Sort sentences by original order
        top_sentences = sorted(top_sentences, key=lambda x: x[0])
        
        # Combine sentences to form summary
        summary = ' '.join([sentences[i] for i, _ in top_sentences])
        
        return summary
    except Exception as e:
        logger.exception(f"Error summarizing with NLTK: {e}")
        # Return a portion of the transcript if summarization fails
        return transcript[:500] + "..." if len(transcript) > 500 else transcript 