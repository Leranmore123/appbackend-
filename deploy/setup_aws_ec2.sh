#!/bin/bash
# AWS EC2 Automated Deployment Setup Script for Django Backend
set -e

APP_DIR=$(pwd)
USER_NAME=$(whoami)

echo "=== Fixing Directory Permissions for Nginx ==="
sudo chmod 755 $(dirname "$APP_DIR") || true
sudo chmod 755 "$APP_DIR" || true

echo "=== Fixing dpkg if interrupted ==="
sudo dpkg --configure -a --force-confold || true

echo "=== Updating Package List ==="
sudo apt update -y

echo "=== Installing Required Dependencies ==="
DEBIAN_FRONTEND=noninteractive sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx git

echo "=== Setting up Virtual Environment ==="
python3 -m venv venv
source venv/bin/activate

echo "=== Installing Python Requirements ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Running Django Migrations & Collectstatic ==="
python manage.py migrate
python manage.py collectstatic --noinput

echo "=== Configuring pwbackend Systemd Service ==="
cat <<EOF | sudo tee /etc/systemd/system/pwbackend.service
[Unit]
Description=Gunicorn daemon for PW Django Backend
After=network.target

[Service]
User=${USER_NAME}
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/venv/bin/gunicorn --access-logfile - --workers 3 --bind 127.0.0.1:8001 pwbackend.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl restart pwbackend
sudo systemctl enable pwbackend

echo "=== pwbackend Service Status & Logs ==="
sudo systemctl status pwbackend --no-pager || true
sudo journalctl -u pwbackend -n 20 --no-pager || true

echo "=== Configuring Nginx Proxy for pwbackend ==="
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
        proxy_pass http://127.0.0.1:8001;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/pwbackend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

echo "=================================================="
echo "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "Your Django Backend is live on EC2 (pwbackend.service)!"
echo "=================================================="
