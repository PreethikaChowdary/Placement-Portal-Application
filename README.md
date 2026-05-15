# Placement Portal Application

This project is a full-stack web application developed as part of the App Development Project in the BS in Data Science and Applications program at IIT Madras.

The application streamlines campus recruitment activities by providing a centralized placement management system for Admins, Companies, and Students.

---

# Problem Statement

Institutes often rely on spreadsheets, emails, or manual workflows to manage placement activities, making it difficult to:

- Manage company approvals
- Track student applications
- Prevent duplicate registrations
- Maintain placement records efficiently

This project addresses these challenges through a role-based placement portal.

---

# Features

## Admin Module
- Manage students and companies
- Approve or reject placement drives
- Blacklist users
- View placement statistics
- Edit and delete records

## Company Module
- Company registration and approval workflow
- Create and manage placement drives
- View student applications
- Update application statuses

## Student Module
- Student registration and login
- Browse approved placement drives
- Apply for jobs
- Track application status
- Upload resumes

---

# Additional Features

- Role-based authentication system
- Duplicate application prevention
- Resume upload support
- REST API endpoints
- Interactive dashboards using Chart.js
- Responsive UI with Bootstrap 5

---

# Tech Stack

## Backend
- Flask
- SQLAlchemy
- SQLite

## Frontend
- HTML
- CSS
- Bootstrap 5
- Jinja2 Templates

## Visualization
- Chart.js

---

# Database Schema

## Tables
- Admin
- Company
- Student
- PlacementDrive
- Application
- Placement

## Relationships
- One-to-Many → Company → PlacementDrive
- One-to-Many → Student → Application
- One-to-Many → PlacementDrive → Application
- One-to-One → Application → Placement

---

# API Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| /api/students | GET | Fetch all students |
| /api/students/<id> | GET | Fetch student by ID |
| /api/students | POST | Create student |
| /api/students/<id> | PUT | Update student |
| /api/students/<id> | DELETE | Delete student |
| /api/companies | GET | Fetch companies |
| /api/drives | GET | Fetch placement drives |
| /api/applications | GET | Fetch applications |
| /api/statistics | GET | Get overall statistics |

---

# Project Structure

```bash
├── app.py
├── templates/
├── static/
│   ├── css/
│   └── uploads/
├── instance/
│   └── database.db
├── README.md
└── requirements.txt
