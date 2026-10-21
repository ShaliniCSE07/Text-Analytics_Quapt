# Text Analytics Pipeline & Dashboard

A robust, enterprise-ready full-stack application for automated customer feedback analytics, fine-grained sentiment analysis, business emotion detection, semantic topic tagging, AI-driven collective summarization, active-learning correction memory, and interactive data visualization.

---

## 🌟 Key Features

### 1. Sentiment & Clause Analysis (`app/sentiment.py`)
* **Transformer Foundation**: Powered by `cardiffnlp/twitter-roberta-base-sentiment-latest` for 3-class sentiment prediction (`Positive`, `Negative`, `Neutral`).
* **Contrast Clause Splitting**: Identifies contrasting discourse markers (`but`, `however`, `although`, `yet`) to decompose complex reviews and accurately resolve dominant sentiment.
* **Confidence Scoring**: Records calibrated confidence percentages (0–100%) to isolate ambiguous reviews and highlight them for human audit.

### 2. Business Emotion Detection (`app/emotion.py`)
* **GoEmotions Integration**: Utilizes `SamLowe/roberta-base-go_emotions` mapped directly to 6 actionable business emotions:
  * `Anger` (hostility, outrage)
  * `Frustration` (friction, delay, annoyance)
  * `Disappointment` (unmet expectations, regret)
  * `Anxiety` (worry, fear, policy risk)
  * `Confusion` (unclear clauses, billing ambiguity)
  * `Delight` (gratitude, admiration, exceptional service)
* **Confidence Gating & Fallback**: Predictions with confidence below 35% fallback to `Uncertain`, preventing false escalations.
* **Granular Score Vector**: Stores complete multi-emotion probability distributions (`Emotion_Scores`) as JSON for in-depth root cause analysis.
* **Non-Destructive Batch Re-Analysis**: `POST /analyze-emotions` enables asynchronous re-analysis across database records without overwriting existing sentiment classifications or tags.

### 3. Self-Learning Correction System (`app/learning.py`, `app/embeddings.py`)
* **Dynamic Semantic Memory**: Maintains an in-memory cosine index of approved human corrections powered by shared SentenceTransformer embeddings (`all-MiniLM-L6-v2`).
* **Active-Learning Sentiment Override**: When a new incoming review strongly matches an approved historical correction (`similarity >= 0.85`), the learned label overrides the base model output (`Label_Source = 'learned'`).
* **Linguistic Signature Safeguards**: Employs structural signature extraction (`_signature()`) to detect negations (`not`, `never`, `no`) and contrast words (`but`, `however`), strictly blocking false-positive matches across opposite polarities (e.g. "settlement was fast" vs. "settlement was not fast").
* **Human Lock Protection**: Reviews verified or corrected by human reviewers (`Label_Source = 'human'`) are permanently locked and skipped by automated pipeline batch jobs.
* **Admin Memory Governance**: Complete audit log via `Review_Corrections` table with dedicated administrative endpoints (`GET /admin/corrections`, `PATCH /admin/corrections/{id}/approval`) to review, approve, or revoke entries from active learning memory.

### 4. Semantic Topic Tagging & Taxonomy Management (`app/topics.py`, `app/topics_config.py`)
* **Zero-Shot Semantic Matching**: Classifies reviews into 31 configured insurance industry topics (e.g., `Claims - Settlement Speed`, `Pricing - Renewal Increase`, `Customer Support - Responsiveness`) based on cosine similarity to semantic topic anchor descriptions.
* **Shared Embedding Pipeline**: Utilizes lazy-loaded shared embeddings across topics and learning modules to minimize GPU/RAM overhead.
* **Runtime Taxonomy CRUD**: Add, edit, or delete topics dynamically via REST API (`/admin/topics`) with immediate persistence to `data/topics_config.json`.

### 5. Distinctive Keyword Extraction & AI Summarization
* **TF-IDF Keyword Extraction (`app/keywords.py`)**: Computes distinctive unigrams and bigrams distinguishing positive and negative feedback using relative frequency scoring.
* **Collective AI Summaries (`app/summarizer.py`)**: Uses `facebook/bart-large-cnn` to synthesize executive summaries of customer sentiment and pain points across filterable product slices.

### 6. Interactive Dark-Themed Frontend Dashboard (`frontend/`)
* **Responsive Dark Aesthetics**: Modern interface with high-contrast typography, tailored dark theme palette, and smooth micro-animations.
* **Multi-Page Navigation (React Router)**:
  * **Dashboard**: Key performance indicators, review volume metrics, sentiment splits, and high-level health summaries.
  * **Customer Reviews**: Paginated, searchable data table with product filters, rating badges, tag chips, and instant Excel export.
  * **Emotions Analytics**: Comprehensive emotion distributions, historical trends, product-level emotion matrix, and confidence threshold filtering.
  * **Trends & Volatility**: Interactive Recharts time-series tracking sentiment changes and automated negative spike alerts.
  * **AI Insights & Themes**: Collective BART summaries combined with dynamic TF-IDF distinctive keyword cards.
  * **Needs Review**: Dedicated audit queue highlighting low-confidence predictions (< 60%) with a built-in Correction Modal.
  * **Review Detail**: Granular modal inspection showcasing raw text, model confidence, full emotion score vectors, and complete correction history.
  * **Settings (Topic Admin)**: Admin interface to manage dynamic topic taxonomy descriptions in real time.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | FastAPI, Uvicorn, Pydantic, Python 3.9+ |
