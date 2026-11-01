# PlacePro – Recruitment & Placement Management System

Internship project (Python track) built at **Kiran Academy**.
The database design specification and the SQL scripts in `database/` were provided by Kiran Academy.
Application code (backend and frontend) by **<Your Name>**.

## About
PlacePro manages the recruitment and placement process of candidates for a training institute or placement organization:
candidates, companies, job openings, an eligibility check, applications, interviews and feedback, offers, joining and placements,
with dashboards and management reports.

**Workflow:** Candidate Registration → Eligibility Verification → Application → Shortlisting → Interview → Feedback → Selection → Offer → Joining → Placement.

## Features
- Candidate, company and job management with search and filters
- Eligibility engine (qualification, percentage, passing year, backlogs, mandatory skills, job status, deadline)
- Duplicate application prevention and a status workflow that blocks invalid jumps
- Interview rounds, feedback, offers, joining and placement tracking
- Dashboard, 12 management reports and an activity log
- Login with roles: Admin, Recruiter, Placement Officer
- Light and Dark mode, responsive layout

## Tech stack
Python, FastAPI, mysql-connector-python, MySQL 8, MySQL Workbench, HTML, CSS, JavaScript, JWT, bcrypt.

## Project structure
```
backend/    Python API (model, dao, service, util, exception, reports, app) and a console menu
frontend/   HTML/CSS/JS pages (login, dashboard, candidates, companies, jobs, applications, interviews, placement process, reports, activity log)
database/   MySQL scripts (schema, sample data, full setup)
```

## How to run it on your computer
1. Install Python 3.10+, MySQL Server 8 and MySQL Workbench.
2. In MySQL Workbench open and run `database/rpms_full_setup.sql` (it recreates the database `rpms_db`).
3. In a terminal:
   ```
   cd backend
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   copy .env.example .env
   ```
4. Open `backend/.env` and set `DB_PASSWORD`, `FRONTEND_DIR=../frontend` and a random `JWT_SECRET`
   (create one with `python -c "import secrets;print(secrets.token_urlsafe(48))"`).
5. Set the demo user passwords: `python scripts/set_demo_passwords.py`
6. Start the app: `python run_api.py` and open http://127.0.0.1:8000

## Demo users (local use only)
| Role | Username | Password |
|---|---|---|
| Admin | admin | Placepro@123 |
| Recruiter | amit.recruiter | Placepro@123 |
| Placement Officer | neha.placement | Placepro@123 |

These passwords are created on your own computer by `set_demo_passwords.py`. Never use them on a real server.

## Screenshots
<img width="1900" height="967" alt="image" src="https://github.com/user-attachments/assets/ffcd6349-1deb-46f7-80b8-b4459a880e2c" />
<img width="1693" height="866" alt="image" src="https://github.com/user-attachments/assets/7b2f4751-522b-49e8-8f60-4088411b4d46" />



## Author
Saniya bangi 
