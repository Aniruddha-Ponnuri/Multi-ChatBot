# Financial Chatbot 🤖💰

An intelligent financial advisory chatbot powered by AI that provides expert financial advice and real-time stock market data.

## 🌟 Features

### Core Capabilities
- 💬 **Conversational AI** - Natural language financial advice using LLM providers (Groq, OpenAI, Azure, Anthropic)
- 📈 **Real-Time Stock Data** - Live market data integration with yfinance
- 🎯 **Smart Symbol Detection** - AI extracts stock symbols from natural questions
- 👎 **User Feedback System** - Rate responses for quality tracking
- 💾 **Persistent Storage** - SQLite database for feedback and session tracking
- 📝 **Conversation History** - Maintains context across messages
- 🇮🇳 **India-Focused** - Financial advice tailored for Indian markets

### Stock Data Features
- 📊 **Live Market Data** - Current prices, volume, market cap, P/E ratios
- 📉 **Historical Analysis** - 1-month price trends and performance metrics
- 🔍 **Intelligent Extraction** - Understands company names and ticker symbols
- 🏢 **Company Info** - Sector, industry, business descriptions
- 💰 **Financial Metrics** - EPS, dividends, 52-week ranges
- 🔄 **Auto-Detection** - Automatically identifies stock-related queries
- 📈 **Multi-Stock Support** - Compare multiple stocks in one query

### Technical Highlights
- ⚡ Fast response generation with multiple LLM provider support
- 🎨 Modern React UI with feedback controls
- 📊 Real-time analytics and statistics
- 🔧 Centralized YAML configuration
- 📋 Comprehensive logging system
- 🌐 Yahoo Finance integration for market data

## 🏗️ Architecture

```
Frontend (React)          Backend (Flask)           Data Sources
─────────────────         ───────────────          ──────────────
                          
┌─────────────┐          ┌─────────────┐          ┌─────────────┐
│  Chatbot.js │◄────────►│   app.py    │◄────────►│ LLM Service │
│  (UI/UX)    │   HTTP   │  (API)      │          │  (OpenAI/   │
└─────────────┘          └──────┬──────┘          │   Groq/etc) │
                                 │                 └─────────────┘
                          ┌──────▼──────┐          ┌─────────────┐
                          │database.py  │          │yfinance     │
                          │(SQLite)     │          │(Stock Data) │
                          └─────────────┘          └─────────────┘
```

## 📦 Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn
- Groq API Key

### Backend Setup

1. **Clone the repository**
```bash
git clone https://github.com/Aniruddha-Ponnuri/Financial-ChatBot.git
cd Financial-ChatBot
```

2. **Create and activate virtual environment**
```bash
# Using conda
conda create -n chat python=3.10
conda activate chat

# Or using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Python dependencies**
```bash
cd Backend
pip install -r requirements.txt
```

**Note**: The `yfinance` package provides real-time stock market data from Yahoo Finance.

4. **Set up environment variables**

Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
ENVIRONMENT=DEV
```

5. **Configure the bot**

Edit `Backend/bot_config.yaml` to customize:
- System prompts
- Model parameters
- Database settings

### Frontend Setup

1. **Install Node dependencies**
```bash
npm install
```

2. **Verify axios and lucide-react are installed**
```bash
npm install axios lucide-react
```

## 🚀 Running the Application

### Start Backend Server

```bash
cd Backend
python app.py
```

The backend will start on `http://localhost:5000`

Expected output:
```
[INFO] Starting Financial Chatbot
[INFO] Stock data fetcher initialized and ready
* Running on http://127.0.0.1:5000
```

### Start Frontend Development Server

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.  
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.

## 🎮 Using the Application

### User Interface

1. **Chat Interface**
   - Type your financial question in the input field
   - Press Enter or click "Ask" button
   - Wait for the response

2. **Feedback System**
   - Each bot response shows two buttons: 👍 (good) and 👎 (poor)
   - Click to rate the response quality
   - Buttons highlight green (positive) or red (negative) after clicking
   - Feedback is stored for quality tracking

### Stock Query Examples

