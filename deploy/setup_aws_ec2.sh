#!/bin/bash
# AWS EC2 Automated Deployment Setup Script for Django Backend
set -e

APP_DIR=$(pwd)
USER_NAME=$(whoami)

echo "=== Fixing dpkg if interrupted ==="
sudo dpkg --configure -a --force-confold || true

echo "=== Updating System Packages ==="
sudo apt update && sudo apt upgrade -y

echo "=== Installing Python, Pip, Nginx, Certbot ==="
sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx git

echo "=== Setting up Virtual Environment ==="
python3 -m venv venv
source venv/bin/activate

echo "=== Installing Dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Running Django Migrations & Collectstatic ==="
python manage.py migrate
python manage.py collectstatic --noinput

echo "=== Configuring Dynamic Gunicorn Service ==="
cat <<EOF | sudo tee /etc/systemd/system/gunicorn.service
[Unit]
Description=gunicorn daemon for Django Backend
After=network.target

[Service]
User=${USER_NAME}
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:${APP_DIR}/pwbackend.sock pwbackend.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

echo "=== Configuring Dynamic Nginx Site ==="
cat <<EOF | sudo tee /etc/nginx/sites-available/pwbackend
server {
    listen 80;
    server_name _;

    client_max_body_size 500M;

    location /static/ {
        alias ${APP_DIR}/staticfiles/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:${APP_DIR}/pwbackend.sock;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/pwbackend /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "=================================================="
echo "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "Your Django Backend is live on EC2!"
echo "=================================================="
