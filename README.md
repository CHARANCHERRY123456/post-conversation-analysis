# Post-Conversation Analysis System

A Django REST Framework application that analyzes AI-human conversations using multiple metrics including sentiment analysis, empathy scoring, clarity assessment, and more. This system provides automated daily analysis of conversations and exposes RESTful APIs for data management.

## Features

### 11+ Analysis Metrics
- **Clarity Score**: Measures readability using Flesch Reading Ease
- **Relevance Score**: Semantic similarity between user queries and AI responses
- **Accuracy Score**: Powered by Google Gemini API for factual correctness
- **Completeness Score**: Evaluates response thoroughness and detail
- **Sentiment Analysis**: Compound sentiment score using VADER
- **Empathy Score**: Emotional alignment analysis using DistilRoBERTa emotion model
- **Fallback Detection**: Identifies generic/unhelpful responses
- **Resolution Score**: Measures issue resolution effectiveness
- **Escalation Detection**: Detects escalation keywords in conversations
- **Response Time Analysis**: Average response time calculation
- **Overall Score**: Weighted aggregate of all metrics

### API Endpoints
- Upload and retrieve conversation data with nested messages
- Analyze conversations and get detailed metrics
- Retrieve all analysis results
- RESTful design with JSON request/response

### Automated Daily Processing
- Scheduled daily analysis at midnight using `schedule` library
- Windows-compatible cron alternative
- Automatic database updates

## Tech Stack

- **Backend**: Django 5.1.3, Django REST Framework 3.15.2
- **Database**: SQLite (easily replaceable with PostgreSQL/MySQL)
- **ML Models**: 
  - HuggingFace Transformers (emotion-english-distilroberta-base)
  - Sentence Transformers (all-MiniLM-L6-v2)
  - VADER Sentiment Analysis
- **AI API**: Google Gemini 2.0 Flash
- **Scheduling**: Python `schedule` library
- **NLP**: TextBlob, textstat

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/CHARANCHERRY123456/post-conversation-analysis.git
cd post-conversation-analysis
```

2. **Create and activate virtual environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
Create a `.env` file in the project root:
```env
GOOGLE_GEMINI_API_KEY=your_gemini_api_key_here
```
Get your Gemini API key from: https://makersuite.google.com/app/apikey

5. **Run database migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser (optional)**
```bash
python manage.py createsuperuser
```

7. **Run development server**
```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`

## API Documentation

### 1. Upload/Retrieve Conversations

**Endpoint**: `/conversation/`

#### GET - Retrieve all conversations
```bash
curl -X GET http://127.0.0.1:8000/conversation/
```

**Response**:
```json
[
  {
    "id": 1,
    "user_id": "user123",
    "created_at": "2024-01-15T10:30:00Z",
    "messages": [
      {
        "sender": "user",
        "message": "What is machine learning?"
      },
      {
        "sender": "AI",
        "message": "Machine learning is a subset of artificial intelligence..."
      }
    ]
  }
]
```

#### POST - Upload new conversation
```bash
curl -X POST http://127.0.0.1:8000/conversation/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "messages": [
      {"sender": "user", "message": "How does neural network work?"},
      {"sender": "AI", "message": "Neural networks are computational models..."}
    ]
  }'
```

**Response**:
```json
{
  "id": 2,
  "user_id": "user123",
  "created_at": "2024-01-15T11:00:00Z",
  "messages": [...]
}
```

### 2. Analyze Conversation

**Endpoint**: `/analysis/<conversation_id>/`

#### POST - Trigger analysis
```bash
curl -X POST http://127.0.0.1:8000/analysis/1/
```

**Response**:
```json
{
  "conversation_id": 1,
  "clarity_score": 85.5,
  "relevance_score": 92.3,
  "accuracy_score": 88.0,
  "completeness_score": 90.0,
  "sentiment_score": 0.85,
  "empathy_score": 0.78,
  "fallback_count": 0,
  "resolution_score": 95.0,
  "escalation_detected": false,
  "avg_response_time": 2.5,
  "overall_score": 87.8,
  "analyzed_at": "2024-01-15T12:00:00Z"
}
```

#### GET - Retrieve existing analysis
```bash
curl -X GET http://127.0.0.1:8000/analysis/1/
```

### 3. Get All Analyses

**Endpoint**: `/analyses/`

#### GET - Retrieve all analysis results
```bash
curl -X GET http://127.0.0.1:8000/analyses/
```

**Response**:
```json
[
  {
    "conversation_id": 1,
    "clarity_score": 85.5,
    "relevance_score": 92.3,
    ...
  },
  {
    "conversation_id": 2,
    "clarity_score": 78.0,
    ...
  }
]
```

## Automated Scheduler Setup

The system includes automated daily analysis at midnight using the `schedule` library.

### Running the Scheduler

**Option 1: Run manually**
```bash
python scheduler.py
```
The script will run continuously and execute analysis at 00:00 every day.

**Option 2: Background process (Windows)**
```bash
# Using pythonw (no console window)
start /B pythonw scheduler.py

