# Deploying HoldemMate

This guide covers the recommended path: **Streamlit Community Cloud** with a
shared-password gate. The whole process takes about 5 minutes.

## Prerequisites

- The `HoldemMate` repo is on GitHub (public or private).
- You have an Anthropic API key.
- You've decided on a shared password to gate the app.

## Step 1 — Push to GitHub

If you haven't already:

```bash
cd HoldemMate
git init -b main
git add .
git status                 # double-check that .env is NOT listed
git commit -m "Initial commit"
git remote add origin https://github.com/<your-user>/HoldemMate.git
git push -u origin main
```

The `.gitignore` already excludes `.env`, `.streamlit/secrets.toml`, and
`__pycache__/`, so secrets stay local.

## Step 2 — Create the app on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app**.
3. Select your `HoldemMate` repo and branch (`main`).
4. **Main file path:** `app.py`
5. (Optional) Set a custom subdomain like `holdemmate`.
6. Click **Advanced settings → Secrets** and paste:

   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   HOLDEMMATE_MODEL = "claude-sonnet-4-6"
   HOLDEMMATE_MC_TRIALS = "2000"
   APP_PASSWORD = "your-shared-password"
   ```

7. Click **Deploy**.

The first build takes ~2 minutes (installing `treys`, `langgraph`,
`anthropic`, `streamlit`). You'll get a URL like
`https://holdemmate.streamlit.app`.

## Step 3 — Test on your phone

Open the URL on your phone. You should see the password prompt. Enter the
password — the card grid loads, with horizontally scrollable suit rows and
red hearts/diamonds.

## Updating the app

Just push to `main`:

```bash
git push origin main
```

Streamlit Cloud auto-redeploys within ~30 seconds.

## Rotating the password

Edit the secrets in the Streamlit Cloud UI (your app → **Settings → Secrets**)
and click **Save**. The app restarts with the new password. No git push needed.

## Cost monitoring

- Each recommendation makes 3 Claude API calls.
- On Sonnet 4.6 (default), expect ~$0.01–$0.02 per recommendation, so ~$0.04–$0.08 per full hand.
- Set a hard monthly cap in the [Anthropic console](https://console.anthropic.com) under **Settings → Limits**. Even with the password gate, this is your real safety net.
- To cut cost ~5×, change `HOLDEMMATE_MODEL` to `claude-haiku-4-5-20251001` in the secrets UI.

## If the build fails

Common issues:

- **`anthropic` library can't authenticate.** The `ANTHROPIC_API_KEY` secret is
  missing or has a typo. Check the Streamlit Cloud secrets UI.
- **`ImportError: No module named 'treys'`.** The build didn't install
  `requirements.txt`. Make sure that file is at the repo root and not nested
  inside another folder.
- **Page is blank or shows the error overlay.** Click **Manage app → Logs** in
  the Streamlit Cloud UI to see the Python traceback.

## Alternative deploy targets

| Target | Cost | When to use |
|---|---|---|
| Streamlit Community Cloud | Free | Default. This guide. |
| Render / Railway | Free tier → $5+/mo | Need custom domain or more CPU |
| Fly.io with Dockerfile | Free tier → pay-as-you-go | Want global edge deployment |
| Self-host on a VPS | $5+/mo (DO, Hetzner) | Full control, run alongside other services |

For Render or Railway, the start command is:

```
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

Set the same secrets as environment variables in the platform's UI.
