# 🎙️ AI Speech Coach

An AI-powered speech analysis tool to help you improve your communication skills.

---

## 🚀 Getting Started

Follow the steps below to run the project locally.

### Step 1: Navigate to the Backend Directory

```bash
cd backend
```

### Step 2: Create a Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

> **Note:** On Mac/Linux, use `source venv/bin/activate` instead.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables

Create a `.env` file inside the `backend/` directory and add your API keys:

```
API_KEY=your_value_here
```

### Step 5: Run the Flask App

```bash
python app.py
```

The app will be running at `http://localhost:5000`

---

## 📁 Project Structure

```
AI-Speech-Coach/
├── backend/
│   ├── app.py
│   ├── auth.py
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── systemprompt.py
│   ├── Procfile
│   └── requirements.txt
├── frontend/
│   ├── static/
│   └── templates/
├── .gitignore
├── render.yaml
└── README.md
```

---

## ⚙️ Deployment

This project is deployed on [Render](https://render.com). Environment variables are configured directly in the Render dashboard and are **not** stored in the repository.