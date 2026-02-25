# PropList: Real Estate Listing Platform

> A backend-first property listing platform built with Python and FastAPI. This guide covers how to manually deploy the application, database, and web server. 
---

## 🛠️ Tech Stack & Architecture

- **Backend Framework:** FastAPI (Asynchronous Python)
- **Database:** PostgreSQL (via `asyncpg`)
- **ORM & Migrations:** SQLAlchemy 2.0 + Alembic
- **Templates:** Jinja2 (Server-Side Rendering)
- **Authentication:** Secure JWT (JSON Web Tokens) with Passlib (bcrypt)
- **File Uploads:** Python `python-multipart`

<img width="1439" height="1110" alt="Screenshot 2026-02-25 at 9 27 05 PM" src="https://github.com/user-attachments/assets/a94374de-ed98-4a4c-86c6-9adb03e61e7d" />


---

##  Step-by-Step Deployment Guide

Follow these exact steps to get the application running from scratch on a fresh Ubuntu server.

### Part 1: Setting up the PostgreSQL Database

We need to install the database, create a user, and grant the correct permissions so our application can store and retrieve data.

**1. Install PostgreSQL**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y
```

**2. Configure Database Access**
We need to allow connections to the database. First, edit the main configuration file:
```bash
sudo vim /etc/postgresql/*/main/postgresql.conf
```
*Find `listen_addresses` and change it to:*
`listen_addresses = '*'`

Next, edit the pg_hba.conf file to allow our user to connect securely:
```bash
sudo vim /etc/postgresql/*/main/pg_hba.conf
```
*Add this line at the bottom:*
`host    proplist_db    proplist_user    127.0.0.1/32    scram-sha-256`

Restart the database service to apply the changes:
```bash
sudo systemctl restart postgresql
sudo systemctl status postgresql
```

**3. Create the Database and User**
Log into the postgres shell to run the SQL commands:
```bash
sudo -u postgres psql
```

Run the following commands inside the psql prompt:
```sql
CREATE DATABASE proplist_db;
CREATE USER proplist_user WITH ENCRYPTED PASSWORD 'your_secure_db_password';
GRANT ALL PRIVILEGES ON DATABASE proplist_db TO proplist_user;

\c proplist_db;
GRANT USAGE ON SCHEMA public TO proplist_user;
GRANT CREATE ON SCHEMA public TO proplist_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO proplist_user;

\q
```

---

### Part 2: Setting up the FastAPI Backend

Now we will pull the code, set up the Python environment, connect to the database, and start the app.

**1. Clone the Code Repository**
First, we need to install Git and Python, then clone the project into the `/var/www/` directory.
```bash
sudo apt install git python3 python3-venv
sudo git clone https://github.com/jkpatelnx/property-listing-platform.git /var/www/proplist
```

We need to take ownership of the folder so we can edit files later without using sudo everywhere:
```bash
sudo chown -R ubuntu:ubuntu /var/www/proplist
cd /var/www/proplist
```

**2. Set up the Python Environment**
It's always best practice to use a virtual environment for Python projects so dependencies don't conflict.
```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Configure Environment Variables**
We need to tell the app how to connect to the database we just made. Copy the example file:
```bash
cp .env.example .env
vim .env
```
Update the `DATABASE_URL` line to match your credentials:
```ini
# Database
DATABASE_URL=postgresql+asyncpg://proplist_user:your_secure_db_password@localhost:5432/proplist_db
# (Leave the rest of the JWT and App settings as they are, or update for production security)
```

**4. Install Dependencies & Build the Database Tables**
Now we install all the required Python packages and use Alembic to build our database schema.
```bash
pip install -r requirements.txt
```

Before migrating, double check the alembic file has the right database URL:
```bash
vim alembic.ini
# Ensure sqlalchemy.url line matches your DATABASE_URL from the .env file
```

Run the migration:
```bash
python -m alembic upgrade head
```

**5. Seed Initial Data**
If you want to populate the database with a default Admin user and some sample properties to test with:
```bash
python seed.py
```
*(You should see an output indicating "Seed complete!" with the Admin credentials).*

**6. Test the Application Locally**
Let's spin up the app to make sure it works!
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
Open your browser and navigate to `http://<Public-IP>:8000`. You should see the site! Once verified, hit `CTRL+C` in the terminal to stop the server for now so we can set up Nginx.

---

### Part 3: Setting up the Nginx Web Server

Nginx will act as a "Reverse Proxy". It listens on the standard HTTP port (80) and passes traffic securely back to our FastAPI app running on port 8000. It's much faster and better for production.

**1. Install Nginx**
```bash
sudo apt install nginx -y
```

**2. Create the Nginx Configuration File**
We need to create a specific configuration file for our property listing app.
```bash
sudo vim /etc/nginx/sites-available/proplist
```

Paste the following configuration into the file. Be sure to change the `server_name` to your actual domain name!

```nginx
server {
    listen 80;
    server_name example.com www.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**3. Enable the Site and Restart Nginx**
We enable the new configuration by linking it, and we delete the default Nginx welcome page so it doesn't conflict.
```bash
# Enable the Configuration
sudo ln -s /etc/nginx/sites-available/proplist /etc/nginx/sites-enabled/

# Remove the Default Nginx Page
sudo rm /etc/nginx/sites-enabled/default

# Check Syntax to make sure we didn't make a typo
sudo nginx -t

# Restart Nginx to apply changes
sudo systemctl restart nginx
```

### Wrapping Up
Finally, start your Uvicorn backend server again in the background (or in a `screen`/`tmux` session, or ideally using a `systemd` service).

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

You can now access your live site on port 80!

Open your browser and navigate to `http://<Public-IP>:80`. You should see the site!
(or)
Open your browser and navigate to `http://<Public-IP>`. You should see the site!
