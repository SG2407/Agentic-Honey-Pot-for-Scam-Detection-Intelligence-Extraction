# Deploying AI-Powered Honeypot API for Hackathon

## 🎯 Recommended: Deploy to Render (Free + Reliable)

### Why Render?
- ✅ **Free tier**: 750 hours/month (enough for hackathon)
- ✅ **Auto-deploy**: Push to GitHub = automatic deployment
- ✅ **HTTPS included**: Secure API endpoint by default
- ✅ **No credit card**: Start immediately
- ✅ **Environment variables**: Easy to manage secrets
- ✅ **Reliable**: Good uptime for hackathons

### Step-by-Step Deployment

#### 1. Prepare Your Repository
```bash
# Make sure all files are committed
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

#### 2. Sign Up for Render
1. Go to: https://render.com
2. Sign up with GitHub account
3. Authorize Render to access your repositories

#### 3. Create New Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository: `Delhi_Hackathon`
3. Configure:
   - **Name**: `honeypot-api` (or your choice)
   - **Region**: Singapore / Oregon (choose closest to India)
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

#### 4. Add Environment Variables
In Render dashboard → Environment:
```
GROQ_API_KEY=your_actual_groq_api_key_here
API_KEY=team_recursives
ENVIRONMENT=production
GROQ_MODEL=llama-3.3-70b-versatile
MAX_CONVERSATION_TURNS=15
```

⚠️ **IMPORTANT**: Add your real Groq API key!

#### 5. Deploy
- Click **"Create Web Service"**
- Wait 2-3 minutes for deployment
- You'll get a URL like: `https://honeypot-api.onrender.com`

#### 6. Test Your Deployment
```bash
# Test health endpoint
curl https://your-app-name.onrender.com/health

# Test honeypot endpoint (replace YOUR_URL)
curl -X POST https://your-app-name.onrender.com/honeypot \
  -H "Content-Type: application/json" \
  -H "x-api-key: team_recursives" \
  -d '{
    "sessionId": "test-123",
    "message": {
      "sender": "scammer",
      "text": "URGENT! Your bank account will be blocked.",
      "timestamp": "2026-02-01T12:00:00Z"
    },
    "conversationHistory": [],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'
```

#### 7. Share with Hackathon Officials
Your API endpoints:
```
Base URL: https://your-app-name.onrender.com
Health Check: GET /health
Honeypot API: POST /honeypot
API Docs: GET /docs (if needed)
```

**API Key for officials**: `team_recursives`

---

## 🔄 Making Changes After Deployment

### Auto-Deploy on Git Push
```bash
# 1. Make your changes locally
# 2. Test locally
python -m uvicorn app.main:app --reload

# 3. Commit and push
git add .
git commit -m "Update scam detection logic"
git push origin main

# 4. Render automatically redeploys (takes ~2 minutes)
```

### Manual Redeploy
- Go to Render dashboard
- Click **"Manual Deploy"** → Deploy latest commit

---

## ⚠️ Important Notes for Free Tier

### Cold Starts
- Free tier **spins down after 15 minutes of inactivity**
- First request after sleep takes 30-60 seconds to wake up
- Subsequent requests are fast

### Keep It Awake (Optional)
Use a free uptime monitor to ping every 10 minutes:

**Option A: UptimeRobot** (https://uptimerobot.com)
- Create free account
- Add monitor: `https://your-app.onrender.com/health`
- Set interval: 5 minutes

**Option B: Cron-job.org** (https://cron-job.org)
- Create free account
- Add job to hit your `/health` endpoint every 10 minutes

---

## 🚀 Alternative: Deploy to Railway

### Why Railway?
- ✅ $5 free credit/month
- ✅ **No sleep/spin-down** (always-on)
- ✅ Faster than Render
- ✅ Great for hackathons

### Quick Setup
1. Go to: https://railway.app
2. Sign up with GitHub
3. **"New Project"** → **"Deploy from GitHub repo"**
4. Select your repository
5. Add environment variables (same as above)
6. Railway auto-detects Python and deploys
7. Get your URL: `https://your-app.railway.app`

**Cost**: ~$3-4 for entire hackathon duration (free $5 credit covers it)

---

## 🌐 Alternative: Deploy to Fly.io

### Why Fly.io?
- ✅ Free tier with 3 VMs
- ✅ Always-on (no cold starts)
- ✅ Good performance

### Setup
```bash
# 1. Install Fly CLI
curl -L https://fly.io/install.sh | sh

# 2. Login
fly auth login

# 3. Launch app
fly launch

# 4. Set secrets
fly secrets set GROQ_API_KEY="your_key_here"
fly secrets set API_KEY="team_recursives"

# 5. Deploy
fly deploy

# 6. Get URL
fly open
```

---

## 📊 Comparison

| Platform | Free Tier | Cold Start | Always-On | Ease | Credit Card |
|----------|-----------|------------|-----------|------|-------------|
| **Render** | 750 hrs/mo | 30-60s | No | ⭐⭐⭐⭐⭐ | No |
| **Railway** | $5 credit | No | Yes | ⭐⭐⭐⭐⭐ | No |
| **Fly.io** | 3 VMs | No | Yes | ⭐⭐⭐⭐ | Yes |
| **Heroku** | Removed free tier | N/A | N/A | N/A | N/A |

---

## 🎯 Recommendation for Your Hackathon

### Best Choice: **Render + UptimeRobot**
1. Deploy to Render (free, easy)
2. Set up UptimeRobot to keep it awake
3. Share API URL with officials
4. Make changes by pushing to GitHub

### Alternative: **Railway** (if you need always-on)
- Use if you expect constant testing
- No cold start issues
- $5 free credit easily covers hackathon

---

## 📝 Final Checklist

Before sharing with officials:

- [ ] Deployed to Render/Railway
- [ ] Environment variables set (especially GROQ_API_KEY)
- [ ] Health endpoint works: `GET /health`
- [ ] Honeypot endpoint works: `POST /honeypot`
- [ ] API key documented: `team_recursives`
- [ ] Test with scam message (verify AI agent activates)
- [ ] Test with legitimate message (verify simple acknowledgment)
- [ ] Set up uptime monitor (if using Render)
- [ ] Share API documentation with officials

---

## 🔗 Your Deployed API URLs

After deployment, update this:

```
🌐 Production API Base URL: https://your-app-name.onrender.com

📍 Endpoints:
  - Health Check: GET /health
  - Honeypot API: POST /honeypot
  - API Docs: GET /docs

🔑 API Key: team_recursives

📊 Status: https://your-app-name.onrender.com/health
```

---

## 💡 Pro Tips

1. **Test before sharing**: Run your test scripts against deployed URL
2. **Monitor logs**: Check Render/Railway dashboard for errors
3. **Have backup**: Deploy to 2 platforms (Render + Railway) for redundancy
4. **Documentation**: Share API docs link with officials
5. **Response time**: First call might be slow (cold start), but subsequent calls are fast

---

## 🆘 Troubleshooting

### Deployment Failed
- Check logs in Render dashboard
- Verify `requirements.txt` is complete
- Ensure `uvicorn` is in requirements

### API Returns 500 Error
- Check environment variables are set
- Verify GROQ_API_KEY is correct
- Check logs for Python errors

### Slow Response
- Normal for first request after sleep (Render free tier)
- Set up uptime monitor to keep warm
- Or upgrade to Railway (no cold starts)

---

Good luck with your hackathon! 🚀
