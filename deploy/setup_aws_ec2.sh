#!/bin/bash
# AWS EC2 Automated Deployment Setup Script for Django Backend
set -e

echo "=== Updating System Packages ==="
sudo apt update && sudo apt upgrade -y

echo "=== Installing Python, Pip, Nginx, Certbot ==="
sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx git

echo "=== Setting up Virtual Environment ==="
cd /home/ubuntu/clascic/django_backend
python3 -m venv venv
source venv/bin/activate

echo "=== Installing Dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Running Django Migrations & Collectstatic ==="
python manage.py migrate
python manage.py collectstatic --noinput

echo "=== Setting up Gunicorn Systemd Service ==="
sudo cp deploy/gunicorn.service /etc/systemd/system/gunicorn.service
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

echo "=== Setting up Nginx Configuration ==="
sudo cp deploy/nginx.conf /etc/nginx/sites-available/pwbackend
sudo ln -sf /etc/nginx/sites-available/pwbackend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo "=== Deployment Completed Successfully! ==="
