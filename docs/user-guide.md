# AssetGuard AI — User Guide

This guide covers how to manage and use the AssetGuard AI system. It is intended for handover to the client and is split into two sections: the **Admin Flow** (IT administrator tasks) and the **User Flow** (day-to-day use by engineers and contractors).

---

## Admin Flow

### 1. Create the First Superuser

Before anyone can log in, you need to create the initial admin account via the command line.

```bash
cd backend
source .venv/bin/activate
python manage.py createsuperuser
```

You will be prompted to enter a username, email address, and password. **Use the admin's email address as the username** — this keeps login credentials consistent across the system.

### 2. Access the Django Admin Panel

Once the server is running, open a browser and go to:

```
http://127.0.0.1:8000/admin/
```

Log in with the superuser credentials you just created.

### 3. Add New Users

All users (engineers, contractors, asset managers) are created in Django Admin.

1. In the admin panel, go to **Users** → **Add User**
2. Set **Username** to the user's email address
3. Set a password and click **Save and continue editing**
4. On the next page, set **Email** to the same email address
5. Click **Save**

> Users cannot change their own passwords. The admin is responsible for setting and distributing credentials directly. The system uses email addresses as usernames throughout — always set both fields to the same email to avoid login issues.

### 4. Manage Assets and Load Limits (CRUD)

All structural data is managed through Django Admin:

| Section | What to manage |
|---|---|
| **Assets** | Add, edit, or remove structures (bridges, piers, etc.) |
| **Locations** | Manage the sites/campuses that assets belong to |
| **Load Capacities** | Set or update the design limits for each asset |

Navigate to the relevant section in the left sidebar, then use the standard Add / Change / Delete controls.

### 5. Upload Engineering Drawings (Admin Portal)

The Admin Portal allows you to upload a PDF or image of an engineering drawing and use AI to automatically extract structural load limits, then save them to the database.

Go to:

```
http://127.0.0.1:8000/demo/
```

Log in with your admin credentials, then follow these steps:

**Step 1 — Upload a drawing**

Click the upload zone (or drag and drop) to select a PDF, JPG, or PNG file of the engineering drawing.

**Step 2 — Select an AI model**

Choose which model to use for extraction:
- **Claude Haiku (Anthropic)** — requires `ANTHROPIC_API_KEY` in `.env`
- **Gemini 1.5 Flash (Google)** — requires `GOOGLE_API_KEY` in `.env`

Either model works; use whichever API key you have available.

**Step 3 — Extract and review**

- Click **Extract Design Limits** to preview the extracted values without saving
- Review the results table (capacity type, value, unit)
- If the data looks correct, click **Extract & Save to Database** to persist it

> Always preview before saving. If the extracted values look wrong, try the other AI model or check that the drawing is legible.

---

## User Flow

Users access the system through the frontend web app. Make sure the backend server and frontend dev server are both running (see [README](../README.md)).

Frontend URL:
```
http://localhost:5173
```

### 1. Log In

Enter your **email address** as the username and your password, then click **Login (Admin)**.

> User accounts are created by the IT administrator as described above. Contact your admin if you do not have credentials.

### 2. Asset Dashboard

After logging in you will see the Asset Dashboard, which has two sections:

- **Select Asset for Load Request** — a searchable table of all available structures. Use the search bar to filter by asset name or ID.
- **Your Recent Assessments** — a history of your own previous compliance checks, showing the date, asset, equipment, and Pass/Fail status.

### 3. Submit a Compliance Check

1. Find the asset you want to check in the table and click **Select & Request**
2. On the Load Request Entry form, fill in:
   - **Equipment Type** — select from the dropdown (e.g. Scissor Lift, Excavator, Crane)
   - **Load weight** — enter the weight of the equipment you plan to place on the structure
3. Submit the form

### 4. View the Result

A result modal will appear immediately:

- **PASSED** — the requested load is within the asset's design limits. You may proceed.
- **FAILED** — the requested load exceeds structural limits. The modal shows the requested value versus the maximum allowable load.

> If the check fails, an automated alert email is sent to the asset manager for review. No manual action is required.
