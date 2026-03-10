# Sitt Yan Student Management System

A Django-based student management platform made by Sitt Yan.

## Overview

This project helps school administrators, staff, and students manage daily academic operations in one place.

## Core Features

### Admin users can
1. Manage staff records
2. Manage student records
3. Manage courses and subjects
4. Manage academic sessions
5. Review attendance data
6. Review and reply to feedback
7. Approve or reject leave requests
8. View dashboard summaries

### Staff users can
1. Take attendance
2. Update attendance
3. Add and update results
4. Apply for leave
5. Send feedback to the administrator
6. Review student self reports

### Student users can
1. View attendance
2. View results
3. Apply for leave
4. Send feedback
5. Submit self reports
6. Manage their account profile

## Screenshots

Screenshots for the interface are available in the `ss/` folder.

## Installation

### Requirements
1. Python 3
2. pip
3. Git

### Setup
1. Clone the repository:
```bash
git clone https://github.com/Opuio1e/cs-g12-track-elective-sitt-yan.git
cd cs-g12-track-elective-sitt-yan
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
```

Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables as needed:
```powershell
$env:MY_SECRET_KEY='replace-with-a-secure-secret-key'
```

5. Run database migrations if needed:
```bash
python manage.py migrate
```

6. Start the development server:
```bash
python manage.py runserver
```

## Default Login Credentials

### Superadmin
- Email: `admin@admin.com`
- Password: `admin`

### Staff
- Email: `staff@staff.com`
- Password: `staff`

### Student
- Email: `student@student.com`
- Password: `student`

## Project Notes

- Local development uses SQLite by default.
- `DATABASE_URL` is optional and only used when explicitly configured.
- The interface styling and project branding in this repository are made by Sitt Yan.

## Maintainer

Made by Sitt Yan.
