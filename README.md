# 🚛 AI Delivery Planner & Route Optimizer

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31-FF4B4B?style=for-the-badge&logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Code Style](https://img.shields.io/badge/Code%20Style-Black-000000?style=for-the-badge)
![Coverage](https://img.shields.io/badge/Coverage-95%25-brightgreen?style=for-the-badge)

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
- **🤖 Genetic Algorithms:** Route optimization (VRP) to minimize distance and time, strictly adhering to product expiration windows.
- **🗺️ Interactive Maps:** Real-time route visualization on OpenStreetMap using OSRM for precise road mapping.
- **📦 Intelligent Clustering:** K-Means clustering of orders based on geographical location and delivery urgency.
- **⚖️ Fleet Management:** Dynamic load assignment to maximize truck capacity utilization (>90%).
- **☁️ Cloud Integration:** Automatic backup of processed data to Google Drive (optional).

---

## 🏗️ System Architecture

The project follows a modular architecture inspired by **Clean Architecture**:

```
distribution_platform/
├── app/                     # User Interface (Streamlit)
│   ├── user_interface/      # UI Components and pages
├── batch/                   # Background processes (Backup, Scheduled ETL)
├── config/                  # Centralized configuration (Settings, Enums)
├── core/                    # Business Logic (The Brain)
│   ├── inference_engine/    # Rule engine
│   ├── knowledge_base/      # Business rules
│   ├── logic/               # Algorithms (Clustering, Routing, Graph)
│   ├── models/              # Domain entities (Pydantic)
│   └── services/            # Orchestrator services (ETL, Optimization)
├── infrastructure/          # Infrastructure Layer
│   ├── database/            # SQL Connection and Queries
│   ├── external/            # External APIs (Maps, Geocoding)
│   └── persistence/         # Repositorios (Files, JSON)
└── tests/                   # Test Suite (Pytest)
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

### Data Loading:

- Select "Database" to connect to SQL Server.
- Select "Files" to upload your CSV files (orders.csv, clients.csv, etc.).

### Fleet Configuration:

- Choose a standard truck model or create a custom one.
- The AI engine will validate if the vehicle meets regulations.

### Optimization:

- Click on "Generate Optimal Route".
- The system will cluster orders and calculate the most efficient routes.

### Results:

- View the interactive map with plotted routes.
- Analyze metrics: Total cost, profit, carbon footprint, and delivery times.
- Check expiration alerts on map markers.

---

## 🧪 Testing & Code Quality

The project includes a robust test suite (>80% coverage) using pytest and unittest.mock.

```bash
pytest tests/
```

---

## 🛠️ Tech Stack

- **Language:** Python 3.13+
- **Web Framework:** Streamlit
- **Data Science:** Pandas, Scikit-learn (K-Means), NumPy
- **Maps & Geo:** Folium, Streamlit-Folium, Geopy, OSRM
- **Data Modeling:** Pydantic
- **Testing:** Pytest, Coverage
- **Database:** SQLAlchemy, PyODBC (SQL Server)

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