| **NLP & Deep Learning** | PyTorch, Hugging Face Transformers (`roberta-base-sentiment-latest`, `go_emotions`, `bart-large-cnn`), `sentence-transformers` (`all-MiniLM-L6-v2`) |
| **Feature Extraction** | Scikit-learn (TF-IDF Vectorizer), `langdetect` |
| **Database & Storage** | SQLite (`data/reviews.db`), JSON (`data/topics_config.json`), CSV audit log |
| **Frontend Framework** | React 18, Vite |
| **Routing & State** | React Router v6, Axios |
| **Styling & Icons** | Tailwind CSS (Tailored Dark Theme), Lucide React |
| **Data Visualization** | Recharts (Line Charts, Bar Charts, Area Charts, Pie Charts) |
| **Reporting & Export** | SheetJS (`xlsx`) for client-side Excel exports |

---

## 🗄️ Database Architecture (`data/reviews.db`)

The SQLite storage layer consists of three interconnected tables:

### 1. `Customer_Reviews` (Raw Ingestion)
| Column | Type | Description |
| :--- | :--- | :--- |
| `Platform_Reference_Id` | `TEXT PRIMARY KEY` | Unique review identifier (e.g., `TW-2007`, `FB-1042`) |
| `Platform` | `TEXT` | Source channel (e.g., `Twitter`, `Facebook`, `Trustpilot`) |
| `Company` | `TEXT` | Target enterprise organization |
| `Product` | `TEXT` | Insurance product line (e.g., `Acme Health Shield`, `Acme Motor Secure`) |
| `Review` | `TEXT` | Raw customer review body text |
| `Month_Year` | `TEXT` | Formatted timeline date (`YYYY-MM`) |
| `Load_timestamp` | `TEXT` | Ingestion timestamp |

### 2. `Customer_Reviews_Analysis` (Pipeline Inference & Annotations)
| Column | Type | Description |
| :--- | :--- | :--- |
| `Platform_Reference_Id` | `TEXT PRIMARY KEY` | Foreign reference to `Customer_Reviews` |
| `Rating` | `TEXT` | Active sentiment rating (`Positive`, `Negative`, `Neutral`) |
| `Tags` | `TEXT` | Semicolon-delimited list of semantic topic tags |
| `Confidence` | `INTEGER` | Sentiment model confidence percentage (0–100) |
| `Emotion` | `TEXT` | Primary business emotion (`Anger`, `Frustration`, `Disappointment`, `Anxiety`, `Confusion`, `Delight`, `Uncertain`) |
| `Emotion_Confidence` | `INTEGER` | Calibrated emotion confidence percentage |
| `Emotion_Scores` | `TEXT` | Full JSON object with probabilities for all 6 business emotions |
| `Emotion_Model` | `TEXT` | Identifier of emotion model used (`roberta-base-go_emotions`) |
| `Label_Source` | `TEXT` | Origin of the active rating (`model`, `human`, or `learned`) |
| `Model_Rating` | `TEXT` | Original base model prediction prior to human/learned override |
| `Learned_From` | `TEXT` | Reference ID of the approved correction memory row, if applied |
| `Learned_Similarity` | `INTEGER` | Percentage cosine similarity (0–100) between input and matched correction |
| `Load_timestamp` | `TEXT` | Timestamp of analysis |

