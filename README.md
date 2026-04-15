# RSWebWorks — Mockup Portfolio

Professional website mockups for local service businesses.

## Structure

```
rswebworks/
├── cw-powerwashing/       → cwpowerwashing.rswebworks.com
├── rauls-lawn-care/       → raulslawncare.rswebworks.com
├── rios-lawn-care/        → rioslawncare.rswebworks.com
└── [future clients]
```

Each folder contains an `index.html` mockup.

## Deploy

```bash
git add .
git commit -m "Add [business] mockup"
git push origin main
```

Vercel auto-deploys to `rswebworks.com` domain.

## DNS Setup

Point `rswebworks.com` A record to Vercel:

```
Type: CNAME
Name: @
Value: cname.vercel.com
TTL: 3600
```

Then configure the domain in Vercel dashboard:
1. Go to Settings → Domains
2. Add `rswebworks.com`
3. Vercel will verify the DNS change

## Local Dev

```bash
python3 -m http.server 3000
# Open http://localhost:3000/cw-powerwashing/
```
