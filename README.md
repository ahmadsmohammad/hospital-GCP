# 🏥 Hospital Management Portal

A cloud-based hospital management system built with **Flask** and **Google BigQuery**, featuring:

- ✅ Role-Based Access Control (RBAC) for Admin, Doctor, Nurse, Patient
- ✅ Login authentication using BigQuery `Users` table
- ✅ Dynamic dashboard rendering with permissions
- ✅ Edit/Delete buttons for authorized roles
- ✅ Secure connection to BigQuery via Cloud Shell or Cloud Run
- 🌐 Deployable entirely on Google Cloud


---

## 🧑‍💻 User Roles & Permissions

| Role     | Permissions by Table (Read / Write / Delete)        |
|----------|-----------------------------------------------------|
| Admin    | Full access to all tables and actions               |
| Doctor   | Can view/edit only their own records and patients   |
| Nurse    | Limited read/write access to assigned areas         |
| Patient  | Can view their own records and appointments         |

Users are stored in the `HospitalDB.Users` table in BigQuery.

---

## 🚀 Getting Started in GCP Cloud Shell

### 1. Clone the Repo

git clone https://github.com/YOUR_USERNAME/hospital-portal.git
cd hospital-portal

### 2. Set up Python Environment
pip install -r requirements.txt

### 3. Authenticate (if needed)
gcloud auth application-default login

### 4. Run the App (Cloud Shell Dev Mode)
python app.py
Then click Web Preview → Port 8080.

🔐 Sample Logins (for testing)
Username	Password	Role
admin1	test	Admin
drsmith	test	Doctor
nursejoy	test	Nurse
john_doe	test	Patient


### 🔒 Security Notes

Passwords will be hashed with bcrypt (coming soon)

RBAC and user-level filtering are enforced in both UI and queries

Supports adding logging, audit trails, and encryption in future phases


🛠️ Tech Stack
Python + Flask

Google BigQuery (cloud database)

Jinja2 templating

Cloud Shell / Cloud Run (runtime)

GitHub (code hosting)


✅ TODOs
 Add password hashing (bcrypt)

 Add user registration flow

 Add new record creation (CRUD)

 Add modals for editing

 Deploy to Cloud Run (prod)

 🧑 Author
Ahmad Mohammad
Contact: ahmadsmohammad02@gmail.com
GitHub: @ahmadsmohammad




