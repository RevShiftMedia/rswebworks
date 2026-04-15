# RSWebWorks Deployment Checklist

## Step 1: GitHub Setup (one-time)

1. Create repo on GitHub: `rswebworks` (public)
2. Add remote to local repo:
   ```bash
   cd ~/rswebworks
   git remote add origin https://github.com/[your-username]/rswebworks.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Vercel Setup (one-time)

1. Go to https://vercel.com/new
2. Import the GitHub repo (`rswebworks`)
3. Accept default settings
4. Deploy

## Step 3: Domain Setup (one-time)

1. In Vercel dashboard:
   - Go to project Settings → Domains
   - Add `rswebworks.com`
   - Copy the CNAME target value

2. In your domain registrar (where rswebworks.com is registered):
   - Update DNS:
     - Type: CNAME
     - Name: @ (or blank)
     - Value: `cname.vercel.com` (from Vercel)
     - TTL: 3600
   - Save

3. Wait 5-10 min for DNS to propagate

4. In Vercel, click "Verify" — should pass

## Step 4: Add New Mockups

1. Create folder:
   ```bash
   mkdir ~/rswebworks/new-client-name
   ```

2. Add `index.html` to folder

3. Commit & push:
   ```bash
   cd ~/rswebworks
   git add .
   git commit -m "Add New Client mockup"
   git push
   ```

4. Vercel auto-deploys in ~30 seconds

5. Visit: `https://newclientname.rswebworks.com/`

## Testing

**Local:** `python3 -m http.server 3000` → `http://localhost:3000/cw-powerwashing/`

**Live:** `https://rswebworks.com/cw-powerwashing/`

## Troubleshooting

- **DNS not resolving?** Wait 10-15 min, check TTL is 3600
- **Vercel showing 404?** Make sure folder has `index.html`
- **Old version showing?** Clear browser cache or use incognito

