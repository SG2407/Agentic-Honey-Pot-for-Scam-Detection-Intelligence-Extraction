# 🚀 Complete Deployment Guide

## Overview

You'll deploy **3 services** that work together:

1. **Existing Honeypot** (Already deployed ✅) - No changes
2. **UI Backend** → Render.com (New)
3. **Streamlit UI** → Streamlit Cloud (New, Free)

---

## 🎯 Step 1: Existing Honeypot (Already Done ✅)

Your existing honeypot is already running:
- **URL**: https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com
- **Status**: Keep it running as-is
- **Action**: NO CHANGES NEEDED

This service will continue to:
- Process honeypot requests
- Send callbacks to GUVI
- Work independently

---

## 🔧 Step 2: Deploy UI Backend to Render

### Option A: Using Render Dashboard (Easier)

1. **Go to Render Dashboard**: https://dashboard.render.com

2. **Create New Web Service**:
   - Click "New +" → "Web Service"

3. **Connect Your Repository**:
   - Connect your GitHub repository
   - If not connected: Click "Connect account" → Authorize GitHub

4. **Configure Service**:
   ```
   Name:              honeypot-ui-backend
   Region:            Oregon (US West)
   Branch:            main
   Root Directory:    (leave empty)
   Runtime:           Python 3
   Build Command:     pip install -r ui/requirements_ui.txt
   Start Command:     uvicorn ui.ui_backend:app --host 0.0.0.0 --port $PORT
   Plan:              Free
   ```

5. **Add Environment Variables**:
   Click "Advanced" → "Add Environment Variable"
   
   ```
   Key: HONEYPOT_API_URL
   Value: https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com
   
   Key: API_KEY
   Value: team_recursives
   
   Key: PYTHON_VERSION
   Value: 3.11.0
   ```

6. **Add Health Check**:
   ```
   Health Check Path: /health
   ```

7. **Click "Create Web Service"**

8. **Wait for Deployment** (5-10 minutes):
   - Watch the logs
   - Wait for "Your service is live 🎉"

9. **Copy Your Backend URL**:
   - Example: `https://honeypot-ui-backend-xyz.onrender.com`
   - **Save this URL** - you'll need it for Streamlit

### Option B: Using render.yaml (Advanced)

1. **Push the render.yaml file to your repo**:
   ```bash
   git add render_ui_backend.yaml
   git commit -m "Add Render config for UI backend"
   git push
   ```

2. **In Render Dashboard**:
   - Click "New +" → "Blueprint"
   - Select your repository
   - Choose `render_ui_backend.yaml`
   - Click "Apply"

---

## 🎨 Step 3: Deploy Streamlit UI to Streamlit Cloud (FREE)

### Prerequisites:
- Push your code to GitHub (if not already)
- Have a GitHub account

### Deployment Steps:

1. **Go to Streamlit Cloud**: https://share.streamlit.io

2. **Sign in with GitHub**

3. **Click "New app"**

4. **Configure App**:
   ```
   Repository:        your-github-username/Delhi_Hackathon
   Branch:            main
   Main file path:    ui/streamlit_app.py
   App URL:           (choose a custom URL or use generated)
   ```

5. **Advanced Settings** → Add Secrets:
   Click "Advanced settings" → "Secrets"
   
   Add this in the secrets box:
   ```toml
   # Replace with your actual UI backend URL from Step 2
   UI_BACKEND_URL = "https://honeypot-ui-backend-xyz.onrender.com"
   ```

6. **Click "Deploy!"**

7. **Wait for Deployment** (2-3 minutes)

8. **Your UI is Live!** 🎉
   - You'll get a URL like: `https://your-app.streamlit.app`

### Update Streamlit App to Use Environment Variable:

After deployment, update the backend URL in the code:

```python
# In ui/streamlit_app.py, change:
UI_BACKEND_URL = "http://localhost:8001"

# To:
import os
UI_BACKEND_URL = os.getenv("UI_BACKEND_URL", "http://localhost:8001")
```

Then commit and push - Streamlit will auto-redeploy.

---

## ✅ Step 4: Verify Everything Works

