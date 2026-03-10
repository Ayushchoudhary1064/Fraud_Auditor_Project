# Deloitte Graduate Hiring Assessment – AI/ML

## Candidate Information

* **Full Name:** Ayush Choudhary
* **Email:** [choudharyayush344@gmail.com](mailto:choudharyayush344@gmail.com)
* **College:** Samskruti College of Engineering & Technology
* **Skill Track:** AI & Machine Learning

---

# Project: Fraud Auditor – Collusive Fraud Detection System

**Fraud Auditor** is an end-to-end visual analytics system designed to detect collusive fraud in health insurance claims using **machine learning and graph network analysis**.

The system identifies suspicious relationships between patients and healthcare providers by constructing **co-visit networks** and applying **community detection algorithms** to highlight potential fraud rings.

This type of system can help insurance companies:

* Detect coordinated fraud rings
* Reduce financial losses
* Improve claim auditing efficiency

---

# Key Technical Features

## 1. Network Analysis

The system constructs a **co-visit graph** using `NetworkX`, where:

* **Nodes:** Patients and Providers
* **Edges:** Shared claim interactions

This allows detection of hidden relationships between entities.

---

## 2. Community Detection

A **weighted community detection algorithm** is applied to identify **dense clusters** within the network that may indicate coordinated fraud behavior.

---

## 3. Machine Learning Fraud Scoring

A fraud prediction model built using `Scikit-learn` evaluates claim patterns and assigns **fraud probability scores** based on claim features such as:

* Claim amount
* Number of visits
* Provider relationships

---

## 4. Interactive Analytics Dashboard

The system includes a **Django-based web dashboard** that allows auditors to:

* Submit and review claims
* Run fraud detection models
* Visualize fraud networks
* Inspect suspicious communities

---

# Technology Stack

## Backend

* Python
* Django

## Machine Learning

* Scikit-learn
* Pandas
* NumPy

## Graph Analytics

* NetworkX

## Visualization

* Matplotlib

---

# Project Architecture

```
User Interface (Django Templates)
        ↓
Django Backend (Views & Controllers)
        ↓
Fraud Detection Engine
   • Machine Learning Model (Scikit-learn)
   • Network Analysis (NetworkX)
        ↓
Database (SQLite)
```

---

# How Fraud Detection Works

1. Claims data is collected from users.
2. A **co-visit network** is generated connecting patients and providers.
3. **Graph community detection** identifies suspicious clusters.
4. The **machine learning model** evaluates claims for fraud risk.
5. Results are visualized through the **admin dashboard**.

---

# Setup & Running the Project

### Clone the repository

```bash
git clone https://github.com/Ayushchoudhary1064/Fraud_Auditor_Project.git
cd Fraud_Auditor_Project
```

### Create virtual environment

```bash
python -m venv fraud-env
```

### Activate virtual environment (Windows)

```bash
fraud-env\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the server

```bash
python manage.py runserver
```

### Open in browser

```
http://127.0.0.1:8000
```

---

# Future Improvements

* Graph neural networks for fraud detection
* Real-time claim monitoring
* Advanced fraud visualization tools
