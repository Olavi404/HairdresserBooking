#!/bin/bash
# Hairdresser Booking Deployment Guide
# Run this on your Ubuntu 22.04+ VPS as root or with sudo

set -e

DOMAIN="hairdresser.it.com"
REPO_URL="https://github.com/Olavi404/HairdresserBooking.git"
APP_USER="webuser"
APP_HOME="/home/$APP_USER/HairdresserBooking"

echo "=== Hairdresser Booking Deployment ==="
echo "Domain: $DOMAIN"
echo "User: $APP_USER"
echo "App dir: $APP_HOME"
echo ""

# Step 1: Update system
echo "[1/8] Updating system packages..."
apt update && apt upgrade -y

# Step 2: Install dependencies
echo "[2/8] Installing dependencies..."
apt install -y python3 python3-venv python3-dev build-essential git nginx certbot python3-certbot-nginx

# Step 3: Create app user
echo "[3/8] Creating app user..."
if id "$APP_USER" &>/dev/null; then
    echo "User $APP_USER already exists"
else
    adduser --disabled-password --gecos "" $APP_USER
    usermod -aG sudo $APP_USER
fi

# Step 4: Clone repository
echo "[4/8] Cloning repository..."
sudo -u $APP_USER bash -c "cd /home/$APP_USER && git clone $REPO_URL"

# Step 5: Set up virtualenv and install dependencies
echo "[5/8] Setting up Python virtualenv and installing dependencies..."
sudo -u $APP_USER bash -c "
    cd $APP_HOME
    python3 -m venv .venv
    . .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    python migrate.py
"

# Step 6: Install systemd service
echo "[6/8] Installing systemd service..."
cp $APP_HOME/hairdresser.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable hairdresser.service
systemctl start hairdresser.service

# Step 7: Configure Nginx
echo "[7/8] Configuring Nginx..."
cp $APP_HOME/hairdresser.nginx /etc/nginx/sites-available/hairdresser
ln -sf /etc/nginx/sites-available/hairdresser /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# Step 8: Set up HTTPS with Certbot
echo "[8/8] Setting up HTTPS with Let's Encrypt..."
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN || true

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. Point your DNS A record for $DOMAIN to this server's IP address"
echo "2. Check service status: sudo systemctl status hairdresser"
echo "3. View logs: sudo journalctl -u hairdresser -f"
echo "4. Access app at: https://$DOMAIN"
echo "5. Admin panel: https://$DOMAIN/admin"
echo ""