### Test Each Service:

1. **Test Existing Honeypot** (should still work):
   ```bash
   curl https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/health
   ```
   Expected: `{"status": "healthy", ...}`

2. **Test UI Backend**:
   ```bash
   curl https://honeypot-ui-backend-xyz.onrender.com/health
   ```
   Expected: `{"status": "healthy", "honeypot_status": "healthy", ...}`

3. **Test Streamlit UI**:
   - Open: `https://your-app.streamlit.app`
   - Enter API key: `team_recursives`
   - Click "Connect"
   - Should see "Connected" status

4. **Test Full Flow**:
   - Send a test message in UI
   - Should get agent reply
   - Intelligence should appear
   - Check logs: Your main honeypot should receive the request

---

## 🔄 Architecture After Deployment

```
┌─────────────────────────────────────────────────────┐
│  User Browser                                        │
│  https://your-app.streamlit.app                    │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  UI Backend (Render)                                 │
│  https://honeypot-ui-backend-xyz.onrender.com       │
│  • Handles chat requests                             │
│  • Stores sessions in SQLite                         │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  Main Honeypot (Render) - UNCHANGED                  │
│  https://agentic-honey-pot-for...onrender.com       │
│  • Original functionality preserved                  │
│  • Still sends callbacks to GUVI ✅                  │
└─────────────────────────────────────────────────────┘
```

---

## 💰 Cost Breakdown

| Service | Platform | Cost |
|---------|----------|------|
| Existing Honeypot | Render Free Tier | $0 ✅ |
| UI Backend | Render Free Tier | $0 ✅ |
| Streamlit UI | Streamlit Cloud | $0 ✅ |
| **TOTAL** | | **$0** 🎉 |

**Note**: Render free tier services spin down after 15 minutes of inactivity. First request after spin-down takes ~30 seconds.

---

## 🔧 Troubleshooting

### Issue: UI Backend can't connect to main honeypot
**Fix**: Check environment variable `HONEYPOT_API_URL` is correct in Render settings

### Issue: Streamlit can't connect to UI backend
**Fix**: 
1. Ensure UI backend is deployed and running
2. Check `UI_BACKEND_URL` in Streamlit secrets
3. Update `streamlit_app.py` to use environment variable

### Issue: CORS errors
**Fix**: UI backend already has CORS configured for `*` origins

### Issue: Services sleeping (Render free tier)
**Expected**: First request wakes up service (30 seconds)
**Solution**: Upgrade to paid tier ($7/month) or use keep-alive service

---

## 🎯 Quick Commands Reference

### Check Service Health:
```bash
# Main honeypot
curl https://agentic-honey-pot-for-scam-detection-iiv4.onrender.com/health

# UI backend
curl https://your-ui-backend.onrender.com/health
```

### View Render Logs:
1. Go to Render Dashboard
2. Click on service name
3. Click "Logs" tab

### Redeploy Services:
**Render**: Push to GitHub → Auto-deploys
**Streamlit**: Push to GitHub → Auto-deploys

---

## 🚀 Final Checklist

- [ ] Existing honeypot is running (already done)
- [ ] UI backend deployed to Render
- [ ] Environment variables set in Render
- [ ] UI backend health check passes
- [ ] Streamlit app deployed to Streamlit Cloud
- [ ] Secrets configured in Streamlit
- [ ] Can access Streamlit UI via browser
- [ ] Can authenticate with API key
- [ ] Can send test message and get reply
- [ ] Intelligence extraction works
- [ ] Main honeypot still receives requests

---

## 📚 Additional Resources

- **Render Docs**: https://render.com/docs
- **Streamlit Cloud Docs**: https://docs.streamlit.io/streamlit-community-cloud
- **Your UI Docs**: `ui/README_UI.md`

---

## 🎉 Success!

Once all three services are running, you'll have:

✅ Original honeypot working independently  
✅ Beautiful UI for demos and testing  
✅ Zero code changes to existing system  
✅ All deployed for FREE  
✅ Auto-deployments on git push  

**Share your Streamlit URL with anyone to demo the system!** 🕷️
