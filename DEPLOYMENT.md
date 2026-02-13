# Deployment Guide — Hairdresser Booking

This guide walks you through deploying the app to a VPS with your domain `hairdresser.it.com` using Nginx + Gunicorn + Certbot (Let's Encrypt).

## Prerequisites

- **VPS**: Ubuntu 22.04 or later with SSH access (DigitalOcean droplet, Linode, Vultr, etc.).
- **Domain**: `hairdresser.it.com` is registered and you control the DNS records.
- **SSH Access**: Can ssh into the server as root or a sudo user.

## Deployment Steps

### 1. DNS Setup

Point your domain to the VPS IP address:
- Log into your domain registrar (e.g., namecheap.com, godaddy.com).
- Create/edit an **A record** for `hairdresser.it.com` → `<VPS_IP>`.
- (Optional) Create a **CNAME record** for `www.hairdresser.it.com` → `hairdresser.it.com`.
- Wait 5–15 minutes for DNS to propagate.

### 2. SSH into VPS

```bash
ssh root@<VPS_IP>
# or
ssh ubuntu@<VPS_IP>
```

### 3. Run Deployment Script

Download and run the automated deployment script:

```bash
cd /tmp
curl -O https://raw.githubusercontent.com/Olavi404/HairdresserBooking/master/deploy.sh
chmod +x deploy.sh
./deploy.sh
```

The script will:
- Update system packages.
- Install Python, Nginx, Certbot.
- Create a non-root `webuser` for running the app.
- Clone the GitHub repo.
- Set up a Python virtualenv and install dependencies.
- Create the SQLite database.
- Install and enable a systemd service (`hairdresser.service`) to auto-start the app.
- Configure Nginx as a reverse proxy.
- Request and install an HTTPS certificate from Let's Encrypt.

### 4. Verify Deployment

Once the script completes:

```bash
# Check if the app service is running
sudo systemctl status hairdresser

# View living logs
sudo journalctl -u hairdresser -f

# Test Nginx
sudo nginx -t

# Restart if needed
sudo systemctl restart hairdresser nginx
```

### 5. Access the App

- **Public site**: https://hairdresser.it.com
- **Admin panel**: https://hairdresser.it.com/admin
- **API endpoints**:
  - `GET /api/stylists` — list stylists
  - `GET /api/slots?stylist_id=1` — available slots
  - `POST /api/book` — create booking
  - `DELETE /api/admin/bookings/<id>` — delete booking (admin)

## Manual Deployment (if script fails)

### 3a. Update system & install dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-dev build-essential git nginx certbot python3-certbot-nginx
```

### 3b. Create app user

```bash
sudo adduser --disabled-password --gecos "" webuser
sudo usermod -aG sudo webuser
```

### 3c. Clone & set up app

```bash
sudo -u webuser bash -c "
  cd /home/webuser
  git clone https://github.com/Olavi404/HairdresserBooking.git
  cd HairdresserBooking
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -r requirements.txt
  python migrate.py
"
```

### 3d. Install systemd service

```bash
sudo cp /home/webuser/HairdresserBooking/hairdresser.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hairdresser.service
sudo systemctl start hairdresser.service
```

### 3e. Configure Nginx

```bash
sudo cp /home/webuser/HairdresserBooking/hairdresser.nginx /etc/nginx/sites-available/hairdresser
sudo ln -sf /etc/nginx/sites-available/hairdresser /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3f. Set up HTTPS

```bash
sudo certbot --nginx -d hairdresser.it.com -d www.hairdresser.it.com
# Follow prompts; choose to redirect HTTP → HTTPS
```

## Monitoring & Logs

```bash
# Service status
sudo systemctl status hairdresser

# Real-time logs
sudo journalctl -u hairdresser -f

# Last 50 lines
sudo journalctl -u hairdresser -n 50

# Nginx access/error logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Common Tasks

### Restart the app
```bash
sudo systemctl restart hairdresser
```

### Stop the app
```bash
sudo systemctl stop hairdresser
```

### Update code from GitHub
```bash
cd /home/webuser/HairdresserBooking
sudo -u webuser git pull origin master
sudo systemctl restart hairdresser
```

### Reset the database
```bash
cd /home/webuser/HairdresserBooking
sudo -u webuser python reset_db.py
sudo systemctl restart hairdresser
```

### Renew HTTPS certificate (auto with certbot)
```bash
sudo certbot renew
```

## Troubleshooting

**App not starting?**
```bash
sudo systemctl status hairdresser
sudo journalctl -u hairdresser -n 20
```

**Nginx 502 Bad Gateway?**
- Check app socket: `sudo ls -la /run/hairdresser.sock`
- Restart app: `sudo systemctl restart hairdresser`
- Check Nginx logs: `sudo tail /var/log/nginx/error.log`

**DNS not resolving?**
- Wait 10–15 minutes for DNS to propagate.
- Verify A record in registrar: `dig hairdresser.it.com`

**HTTPS not working?**
- Check Certbot status: `sudo certbot certificates`
- Verify domain in Nginx config: `sudo cat /etc/nginx/sites-available/hairdresser`
- Restart Nginx: `sudo systemctl restart nginx`

## Support

For issues, check the app logs or the GitHub repo: https://github.com/Olavi404/HairdresserBooking

---

Deployed on: [today's date]  
Domain: hairdresser.it.com
