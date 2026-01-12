
# 🗓️ AI Workforce Scheduler

**Background:** I was recently tasked with managing the monthly shift schedule at my workplace. Instead of sticking to Excel spreadsheets and manual calculations, I decided to take it a step further. I engineered this full-stack automated solution to handle constraints, ensure fairness, and integrate local AI for natural language interactions—turning a tedious manual task into an optimized, intelligent workflow.

And so  was born:

A smart, automated workforce scheduling system powered by **Google OR-Tools** and **Local AI (Ollama)**.

This system automatically generates monthly work schedules while respecting strict rules (Shifts, Shabbat, Holidays) and allows you to use **Natural Language** (English or Hebrew) to tell the AI about unavailability (e.g., *"Shaked is sick on the 12th"*).

---

## 🚀 Features

- **Smart Scheduling Engine**  
  Uses constraint programming to guarantee fairness and coverage.

- **AI Assistant**  
  Talk to the scheduler in plain English/Hebrew to set constraints (powered by Llama 3 / Gemma).

- **Modern Dashboard**  
  A clean user interface to view schedules, statistics, and manage settings.

- **REST API**  
  Full backend service ready for production integration.

- **Rules Handled**
  - Morning / Night shifts
  - Max shifts per month
  - Shabbat quotas & strict definitions
  - **Minimum Rest:** No Morning shift immediately after a Night shift

---

## 📂 Project Structure

```text
/workforce_scheduler
├── main.py                 # Backend API (The Brain)
├── core.py                 # Math & Logic Engine (OR-Tools)
├── models.py               # Data Structures
├── requirements.txt        # List of libraries to install
│
├── ui/
│   └── app.py              # User Interface (Streamlit)
│
└── agent/
    ├── constraint_agent.py # AI Translator (Talks to Ollama)
    └── api_client.py       # API Helper
````

---

## 🛠️ Simple Setup Guide

### 1. Install Python Libraries

Open your terminal (Command Prompt / PowerShell / PyCharm Terminal) in the project folder and run:

```bash
pip install fastapi uvicorn ortools streamlit requests pandas ollama
```

---

### 2. Set Up the AI (Ollama)

We use **Ollama** to run the AI locally on your computer (free & private).

1. **Download & Install**
   Go to [https://ollama.com](https://ollama.com) and install it.

2. **Start the Server**
   Open the **Ollama** app on your computer (it runs in the system tray).

3. **Download the Model**

```bash
ollama pull gemma3:27b
```

> 💡 If you use a different model (e.g. `llama3`), update `MODEL_NAME` in
> `agent/constraint_agent.py`.

---

## ▶️ How to Run the Project

You need **two terminal windows** running simultaneously.

---

### Step 1: Start the Backend (The Engine)

In the **first terminal**, run:

```bash
uvicorn main:app --reload --port 8000
```

You should see:

```
Uvicorn running on http://127.0.0.1:8000
```

---

### Step 2: Start the UI (The Dashboard)

In the **second terminal**, run:

```bash
streamlit run ui/app.py
```

Your browser will automatically open the dashboard.

---

## 🤖 How to Use the System

### 1. Configure Calendar

* Select **Year**
* Select **Month**

---

### 2. Use the AI Constraint Assistant

In the **AI Constraint Assistant** box, type freely in English or Hebrew.

**Examples:**

* `Lior cannot work on the 5th and 10th`
* `Shaked cannot work Sunday mornings`
* `שקד לא יכול לעבוד ראשון בוקר כל החודש`

Click **✨ Parse & Add**
The AI will convert your text into structured scheduling constraints.

---

### 3. Generate the Schedule

Click **🚀 Generate Final Schedule**

The system will compute the optimal schedule based on all constraints.

---

### 4. View Results

* **Daily Schedule** – Full monthly table
* **Statistics** – Shift counts per employee
* **Raw JSON** – Full API response for debugging or integration

---

## ❓ Troubleshooting

### Ollama server not responding

**Cause:** Ollama is not running.
**Fix:** Open the Ollama app from the Start Menu and ensure it’s active.

---

### ConnectionRefusedError / Cannot connect to API

**Cause:** Backend is not running.
**Fix:** Make sure you started the backend with:

```bash
uvicorn main:app --reload --port 8000
```

---

### Solver Failed / Status: INFEASIBLE

**Cause:** The constraints are impossible (e.g., everyone unavailable on the same day).
**Fix:** Remove or relax some constraints and try again.

---

## 🎉 Enjoy!

You now have a fully functional **AI-powered workforce scheduler** with:

* A strong optimization engine
* A clean API
* A visual dashboard
* A natural-language AI assistant

Enjoy building on it 🚀

```

---
