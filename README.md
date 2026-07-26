# Berkeley Class Scheduler 🐻

A full-stack web application designed to help UC Berkeley students optimize, plan, and visualize their course schedules. 

## 🛠️ Tech Stack
* **Backend:** Python, SQLite (`scheduler.db`)
* **Frontend:** JavaScript/React (Node.js)
* **Data Collection:** Custom web scraper (`deep_scraper.py`) for pulling accurate course data.

## 📂 Project Structure
* `/backend` - Contains the Python API, database, and scraping scripts.
* `/frontend` - Contains the user interface and frontend components.

## 🚀 How to Run Locally

### 1. Backend Setup
Open a terminal and navigate to the backend directory:

`cd backend`
`python -m venv venv`
`source venv/bin/activate`
`pip install -r requirements.txt`
`python main.py`

### 2. Frontend Setup
Open a second, separate terminal and navigate to the frontend directory:

`cd frontend`
`npm install`
`npm start`

## 📝 Features
* Scrapes up-to-date course information.
* Interactive UI for building a class schedule.
* Local database storage for fast data retrieval.