The chatbot automatically detects and fetches real-time stock data. Try these:

**Single Stock:**
```
"What's the current price of Apple stock?"
"How is TSLA performing today?"
"Tell me about Microsoft stock"
```

**Multiple Stocks:**
```
"Compare Amazon and Google stocks"
"Should I invest in NVDA or AMD?"
```

**Analysis Requests:**
```
"Analyze Tesla's stock performance"
"Is Apple stock overvalued based on P/E ratio?"
"What's the 52-week range for META?"
```

The system will:
1. 🎯 Extract stock symbols (AAPL, TSLA, MSFT, etc.)
2. 📊 Fetch live market data (price, volume, metrics)
3. 📈 Get historical trends (1-month performance)
4. 💡 Provide data-driven analysis

### Example Workflow

```
1. User: "Should I invest in mutual funds or stocks?"
   ↓
### Query Workflow

```
1. User: "Should I invest in Tesla?"
   ↓
2. System detects question and checks for stock symbols
   ↓
3. LLM Service generates response based on financial knowledge
   ↓
4. Bot: "Consider diversification..." [👍] [👎]
   ↓
5. User clicks 👍 (positive feedback)
   ↓
6. Feedback stored for quality tracking
```

### Stock Query Workflow

```
1. User: "What's Apple's stock price?"
   ↓
2. LLM extracts: symbol="AAPL", is_stock_query=true
   ↓
3. yfinance fetches real-time AAPL data
   ↓
4. Stock context injected into prompt
   ↓
5. Bot: "Apple (AAPL) is currently trading at $178.50...
         with P/E ratio of 28.5, up 7.54% this month" [👍] [👎]
```

## 🧪 Testing

### Test API Endpoints

You can test the backend API using curl or Postman:

```bash
# Health check
curl http://localhost:5000/health

# Ask a question
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are bonds?"}'
```

### Submit Feedback

```bash
curl -X POST http://localhost:5000/feedback \
  -H "Content-Type: application/json" \
  -d '{"question":"What is SIP?","answer":"Systematic Investment Plan...","rating":1}'
```

## 📊 API Endpoints

| Endpoint | Method | Description | Request Body |
|----------|--------|-------------|--------------|
| `/ask` | POST | Get chatbot response | `{question, history, session_id}` |
| `/feedback` | POST | Submit user rating | `{question, answer, rating, session_id}` |
| `/sessions` | GET | Get all chat sessions | - |
| `/sessions/<id>` | GET | Get specific session | - |
| `/sessions/<id>` | DELETE | Delete session | - |
| `/health` | GET | System health check | - |

## ⚙️ Configuration

### Bot Settings (`Backend/bot_config.yaml`)

Edit this file to customize prompts, model parameters, and database settings:

```yaml
prompts:
  system_prompt: "You are a financial assistant..."
  general_question_prompt: |
    You are an AI assistant. Answer the following question...
  financial_prompt_template: |
    You are an AI financial assistant. Use your knowledge...

model:
  name: "llama-3.1-8b-instant"
  default_temperature: 0.1
  max_tokens: 2000
```

## 📁 Project Structure

```
Financial-ChatBot/
├── Backend/
│   ├── app.py                    # Flask server with API endpoints
│   ├── config.py                 # Configuration loader
│   ├── bot_config.yaml           # Bot configuration file
│   ├── requirements.txt          # Python dependencies
│   ├── utils/
│   │   ├── logger.py             # Custom logging system
│   │   ├── database.py           # SQLite feedback handler
│   │   ├── helpers.py            # Utility functions
│   │   └── stock_data.py         # Stock data fetcher
│   └── services/
│       └── llm_service.py        # LLM provider abstraction
│   ├── bot_config.yaml           # Configuration file
│   ├── test_rl.py                # Test suite
│   ├── feedback.db               # SQLite database (auto-created)
│   ├── model_data/               # Saved models
│   │   └── reward_classifier.pkl
├── Frontend/
│   ├── src/
│   │   ├── Chatbot.js            # React chatbot component
│   │   ├── Chatbot.css           # Chatbot styles
│   │   ├── App.js                # Main app component
│   │   ├── components/
│   │   │   └── Sidebar.js        # Chat sidebar component
│   │   ├── services/
│   │   │   └── api.js            # API service layer
│   │   └── index.js              # React entry point
│   ├── public/
│   │   └── index.html            # HTML template
│   └── package.json              # Node dependencies
├── documentation/                # Project documentation
├── README.md                     # This file
└── .env                          # Environment variables
```

## 🔧 Troubleshooting

### Backend Issues

**Problem**: Import errors
```bash
# Solution: Install dependencies
cd Backend
pip install -r requirements.txt
```

**Problem**: Backend won't start
```bash
# Check Python version
python --version  # Should be 3.8+

