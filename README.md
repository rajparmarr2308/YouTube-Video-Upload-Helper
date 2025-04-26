# YouTube Video Upload Helper

A web-based tool to assist in uploading YouTube videos by automating the generation of descriptions, tags, and more. No paid APIs required!

## Features

- Video upload and content extraction using free speech recognition
- Related content discovery through web scraping
- Multiple auto-generated description options with validation
- Short tags integrated into default description section for easy editing
- Customizable default description templates

## Local Setup

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Optional: Set up API keys for improved results (not required):
- Create a `.env` file in the project root using the `.env.example` template
- The application will work without any API keys

3. Run the application:
```
python app.py
```

4. Open your browser and go to `http://localhost:8080`

## Deployment to Choreo

[Choreo](https://console.choreo.dev/) is a cloud platform for deploying containerized applications. Follow these steps to deploy:

### Prerequisites

- A [Choreo](https://console.choreo.dev/) account
- [Git](https://git-scm.com/) installed locally
- [Docker](https://www.docker.com/) installed locally (for testing)

### Deployment Steps

1. **Clone your repository** (if you haven't already):
```
git clone <your-repo-url>
cd <your-repo-directory>
```

2. **Test Docker build locally** (optional):
```
docker build -t youtube-helper .
docker run -p 8080:8080 youtube-helper
```
Visit `http://localhost:8080` to test if it's working correctly.

3. **Login to Choreo Console**:
- Go to [Choreo Console](https://console.choreo.dev/)
- Login with your credentials

4. **Create a New Component**:
- Click on "Create a New Component"
- Select "Service" for component type
- Choose "Container" for implementation type

5. **Connect Your Repository**:
- Connect to your Git provider (GitHub, GitLab, etc.)
- Select the repository containing this code

6. **Configure Deployment**:
- Choreo will automatically detect the Dockerfile
- Ensure the container port is set to 8080
- Set the build context to the root directory

7. **Deploy the Component**:
- Click "Deploy" to start the deployment process
- Wait for the build and deployment to complete

8. **Access Your Application**:
- Once deployment is complete, click on the provided URL to access your application

### Environment Variables

For better performance, you can set these optional variables in Choreo:
- `YOUTUBE_API_KEY`: Your YouTube Data API key
- `SERPAPI_API_KEY`: Your SerpAPI key

## How It Works (No APIs)

- **Speech Recognition**: Uses Google's free speech recognition service
- **Text Summarization**: Implements NLTK for extractive summarization
- **Content Discovery**: Scrapes web results instead of using paid APIs
- **Description Options**: Generates multiple concise description options (4-5 lines) based on different sources
- **Description Validation**: Checks for potential issues in generated descriptions
- **Tag Integration**: Automatically adds relevant short tags to the default description section

## Tech Stack

- Frontend: HTML + Bootstrap
- Backend: Flask (Python)
- NLP: NLTK, BeautifulSoup4
- Deployment: Docker, Choreo
- No paid APIs required! 