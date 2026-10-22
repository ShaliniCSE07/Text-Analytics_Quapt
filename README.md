# Text Analytics Pipeline & Dashboard

A robust, full-stack application for automated text analytics, fine-grained sentiment analysis, semantic topic tagging, AI-driven summarization, and data visualization.

---

## 🌟 Key Features

### Backend & Analytics Pipeline (FastAPI & Python)
* **Language Filtering (`app/language_filter.py`)**: Uses `langdetect` to filter non-English or empty reviews, marking unsupported inputs gracefully.
* **Sentiment Analysis (`app/sentiment.py`)**:
  * Utilizes `cardiffnlp/twitter-roberta-base-sentiment-latest` transformer model for high-accuracy predictions (`Positive`, `Negative`, `Neutral`).
  * **Contrast Word Logic**: Detects contrast keywords (`but`, `however`), splits multi-clause reviews, and resolves mixed sentiment.
  * **Confidence Scoring**: Records the probability score of predictions to flag low-confidence outputs for manual review.
* **Semantic Topic Tagging (`app/topics.py`)**:
  * Uses `SentenceTransformer` (`all-MiniLM-L6-v2`) to compute cosine similarity against configured insurance topic descriptions (e.g. `Claims - Settlement Speed`, `Service - Call Centre and Support`).
* **Distinctive Keyword Extraction (`app/keywords.py`)**: Uses TF-IDF and relative frequency scoring to extract highly distinctive phrases (unigrams/bigrams) that characterize Positive vs. Negative reviews (e.g. `claim settlement`, `renewal premium`, `surveyor`).
* **AI Summarization (`app/summarizer.py`)**: Uses `facebook/bart-large-cnn` to auto-generate concise, executive summaries of review subsets.
* **Runtime Topic Management (`data/topics_config.json`)**: Configured topics are saved as JSON and can be edited via REST API dynamically without restarting the server.
* **Relational Database (`app/database.py`)**: Stores raw reviews and pipeline outputs in SQLite (`data/reviews.db`) for rapid querying across products (`Acme Health Shield`, `Acme Motor Secure`).

### Frontend Dashboard (React, Tailwind CSS, Recharts)
* **Dark Theme UI**: Premium aesthetic with deep blues/grays and amber accents.
* **Multi-Page Navigation (React Router)**:
  * **Dashboard**: High-level statistical breakdown and sentiment distribution.
  * **Customer Reviews**: Paginated, filterable data table with Excel export.
  * **Trends & Volatility**: `Recharts` visualizations showing Sentiment Over Time and Sentiment by Product. Includes automated Spike Detection for negative trend alerts.
  * **AI Insights & Themes**: Surfaces the `BART` generated summary and semantic TF-IDF Distinctive Keywords panels.
  * **Needs Review**: Flags low-confidence model outputs. Allows auditors to manually fix incorrect sentiments or tags via a Correction Modal.
  * **Settings (Topic Admin)**: Interactive CRUD interface to Add, Edit, or Delete semantic topics in real-time.
  * **Review Detail**: Deep dive into individual reviews, showcasing a timeline of historical manual corrections (`data/corrections_log.csv`).

---

## 🛠️ Technology Stack

**Backend:**
* Python 3.9+
* FastAPI & Uvicorn (REST API)
* PyTorch & Hugging Face `transformers` (RoBERTa & BART)
* `sentence-transformers` (MiniLM)
* `scikit-learn` (TF-IDF Vectorizer)
* SQLite (Storage)

**Frontend:**
* React 18 & Vite
* React Router v6
* Tailwind CSS v4 (Custom Dark Theme)
* Recharts (Data Visualizations)
* Lucide React (Icons)
* SheetJS (`xlsx`) (Excel Exports)
* Axios (API Client)

---

## 📁 Repository Structure

```text
text_analytics/
├── app/
│   ├── evaluate_accuracy.py    # Sentiment model performance evaluation
│   ├── keywords.py             # TF-IDF distinctive keyword extraction
│   ├── main.py                 # FastAPI application & endpoints
│   ├── pipeline.py             # Core analyze_review function
│   ├── sentiment.py            # RoBERTa sentiment model integration
│   ├── summarizer.py           # BART summarization integration
│   ├── topics.py               # SentenceTransformer topic tagger
│   ├── topics_config.py        # JSON-backed topic config loader
│   ├── database.py             # SQLite schema and initialization
│   ├── load_reviews.py         # Batch ingest CSV to SQLite
│   └── run_pipeline_on_db.py   # Run NLP pipeline across SQLite rows
├── data/
│   ├── reviews.db              # SQLite Database (generated)
│   ├── topics_config.json      # Dynamic topic taxonomy (generated)
│   ├── corrections_log.csv     # Manual auditor correction history
│   └── sample_customer_reviews.csv
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── src/
│   │   ├── api/client.js       # Axios endpoint wrappers
│   │   ├── components/         # Reusable React UI elements (Charts, Modals)
│   │   ├── pages/              # React Router Page Views
│   │   ├── App.jsx             # Router layout & Sidebar implementation
│   │   └── index.css           # Tailwind tokens & dark theme
├── README.md
└── requirements.txt
```

---

## 🚀 Getting Started

### 1. Backend Setup

```bash
# Create & activate virtual environment
python -m venv venv
# Windows: .\venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install Node dependencies
npm install

# Start the Vite dev server
npm run dev
```

Visit `http://localhost:5173` in your browser to interact with the Sentiment Analytics Dashboard!

---

## 🧠 Fine-Tuning the Model (Insurance Domain)

This branch includes scripts for fine-tuning the RoBERTa model on domain-specific insurance data and comparing it to the zero-shot baseline.

### 1. Baseline Evaluation (Pretrained)
To evaluate the current `cardiffnlp` model on the `data/labeled_validation_set.csv`:
```bash
python app/evaluate_baseline.py