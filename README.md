# 🚛 AI Delivery Planner & Route Optimizer

![Python](https://img.shields.io/badge/Python-3.13%2B-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.51-FF4B4B?style=for-the-badge&logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Code Style](https://img.shields.io/badge/Code%20Style-Black-000000?style=for-the-badge)
![Coverage](https://img.shields.io/badge/Coverage-90%25-brightgreen?style=for-the-badge)

**Intelligent Distribution Platform for Perishable Goods.**
An advanced system leveraging genetic algorithms and clustering to optimize delivery routes in real-time, ensuring product freshness while minimizing operational costs.

---

## 📋 Table of Contents

1. [Key Features](#-key-features)
2. [System Architecture](#-system-architecture)
3. [Installation & Setup](#-installation--setup)
4. [Running the Project](#-running-the-project)
5. [Usage Guide](#-usage-guide)
6. [Testing & Code Quality](#-testing--code-quality)
7. [Tech Stack](#-tech-stack)

---

## 🌟 Key Features

- **🧠 Inference Engine:** Automatic vehicle validation based on business rules (capacity, consumption, velocity constraints).
- **🧬 Algorithm Visualizer:** Watch step-by-step how the AI (Genetic or OR-Tools) constructs the optimal route in real-time.
- **🗺️ Interactive Maps:** Real-time route visualization on OpenStreetMap using OSRM for precise road mapping.
- **📦 Order Manifest:** Detailed breakdown of consolidated orders, including product-level details and financial summaries.
- **📊 Advanced Analytics:** Interactive dashboards for fleet efficiency, cost vs. revenue analysis, and load distribution.
- **⚖️ Fleet Management:** Dynamic load assignment to maximize truck capacity utilization (>90%).

---

## 🏗️ System Architecture

The project follows a modular **Clean Architecture** to ensure scalability and maintainability:

```
distribution_platform/
├── app/ # Presentation Layer (Streamlit)
│   ├── components/ # Reusable UI Widgets (Cards, Charts, Timelines)
│   ├── config/ # UI Constants & Enums
│   ├── services/ # Bridge services (Data, Validation, Optimization)
│   ├── state/ # Centralized Session Management
│   ├── views/ # Page Rendering Logic (Form, Results, Processing)
│   └── main.py # Application Entry Point
├── core/ # Domain Layer (The Brain)
│   ├── inference_engine/ # Validation Rule Engine
│   ├── knowledge_base/ # Business Rules Repository
│   ├── models/ # Domain Data Models (Pydantic)
│   └── services/ # Orchestrators (ETL, Solver Logic)
├── infrastructure/ # Infrastructure Layer
│   ├── external/ # External APIs (Maps, Geocoding)
│   └── persistence/ # Data Repositories (CSV, JSON, SQL)
└── tests/ # Test Suite (Pytest)
```

---

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ai-delivery-planner.git
cd ai-delivery-planner
```

### 2. Create a virtual environment

Recommended to isolate dependencies:

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

```bash
uv sync
```

### 4. Configure environment variables

Create a `.env` file in the project root based on the example below:

```env
# Database (SQL Server) - Optional if using Files mode
DB_HOST=localhost
DB_PORT=1433
DB_NAME=DistributionDB
DB_USER=sa
DB_PASSWORD=your_password
DB_DRIVER=ODBC Driver 17 for SQL Server

# Google Drive (Optional for backups)
GDRIVE_FOLDER_ID=your_folder_id
GDRIVE_CREDENTIALS_PATH=credentials.json
```

---

## ▶️ Running the Project

To launch the web application:

```bash
streamlit run distribution_platform/app/main.py
```

The application will be available at:
[http://localhost:8501](http://localhost:8501)

---

## 📱 Usage Guide

### Mission Control (Form):

- Data Ingestion: Select "Files" to upload your datasets (orders, clients, etc.) or connect to the Database.
- Fleet Configuration: Choose a standard truck model or create a Custom Prototype.
- Validation: The system validates if the selected vehicle fits the mission requirements.

### Processing:

- Select the algorithm: Genetic Evolutionary or Google OR-Tools.
- Click Initiate Sequence to start the optimization engine.

### Mission Results:

- 🌍 Geospatial Map: Interactive map with routes, legends, and markers.
- 🧬 Algorithm Visualizer: Replay the optimization process step-by-step.
- 📦 Order Manifest: Searchable table of orders with detailed product breakdown.
- 🔍 Route Inspector: Deep dive into specific truck routes with timelines and navigation links.

---

## 🧪 Testing & Code Quality

The project includes a robust test suite (>90% coverage) using pytest and unittest.mock.

```bash
pytest tests/
```

---

## 🛠️ Tech Stack

- **Language:** Python 3.13+
- **Web Framework:** Streamlit, Plotly (Charts)
- **Algorithms:** DEAP (Genetic), Google OR-Tools
- **Data Science:** Pandas, Scikit-learn (K-Means), NumPy
- **Maps & Geo:** Folium, Geopy, OSRM
- **Backups:** Google Drive (Optional)
- **Data:** CSV, XLSX, TXT, JSON, SQL
- **Data Modeling:** Pydantic
- **Quality & Testing:** Pytest, Ruff, Mypy
- **Database:** SQLAlchemy, PyODBC (SQL Server)

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
