# AffiliateHub — Amazon Affiliate Website
**Python + Flask + SQLite** | Mobile-responsive | Pinterest-optimized | Admin panel + click tracking

---

## 📁 Project Structure

```
affiliatehub/
├── app.py                  ← Main Flask app (routes, models, logic)
├── requirements.txt        ← Python dependencies
├── templates/
│   ├── base.html           ← Shared layout (navbar, footer)
│   ├── index.html          ← Homepage
│   ├── search.html         ← Search results + filters
│   ├── category.html       ← Category page
│   ├── article.html        ← Blog article (Pinterest-optimized)
│   ├── product.html        ← Single product page
│   ├── partials/
│   │   └── product_card.html
│   └── admin/
│       ├── base.html       ← Admin layout
│       ├── login.html
│       ├── dashboard.html  ← Click stats + charts
│       ├── products.html
│       ├── product_form.html
│       ├── articles.html
│       ├── article_form.html
│       └── categories.html
└── static/
    ├── css/main.css        ← Full responsive styles
    └── js/main.js          ← Live search autocomplete
```

---

## ⚙️ Setup (Local / Termux)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Amazon tag (optional — defaults to 'yourtag-20')
export AMAZON_TAG="yourname-20"
export ADMIN_PASSWORD="your_secure_password"

# 3. Run
python app.py
# → Open: http://localhost:5000
# → Admin: http://localhost:5000/admin  (password: changeme123 by default)
```

---

## 🚀 Deployment (Render.com — Free Tier)

1. Push this folder to a GitHub repo
2. Go to [render.com](https://render.com) → New Web Service → connect your repo
3. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
4. Add environment variables:
   - `AMAZON_TAG` = your Amazon Associates tag
   - `ADMIN_PASSWORD` = a strong password
   - `SECRET_KEY` = a random 64-char string

---

## 🚀 Deployment (Railway / Fly.io)

Both work the same way — push to GitHub, connect repo, set env vars, deploy.

---

## 📌 Pinterest Strategy

**The funnel:** Pinterest Pin → Your Article → Amazon Affiliate Link

1. Write a roundup article (e.g. "10 Best Air Fryers Under $100")
2. Add a **Pinterest Image** (735×1102 vertical) to the article in Admin
3. The article page automatically includes:
   - Pinterest `data-pin-description` on images
   - Open Graph `og:image` pointing to your Pinterest image
   - JSON-LD Article schema for Rich Pins
   - Pinterest's `pinit.js` for the Save button
4. Pin your article URL (not the Amazon link) to Pinterest

---

## 💰 Amazon Associates Setup

1. Sign up at [affiliate-program.amazon.com](https://affiliate-program.amazon.com)
2. Get your **Associate Tag** (e.g. `myblog-20`)
3. Set it as `AMAZON_TAG` environment variable
4. Find ASINs: On any Amazon product page, look at the URL → `/dp/ASIN`
   - Example: `amazon.com/dp/B00FLYWNYQ` → ASIN is `B00FLYWNYQ`
5. Add products in Admin → Products → the affiliate URL builds automatically

---

## 🔑 Admin Panel

URL: `/admin` | Default password: `changeme123` (change via `ADMIN_PASSWORD` env var)

**What you can do without touching code:**
- ➕ Add/edit/delete products (name, ASIN, price, image, rating, tags)
- 📝 Write and publish articles with HTML content
- 🔗 Link products to articles (they appear in sidebar + "Products Mentioned")
- 🗂️ Create categories with icons
- 📊 View click stats, top products, daily click chart, referrer tracking

---

## 📊 Click Tracking

Every "View on Amazon" click goes through `/track/<product_id>` which:
1. Records: timestamp, product, article source, IP, referrer
2. Increments the product's `click_count`
3. Redirects to Amazon with your affiliate tag

View all data in **Admin → Dashboard**.

---

## 🐍 What You're Learning

Working through this project teaches you:

| Concept | Where it appears |
|---------|-----------------|
| Flask routes & views | Every `@app.route` in app.py |
| SQLAlchemy ORM | Models: Product, Article, Category, Click |
| Template inheritance | base.html → index.html / article.html |
| Forms & POST requests | Admin forms in product_form.html |
| Context processors | `inject_nav_categories()` |
| Cookies & auth | Admin login session |
| Database relationships | ArticleProduct join table |
| Environment variables | SECRET_KEY, ADMIN_PASSWORD, AMAZON_TAG |
| Deployment | gunicorn + Render/Railway |

---

## 🗺️ Next Steps (When You're Ready)

- [ ] Add image upload (Flask-Uploads or Cloudinary)
- [ ] Add pagination on search / category pages
- [ ] Email newsletter capture (Mailchimp integration)
- [ ] Sitemap.xml for SEO (`/sitemap.xml` route)
- [ ] RSS feed for Pinterest RSS boards
- [ ] User authentication for multiple admins
- [ ] Scheduled price updates via Amazon PA API
