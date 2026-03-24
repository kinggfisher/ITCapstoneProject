# ITCapstoneProject
Group 12 IT Captstone Project
# AssetGuard AI

AssetGuard AI is a web portal that helps organisations check whether a planned equipment or machinery load is safe to place on a structure.

Engineers, contractors, and asset managers can log in, select an asset, enter a load, and get a clear answer — pass or fail — based on the structure's design limits. If a load exceeds what's safe, the system automatically sends an alert email to the relevant people.

---

## What it does

1. log in and select a structure or asset
2. enter the load you're planning to place on it
3. system checks it against the asset's design limits
4. get a clear pass or fail result, with an explanation
5. If it fails, an alert is automatically sent to the team

---
## Team
| Name (Surname, First Name) | Student ID |
| :--- | :--- |
| **Gowda**, Dhanush | 24245807 |
| **Han**, Fei | 24495786 |
| **Luo**, Jingwei | 23875736 |
| **Sun**, Yuxin | 21900579 |
| **Wang**, Xingyue | 24090791 |
| **Yang**, Kuan | 22595879 |

---

## Architecture Overview

- **Frontend (React):** user login, asset selection, load input, results, history
- **Backend (Django + DRF):** REST API + compliance logic + validation + auth
- **Database (PostgreSQL / Supabase):** assets, limits, users, assessments/history
- **Admin (Django Admin):** internal data management interface

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | React |
| Backend | Django 4.x + Django REST Framework |
| Database | PostgreSQL (Supabase) |
| Local Dev DB (optional) | SQLite |
| Project tracking | GitHub Issues + GitHub Projects |
| Collaboration | Microsoft Teams + OneDrive |

---


## Getting Started (Backend)

### Prerequisites
- Python 3.10+ recommended
- pip / venv

### Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