# Verify API key is set in .env
# For Groq: GROQ_API_KEY=your_key
# For OpenAI: OPENAI_API_KEY=your_key
```

**Problem**: Stock data not working
```bash
# Verify yfinance is installed
pip list | grep yfinance

# Check logs for stock fetcher errors
# Look for: [ERROR] Error fetching stock data
```

### Frontend Issues

**Problem**: Can't connect to backend
```bash
# Ensure backend is running on port 5000
# Check Chatbot.js has correct URL: http://localhost:5000
```

**Problem**: Feedback buttons not working
```bash
# Check browser console for errors
# Verify axios is installed: npm list axios
```

### Database Issues

**Problem**: Feedback not saving
```bash
# Check database file exists
ls Backend/feedback.db

# Check logs for errors
# Look for: [ERROR] Error saving feedback
```

## 📚 Documentation

Additional documentation available in the `documentation/` folder:
- Stock Integration Guide
- LLM Provider Guide
- Currency Handling Guide
- System Architecture

## 🎯 Best Practices

1. **API Key Management**
   - Use environment variables for API keys
   - Never commit `.env` file to version control
   - Rotate keys periodically

2. **Monitor Performance**
   - Check logs regularly for errors
   - Monitor API usage and costs
   - Track response times

3. **Stock Queries**
   - Use official ticker symbols (AAPL, MSFT, etc.)
   - For Indian stocks, use .NS suffix (RELIANCE.NS)
   - Verify symbol accuracy for best results

4. **Database Maintenance**
   - Periodically backup feedback.db
   - Clean old sessions if needed
   - Monitor database size

5. **User Feedback**
   - Encourage users to provide feedback
   - Use feedback data to improve prompts
   - Track feedback patterns

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**
   - Set `ENVIRONMENT=PROD` in `.env`
   - Use production-grade API keys
   - Secure sensitive configuration

2. **Database**
   - Consider PostgreSQL for production scale
   - Implement backup strategy
   - Use connection pooling

3. **Caching**
   - Add Redis for response caching
   - Cache stock data with appropriate TTL
   - Cache LLM responses for common queries

4. **Load Balancing**
   - Use Gunicorn or uWSGI for Flask
   - Multiple worker processes
   - Consider containerization (Docker)

5. **Monitoring**
   - Set up centralized logging
   - Add error tracking (Sentry, etc.)
   - Monitor API rate limits

### Build for Production

```bash
# Build React app
npm run build

# Serve with production server
# (e.g., Nginx, Apache, or serve package)
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- **LangChain** - LLM provider abstraction
- **Groq/OpenAI/Anthropic** - LLM providers
- **yfinance** - Stock market data
- **Create React App** - Frontend scaffolding
- **Flask** - Web framework

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation in the `documentation/` folder
- Review the troubleshooting section above

## 🔄 Recent Updates

- ✨ Multi-LLM provider support (Groq, OpenAI, Azure, Anthropic)
- ✨ Real-time stock data integration with yfinance
- ✨ Smart stock symbol extraction
- ✨ India-focused financial advice
- ✨ User feedback collection (thumbs up/down)
- ✨ Chat session management
- ✨ SQLite database for persistence
- ✨ Comprehensive logging system
- ✨ Centralized YAML configuration
- 📚 Complete documentation suite

---

**Built with ❤️ for better financial decision-making**
