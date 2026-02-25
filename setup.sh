#!/bin/bash

# CONFIGURATION VARIABLES ################################################################
DB_NAME="proplist_db"
DB_USER="proplist_user"
DB_PASS="your_secure_db_password"


# Update the system ######################################################################
sudo apt update

# Install and setup PostgreSQL ###########################################################
sudo apt install postgresql postgresql-contrib -y

sudo bash -c 'echo "listen_addresses = '\''localhost'\''" >> /etc/postgresql/*/main/postgresql.conf'
sudo bash -c 'echo "host    ${DB_NAME}    ${DB_USER}    127.0.0.1/32         scram-sha-256" >> /etc/postgresql/*/main/pg_hba.conf'

sudo systemctl start postgresql
sudo systemctl enable postgresql

sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME};"
sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH ENCRYPTED PASSWORD '${DB_PASS}';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"

sudo -u postgres psql -d ${DB_NAME} -c "GRANT USAGE ON SCHEMA public TO ${DB_USER};"
sudo -u postgres psql -d ${DB_NAME} -c "GRANT CREATE ON SCHEMA public TO ${DB_USER};"
sudo -u postgres psql -d ${DB_NAME} -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${DB_USER};"

# Setting up the FastAPI Backend and app ##################################################
sudo apt install git python3 python3-venv -y

if [ -d "/var/www/proplist" ]; then
    sudo rm -rf /var/www/proplist
fi
sudo git clone https://github.com/jkpatelnx/property-listing-platform.git /var/www/proplist

sudo chown -R ubuntu:ubuntu /var/www/proplist
cd /var/www/proplist

python3 -m venv venv
source venv/bin/activate

cp .env.example .env
sed -i '1,2d' .env 
echo "# database" >> .env
echo "DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASS}@127.0.0.1:5432/${DB_NAME}" >> .env

pip install -r requirements.txt
python -m alembic upgrade head

python seed.py

# install nginx ##########################################################################
sudo apt install nginx -y

sudo systemctl start nginx
sudo systemctl enable nginx

sudo bash -c 'cat > /etc/nginx/sites-available/proplist << "EOF"
server {
    listen 80;
    server_name proplist.example.com; # Change this to your real domain (e.g. prop.jkpatelnx.in)

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF'

sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/proplist /etc/nginx/sites-enabled/

sudo nginx -t
sudo systemctl reload nginx

# Finally, start the app #################################################################
uvicorn main:app --host 0.0.0.0 --port 8000

