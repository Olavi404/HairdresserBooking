# Deployment Guide — Hairdresser Booking on Render

Deploy your hairdresser booking app to Render.com in 10 minutes.

## What is Render?

Render is a cloud hosting platform:
- Free tier: 1 web service, automatic HTTPS, auto-deploys from GitHub.
- Paid: from ~$7/month for more features.
- No credit card required for free tier (but limited resource hours).

## Prerequisites

- GitHub account (repo already at https://github.com/Olavi404/HairdresserBooking)
- Render account (free signup at render.com)
- Domain `hairdresser.it.com` registered

## Deployment Steps

### 1. Sign Up for Render

1. Go to [render.com](https://render.com)
2. Click **Sign up** and choose **Sign up with GitHub**
3. Authorize Render to access your GitHub repos
4. Complete onboarding

### 2. Create a New Web Service

1. In Render dashboard, click **+ New**
2. Select **Web Service**
3. Select repository: **HairdresserBooking** (or search and click "Connect")
4. Configure the service:
   - **Name**: `hairdresser-booking`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python migrate.py`
   - **Start Command**: `gunicorn -w 3 -b 0.0.0.0:10000 app:app`
   - **Plan**: Free (or Starter if you want better uptime)

5. Click **Create Web Service**

Render will start deploying. Wait 2–3 minutes for the first build to complete.

### 3. Deploy Verification

Once deployment completes:
- You'll see a URL like `hairdresser-booking-abc123.onrender.com`
- Visit that URL to verify the app is running
- Navigate to `/admin` to test the admin panel

### 4. Connect Custom Domain

1. In Render dashboard, go to your service → **Settings**
2. Under **Custom Domains**, click **Add Custom Domain**
3. Enter `hairdresser.it.com`
4. Render will show DNS instructions:
   - Add a **CNAME record**:
     - Name: `hairdresser.it.com`
     - Value: `<your-render-service>.onrender.com`
   - (Optional) Add another CNAME for `www.hairdresser.it.com` pointing to the same value

5. Copy the provided DNS records

### 5. Point Your Domain (DNS)

1. Log into your domain registrar (e.g., namecheap.com, godaddy.com)
2. Find DNS settings
3. Create or edit the following DNS records:
   - **CNAME record**:
     - Hostname: `hairdresser.it.com` (or `@` for root)
     - Value: `<your-render-service>.onrender.com`
   - (Optional) **CNAME** for `www`:
     - Hostname: `www`
     - Value: `<your-render-service>.onrender.com`
4. Save changes
5. Wait 5–15 minutes for DNS to propagate

### 6. Verify HTTPS & Access the App

- HTTPS is automatically enabled by Render
- Once DNS propagates (5–15 min), open **https://hairdresser.it.com**
- Admin panel: **https://hairdresser.it.com/admin**

## Auto-Deployment

The app will automatically redeploy whenever you push to GitHub:
```bash
cd /path/to/hairdresserbooking
git add .
git commit -m "Update feature"
git push origin master
```

Render will detect the push and start a new build/deployment automatically.

## Monitoring & Logs

In Render dashboard:
1. Go to your service
2. Click **Logs** tab to view real-time logs
3. Click **Events** to see deployment history

## Updating the App

1. Make changes locally:
   ```bash
   git add .
   git commit -m "Your change"
   ```

2. Push to GitHub:
   ```bash
   git push origin master
   ```

3. Render auto-deploys (check **Events** in dashboard)

## Environment Variables (if needed)

In Render dashboard → Service → Environment:
- Add any env vars (e.g., secret keys, API tokens)
- Common for this app: none required (uses SQLite by default)

## Database Persistence

**⚠️ Important**: SQLite on Render is **not persistent** (resets on redeployment).  
For production, use a managed database:
1. Go to Render dashboard → **PostgreSQL** (or MySQL)
2. Create a database and get the connection string
3. Update `app.py` to use PostgreSQL instead of SQLite

For now (development), SQLite works fine and data persists between normal restarts.

## Troubleshooting

**Deployment failed?**
- Check **Logs** tab for error messages
- Verify `Procfile` or `render.yaml` is correct
- Ensure `requirements.txt` includes all dependencies

**Domain not resolving?**
- Wait 10–15 minutes for DNS to propagate
- Verify CNAME records in your registrar
- Use `dig hairdresser.it.com` to check DNS

**502 Bad Gateway?**
- Check app logs in Render dashboard
- Restart the service: Render dashboard → **Redeploy**

**App crashes on start?**
- Check logs: **Logs** tab
- Verify database migration: `python migrate.py` in build command

## Cleanup/Deletion

To stop the app (no charge):
1. Render dashboard → Select service
2. Settings → **Delete Service**

## Support

- Render docs: https://render.com/docs
- GitHub issues: https://github.com/Olavi404/HairdresserBooking/issues
- Email: admin@hairdresser.it.com

---

**Deployed on**: February 13, 2026  
**Domain**: hairdresser.it.com  
**Platform**: Render.com
