# Bayora Isolation Lab: 1-Month Cloud Deployment Guide (₹0 Budget)

This guide explains how to deploy **Bayora Isolation Lab** to a free cloud platform so your public link remains **live 24/7 for 1 month** during the hackathon evaluation period, even when your laptop is turned off or in sleep mode.

---

## Recommended Free Cloud Host: Render.com

Render provides a completely free Web Service tier (750 free hours per month = 100% free for 30+ days) with automatic SSL (`https://bayora-isolation-lab.onrender.com`), continuous deployment, and zero credit card requirement.

### Step 1: Push your project to GitHub

Run these commands in your project folder:

```bash
git add .
git commit -m "Deploy Bayora Isolation Lab v1.0.0"
git branch -M main
git push -u origin main
```

---

### Step 2: Deploy to Render (60-Second 1-Click Setup)

1. Go to [https://render.com](https://render.com) and sign in (or create a free account with GitHub).
2. Click the **"New +"** button in the top right and select **"Web Service"** (or **"Blueprint"**).
3. Connect your `bayora-isolation-lab` GitHub repository.
4. Render will automatically detect the `render.yaml` or `Dockerfile`:
   - **Name:** `bayora-isolation-lab`
   - **Runtime:** `Docker`
   - **Instance Type:** `Free`
   - **Environment Variables:**
     - `GROQ_API_KEY`: Enter your Groq API key in the Render dashboard
     - `GROQ_MODEL`: `llama-3.3-70b-versatile`
5. Click **"Deploy Web Service"**.

In approximately 2 minutes, Render will build the unified Docker image, seed baseline demo policies, and provide your permanent public HTTPS URL:
```text
https://bayora-isolation-lab.onrender.com
```

*This link will remain live and accessible globally for the entire month!*

---

## Alternative Free Option: Hugging Face Spaces

If you prefer Hugging Face:
1. Go to [https://huggingface.co/spaces](https://huggingface.co/spaces) and click **"Create new Space"**.
2. Select **Space SDK:** `Docker` (Blank).
3. Push your repository files to the Hugging Face Space git remote:
   ```bash
   git remote add space https://huggingface.co/spaces/<YOUR_USERNAME>/bayora-isolation-lab
   git push space main
   ```
4. Hugging Face builds and hosts the app with a permanent URL: `https://<YOUR_USERNAME>-bayora-isolation-lab.hf.space`.

---

## Local Docker Container Verification

To test the exact container that runs in the cloud on your laptop:

```bash
# Build the production Docker image
docker build -t bayora-isolation-lab .

# Run container on port 8000
docker run -p 8000:8000 -e GROQ_API_KEY="your_groq_api_key_here" bayora-isolation-lab
```
Open `http://localhost:8000` to verify the unified full-stack application.
