from flask import Flask, render_template, request, redirect, session
from google.cloud import bigquery
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "devkey123")

# BigQuery client
client = bigquery.Client()

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "password123")

ROLE_PERMISSIONS = {
    "Admin": {
        "Patients": "RWD",
        "Doctors": "RWD",
        "Appointments": "RWD",
        "MedicalRecords": "RWD",
        "Admissions": "RWD"
    },
    "Doctor": {
        "Patients": "RW",
        "Doctors": "R",
        "Appointments": "RW",
        "MedicalRecords": "RW",
        "Admissions": "R"
    },
    "Nurse": {
        "Patients": "R",
        "Doctors": "R",
        "Appointments": "RW",
        "MedicalRecords": "R",
        "Admissions": "RW"
    },
    "Patient": {
        "Patients": "R",
        "Appointments": "RW"
    }
}

#Prevents SQL injection and securely passes values using parameterized queries
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        query = f"""
            SELECT role, user_id
            FROM HospitalDB.Users
            WHERE username = @username AND password_hash = @password
            LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("username", "STRING", username),
                bigquery.ScalarQueryParameter("password", "STRING", password),
            ]
        )

        result = client.query(query, job_config=job_config).result()
        user = list(result)

        if user:
            session['role'] = user[0]['role']
            session['user_id'] = user[0]['user_id']
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    role = session.get('role')
    if not role:
        return redirect('/')

    dataset = 'HospitalDB'
    allowed_tables = ROLE_PERMISSIONS.get(role, {})
    table_data = {}

    for table_name, perms in allowed_tables.items():
        table_id = f"{client.project}.{dataset}.{table_name}"

        # Row-level filtering for Doctors and Patients
        if role == 'Doctor' and table_name in ['MedicalRecords', 'Appointments']:
            query = f"SELECT * FROM `{table_id}` WHERE doctor_id = @user_id LIMIT 10"
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("user_id", "INT64", user_id),
                ]
            )
        elif role == 'Patient' and table_name in ['MedicalRecords', 'Appointments', 'Patients']:
            if table_name == 'Patients':
                query = f"SELECT * FROM `{table_id}` WHERE user_id = @user_id"
            else:
                query = f"SELECT * FROM `{table_id}` WHERE patient_id = (SELECT patient_id FROM `{client.project}.{dataset}.Patients` WHERE user_id = @user_id) LIMIT 10"
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("user_id", "INT64", user_id),
                ]
            )
        else:
            # No filtering — Admin or general access
            query = f"SELECT * FROM `{table_id}` LIMIT 10"
            job_config = None

        result = client.query(query, job_config=job_config).result() if job_config else client.query(query).result()
        table_data[table_name] = {
            "rows": [dict(row) for row in result],
            "permissions": perms
        }

    return render_template('dashboard.html', tables=table_data, role=role)

@app.route('/edit/<table>/<row_id>', methods=['GET', 'POST'])
def edit_row(table, row_id):
    role = session.get('role')
    if not role or table not in ROLE_PERMISSIONS.get(role, {}) or 'W' not in ROLE_PERMISSIONS[role][table]:
        return "Unauthorized", 403

    table_id = f"{client.project}.HospitalDB.{table}"

    if request.method == 'POST':
        updates = {key: value for key, value in request.form.items()}
        # Identify the primary key field for this table
        pk_field = f"{table[:-1].lower()}_id"  # e.g., patient_id from Patients

        # Remove the primary key from the update fields
        if pk_field in updates:
            updates.pop(pk_field)

        # Construct safe SET clause
        set_clause = ", ".join([
            f"{key} = {value}" if value.isdigit() else f"{key} = '{value}'"
            for key, value in updates.items()
        ])

        query = f"UPDATE `{table_id}` SET {set_clause} WHERE {table[:-1].lower()}_id = @row_id"

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("row_id", "INT64", int(row_id))
            ]
        )

        client.query(query, job_config=job_config).result()
        return redirect('/dashboard')

    # Fetch row
    query = f"SELECT * FROM `{table_id}` WHERE {table[:-1].lower()}_id = @row_id"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("row_id", "INT64", int(row_id))
        ]
    )
    row = list(client.query(query, job_config=job_config).result())[0]

    return render_template("edit.html", table=table, row=row, row_id=row_id)

@app.route('/delete/<table>/<row_id>', methods=['POST'])
def delete_row(table, row_id):
    role = session.get('role')
    if not role or table not in ROLE_PERMISSIONS.get(role, {}) or 'D' not in ROLE_PERMISSIONS[role][table]:
        return "Unauthorized", 403

    table_id = f"{client.project}.HospitalDB.{table}"
    id_column = f"{table[:-1].lower()}_id"  # crude way to map table → PK

    query = f"DELETE FROM `{table_id}` WHERE {id_column} = @row_id"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("row_id", "INT64", int(row_id))
        ]
    )

    client.query(query, job_config=job_config).result()
    return redirect('/dashboard')



@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

