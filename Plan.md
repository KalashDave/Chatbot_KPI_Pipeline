# Project Goal
Build an end-to-end data pipeline and performance dashboard to track customer service chatbot KPIs using the Bitext Customer Support dataset.

# Architecture & Tools
* **Language:** Python 3.12+
* **Package Manager:** `uv` (Fast dependency resolution)
* **Linting & Formatting:** `ruff` (Modern, ultra-fast code quality tool)
* **Testing:** `pytest`
* **Version Control:** Git / GitHub
* **Storage:** Local SQLite database
* **UI/Visualization:** Streamlit

# Project Structure
This layout separates data handling, the user interface, and automated testing.

chatbot-kpi-dashboard/
  ├── .env                   # Stores HF_TOKEN (Do not commit to GitHub)
  ├── .gitignore             # Excludes .env, virtual environments, data/, and __pycache__/
  ├── plan.md                # This project roadmap
  ├── README.md              # Public documentation for your GitHub repo
  ├── pyproject.toml         # Dependency list managed by uv (includes ruff configs)
  ├── data/                  # Local data storage (Do not commit to GitHub)
  │   └── chatbot_metrics.sqlite  
  ├── src/                   # Main source code directory
  │   ├── ingest.py          # Script to pull data from Hugging Face
  │   ├── process.py         # Script to engineer features and calculate KPIs
  │   ├── database.py        # Script to create and update the SQLite tables
  │   └── app.py             # Streamlit application for the dashboard
  └── tests/                 # Automated testing directory
      └── test_process.py    # Pytest unit tests for your data logic

# Phase 0: Environment & Repository Setup
* Initialize a local Git repository and create a `.gitignore` file.
* Use `uv venv` to create the virtual environment.
* Use `uv pip install` to install dependencies: `datasets`, `huggingface_hub`, `pandas`, `sqlite3`, `streamlit`, `python-dotenv`, `pytest`, `ruff`, `plotly`.
* Create a `.env` file to securely store the `HF_TOKEN`.

# Phase 1: Data Ingestion (`src/ingest.py`)
* Load environment variables using `python-dotenv`.
* Connect to the Hugging Face API using the `datasets` library.
* Download the "train" split of the `bitext/Bitext-customer-support-llm-chatbot-training-dataset`.
* Convert the data into a Pandas DataFrame for cleaning and manipulation.

# Phase 2: Feature Engineering (`src/process.py`)
Generate the following synthetic columns to support all 10 realistic KPIs:
* **Time Metrics:** Generate a synthetic `timestamp` column (30-day period). Create `average_handling_time` (benchmark: 2-5 min).
* **User Tracking:** Generate a `user_id` column to calculate **Return Visitor Rate** (benchmark: > 30%) and **Conversation Volume**.
* **Fallback Rate:** Create an `is_fallback` flag indicating a failure to understand (benchmark: < 10%).
* **Human Takeover Rate:** Generate a `human_takeover` flag for agent handovers (benchmark: < 25%).
* **Resolution Rate (FCR):** Create an `is_resolved` flag for first-contact resolution (benchmark: > 65%).
* **Automation Rate:** Implicitly calculated as non-human takeovers (benchmark: 70-85%).
* **Customer Satisfaction:** Generate `csat_score` (1-5) and compute percentage of positive ratings (benchmark: > 80%).
* **Business Impact:** Generate a `converted` flag for **Conversion Rate** (benchmark: 5-15%) and a `would_be_ticket` flag to calculate the **Ticket Deflection Rate** (benchmark: > 50%).

# Phase 3: Testing & Code Quality (`tests/`)
* Use `ruff format .` and `ruff check .` to automatically format code and catch syntax errors.
* Write unit tests in `test_process.py` using `pytest`:
    * **Bounds Testing:** Ensure the generated `csat_score` is never less than 1 or greater than 5.
    * **Column Validation:** Ensure the 10 KPI logic boolean columns (`is_fallback`, `human_takeover`, `is_resolved`, `converted`, `would_be_ticket`) are present and typed correctly.
    * **Data Type Testing:** Ensure `average_handling_time` outputs as an integer or float, not a string.

# Phase 4: Data Storage (`src/database.py`)
* Create a local SQLite database named `chatbot_metrics.sqlite` inside the `data/` folder.
* Write the engineered Pandas DataFrame into a structured SQL table, enforcing data types for boolean variables.
* Run the script to populate the database only after all `pytest` checks pass.

# Phase 5: Dashboard Visualization (`src/app.py`)
Build a visually impressive, highly interactive Streamlit dashboard that reads from `chatbot_metrics.sqlite`. Display all 10 standard Chatbot KPIs.
* **Brand Styling (Custom CSS):** Override the default theme. Use a sleek, premium Dark Theme with glassmorphism effects. Primary Color: `#00F0FF` (Cyan). Secondary Color: `#FF0055` (Neon Pink). Metric cards must have semi-transparent backgrounds, glowing borders, and rounded corners to look "visually stunning".
* **Layout Structure:** Use `st.set_page_config(layout="wide")`. Create a sidebar with 'Select Date Range' and a multi-select for 'Filter by Intent'. Title: "OTA Mila Performance Dashboard".
* **KPI Matrix (Top Rows):** Group the 10 KPIs into 3 categories:
    * **Efficiency:** Automation Rate, Resolution Rate, Human Takeover Rate, Fallback Rate, Avg. Handling Time.
    * **Customer Experience:** CSAT Score, Return Visitor Rate, Conversation Volume.
    * **Business Impact:** Conversion Rate, Ticket Deflection Rate.
* **Middle Row (Plotly Charts):** Use `st.columns(2)` and `plotly.express`. Left: Time-series line chart of "Conversation Volume vs. Human Takeovers" (Deep Blue for volume, Coral for takeovers). Right: Horizontal bar chart of "Average Handling Time by Intent" sorted longest to shortest.
* **Bottom Row (QA Log):** Query the 10 most recent chats where `csat_score` is 1 or 2, a fallback occurred, or a human takeover happened. Display using `st.dataframe`.