# Or use Task Scheduler for production
```

**Option 3: Linux/Mac (systemd service)**
Create `/etc/systemd/system/conversation-analysis.service`:
```ini
[Unit]
Description=Conversation Analysis Scheduler
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/post-conversation-analysis
ExecStart=/path/to/venv/bin/python scheduler.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable conversation-analysis
sudo systemctl start conversation-analysis
```

### How It Works

1. The scheduler runs at 00:00 daily
2. Fetches all conversations from the database
3. Analyzes each conversation using 11+ metrics
4. Saves/updates analysis results in the database
5. Logs success/failure for each conversation

## Project Structure

```
post-conversation-analysis/
├── analysis_app/              # Main Django app
│   ├── models.py              # Conversation, Message, ConversationAnalysis models
│   ├── serializers.py         # DRF serializers for API
│   ├── views.py               # API endpoints
│   ├── utils.py               # Core analysis utilities (11 metrics)
│   ├── gemini_utils.py        # Gemini API integration
│   ├── empathy_utils.py       # Empathy scoring logic
│   ├── cron.py                # Daily analysis cron job
│   └── urls.py                # URL routing
├── post_analysis_main/        # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── scheduler.py               # Scheduler entry point
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (create this)
└── README.md                  # This file
```

## Analysis Metrics Explained

### 1. Clarity Score (0-100)
Uses Flesch Reading Ease formula to measure how easy the AI responses are to understand.
- **90-100**: Very easy to read
- **60-70**: Plain English
- **0-30**: Very difficult to read

### 2. Relevance Score (0-100)
Calculates semantic similarity between user queries and AI responses using sentence embeddings.
- Uses `all-MiniLM-L6-v2` model
- Higher score = more relevant response

### 3. Accuracy Score (0-100)
Powered by Google Gemini API to evaluate factual correctness and reliability of AI responses.

### 4. Completeness Score (0-100)
Evaluates whether responses are thorough based on:
- Response length
- Presence of examples
- Use of explanatory phrases

### 5. Sentiment Score (-1 to 1)
VADER sentiment analysis compound score:
- **Positive**: > 0.05
- **Neutral**: -0.05 to 0.05
- **Negative**: < -0.05

### 6. Empathy Score (0-1)
Measures emotional alignment between user and AI using emotion classification model.
- Detects 7 emotions: joy, sadness, anger, fear, surprise, disgust, neutral
- Calculates cosine similarity between emotion vectors

### 7. Fallback Count
Number of generic/unhelpful responses detected:
- "I don't know"
- "I'm not sure"
- "Sorry, I can't help"
- etc.

### 8. Resolution Score (0-100)
Measures problem-solving effectiveness:
- Checks for resolution keywords
- Analyzes positive sentiment in final messages
- Higher score = better issue resolution

### 9. Escalation Detection (Boolean)
Detects if conversation required escalation:
- Keywords: "speak to manager", "file complaint", "escalate"
- Returns `true` if escalation detected

### 10. Average Response Time (seconds)
Calculates average time between user message and AI response (simulated with random values 1-5s in current implementation).

### 11. Overall Score (0-100)
Weighted average of all metrics:
- Clarity: 10%
- Relevance: 20%
- Accuracy: 20%
- Completeness: 15%
- Sentiment: 10%
- Empathy: 10%
- Resolution: 10%
- Fallback penalty: -5 points per fallback
- Response time bonus: +5 if < 3s

## Error Handling

The system includes comprehensive error handling:

- **API Quota Exceeded**: Graceful fallback when Gemini API quota is reached
- **Model Loading Errors**: Automatic fallback to keyword-based analysis
- **Database Errors**: Transaction rollback and error logging
- **Invalid Input**: JSON validation and error messages
- **Network Issues**: Retry logic and timeout handling

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_GEMINI_API_KEY` | Google Gemini API key for accuracy scoring | Yes |
| `DEBUG` | Django debug mode (default: True) | No |
| `SECRET_KEY` | Django secret key | No (auto-generated) |

## Development

### Run Tests
```bash
python manage.py test analysis_app
```

### Access Django Admin
1. Create superuser: `python manage.py createsuperuser`
2. Visit: `http://127.0.0.1:8000/admin/`
3. Login with superuser credentials

### Database Management
```bash
# Reset database
python delete.py

# Create fresh migrations
python manage.py makemigrations
python manage.py migrate
```

## Troubleshooting

### Issue: "No module named 'google.generativeai'"
**Solution**: 
```bash
pip install google-generativeai
```

### Issue: "Model not found" errors
**Solution**: The system will download required models on first run. Ensure stable internet connection.

### Issue: Scheduler not running
**Solution**: 
1. Check if `scheduler.py` is running
2. Verify no port conflicts
3. Check logs for errors

### Issue: API returns empty analysis
**Solution**:
1. Ensure conversation exists: `GET /conversation/`
2. Check Gemini API key in `.env`
3. Verify internet connection

## Performance Optimization

- Models are loaded once at startup (singleton pattern)
- Lightweight models used (242MB total vs 1.43GB+ alternatives)
- Semantic similarity uses efficient sentence transformers
- Database queries optimized with `select_related()`

## Contributing

This is an internship assignment project. For improvements:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is created as part of an internship assignment.

## Contact

**Developer**: Charan Cherry  
**GitHub**: [@CHARANCHERRY123456](https://github.com/CHARANCHERRY123456)  
**Repository**: [post-conversation-analysis](https://github.com/CHARANCHERRY123456/post-conversation-analysis)

## Acknowledgments

- **Kipps.AI** - Internship assignment provider
- **Google Gemini** - AI-powered accuracy scoring
- **HuggingFace** - Pre-trained emotion detection models
- **Django Community** - Excellent framework and documentation

---

Built with ❤️ for Kipps.AI Internship Assignment