### 3. `Review_Corrections` (Active-Learning Audit Log & Memory Source)
| Column | Type | Description |
| :--- | :--- | :--- |
| `Correction_Id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Auto-incrementing correction log identifier |
| `Platform_Reference_Id` | `TEXT` | Target review ID |
| `Review_Text` | `TEXT` | Review text snapshot at the time of correction |
| `Original_Rating` | `TEXT` | Earliest known AI prediction before any human edit |
| `Corrected_Rating` | `TEXT` | Human-corrected sentiment value |
| `Original_Tags` | `TEXT` | Tags before correction |
| `Corrected_Tags` | `TEXT` | Human-adjusted tags |
| `Corrected_By` | `TEXT` | Auditor username / email |
| `Corrected_At` | `TEXT` | ISO-8601 UTC timestamp |
| `Approved_For_Learning` | `INTEGER` | Binary flag (`1` = active memory, `0` = excluded from learning) |

---

## 🔌 API Reference

### Health & Review Analysis
* `GET /health`: System status and DB connectivity check.
* `POST /analyze-review`: Single review real-time inference (language check, sentiment, contrast clauses, emotions, topic tags, and learned memory match).
* `GET /reviews`: Paginated review listings with filtering by `product`, `rating`, `search`, and sorting.
* `GET /reviews/{platform_reference_id}`: Detailed inspection of a specific review, including emotion breakdown and correction history.
* `PATCH /reviews/correct`: Submit human correction for sentiment and/or tags. Logs to `Review_Corrections` and locks `Label_Source = 'human'`.

### Emotion Analytics
* `GET /reviews/emotions`: Paginated reviews with emotion filtering and minimum confidence threshold (`min_confidence`).
* `GET /reviews/emotions/summary`: Aggregated emotion distributions, dominant emotions, and sentiment cross-tabulation.
* `GET /reviews/emotions/trend`: Time-series monthly volume breakdown per business emotion.
* `POST /analyze-emotions`: Asynchronous batch re-analysis to compute/update emotions across all eligible database rows.

### Aggregations & AI Insights
* `GET /reviews/summary`: Overall review counts, sentiment volume, average confidence, and flagged count.
* `GET /reviews/trend`: Monthly time-series data for positive, neutral, and negative review volume.
* `GET /reviews/by-product`: Breakdown of review counts and sentiment percentages grouped by product line.
* `GET /reviews/summary-text`: Generates collective natural-language summary via BART for a selected product or all products.
* `GET /reviews/keywords`: Top positive and negative distinctive keywords via TF-IDF.
* `GET /reviews/low-confidence`: Returns reviews with confidence score < 60% requiring human review.
* `GET /reviews/spike-check`: Identifies sudden negative sentiment spikes using moving-average anomaly detection.

### Admin & Taxonomy Management
* `GET /admin/topics`: Retrieve all active semantic topics and descriptions.
* `POST /admin/topics`: Create a new topic with semantic anchor description.
* `PUT /admin/topics/{name}`: Update description for an existing topic.
* `DELETE /admin/topics/{name}`: Remove a topic from the taxonomy.
* `GET /admin/corrections`: View all historical human corrections and their learning approval status.
* `PATCH /admin/corrections/{correction_id}/approval`: Toggle `Approved_For_Learning` (`true`/`false`) to control inclusion in the self-learning memory index.

---

## 📁 Repository Structure

```text
text_analytics/
├── app/
│   ├── database.py             # SQLite schema, tables (Reviews, Analysis, Corrections), & migrations
│   ├── embeddings.py           # Shared lazy-loaded SentenceTransformer model instance
│   ├── emotion.py              # GoEmotions model integration & business emotion mapper
│   ├── evaluate_accuracy.py    # Sentiment model performance evaluation
│   ├── export_txt_report.py    # Text report exporter
│   ├── keywords.py             # TF-IDF distinctive keyword extraction
│   ├── language_filter.py      # Language detection & support filter
│   ├── learning.py             # Active-learning correction memory & signature validation
│   ├── load_reviews.py         # Batch ingest raw review CSVs to SQLite
│   ├── main.py                 # FastAPI application, routes, & admin endpoints
│   ├── migrate_corrections.py  # One-time migration of legacy correction logs
│   ├── pipeline.py             # Core review analysis pipeline with learned memory integration
│   ├── preprocess.py           # Text cleaning & normalization utilities
│   ├── run_pipeline_on_db.py   # Batch pipeline execution across database rows
│   ├── sentiment.py            # RoBERTa sentiment classifier & contrast clause logic
│   ├── summarizer.py           # Collective feedback summarization using BART
│   ├── topics.py               # Semantic topic tagger using shared embeddings
│   └── topics_config.py        # Dynamic topic taxonomy configuration loader
├── data/
│   ├── reviews.db              # SQLite Database
│   ├── topics_config.json      # Dynamic topic taxonomy
│   ├── corrections_log.csv     # Auditor manual correction audit log
│   └── sample_customer_reviews.csv
├── frontend/
│   ├── src/
│   │   ├── api/client.js       # Axios client & API endpoints
│   │   ├── components/         # Reusable React components (Charts, Modals, Tables)
│   │   ├── pages/              # Page views (Dashboard, Reviews, Emotions, Trends, Settings, etc.)
│   │   ├── App.jsx             # Top-level routing & layout
│   │   └── index.css           # Styling & dark-mode theme tokens
│   ├── package.json
│   └── vite.config.js
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

# Initialize database schema & run migrations
python -m app.database

# Ingest initial reviews dataset (if not already loaded)
python -m app.load_reviews

# (Optional) Migrate legacy correction CSV to database memory
python -m app.migrate_corrections

# (Optional) Run the complete NLP pipeline across all database rows
python -m app.run_pipeline_on_db

# Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
```

Visit `http://localhost:5173` in your browser to interact with the dashboard.
API documentation is automatically available via Swagger UI at `http://localhost:8000/docs`.
