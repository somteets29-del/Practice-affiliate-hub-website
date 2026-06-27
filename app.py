"""
AffiliateHub - Amazon Affiliate Content Website
Python + Flask + SQLite
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import re
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///affiliatehub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

AMAZON_TAG = os.environ.get('AMAZON_TAG', '101019a-20')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Cynthia@123')

db = SQLAlchemy(app)


@app.context_processor
def inject_nav_categories():
    try:
        cats = Category.query.all()
    except Exception:
        cats = []
    return dict(categories_nav=cats)


# ─── MODELS ───────────────────────────────────────────────────────────────────

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50), default='🛍️')
    products = db.relationship('Product', backref='category', lazy=True)
    articles = db.relationship('Article', backref='category', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    image_url = db.Column(db.String(500))
    amazon_asin = db.Column(db.String(20))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    rating = db.Column(db.Float, default=4.5)
    review_count = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    click_count = db.Column(db.Integer, default=0)
    tags = db.Column(db.String(500))

    @property
    def affiliate_url(self):
        if self.amazon_asin:
            return f"https://www.amazon.com/dp/{self.amazon_asin}?tag={AMAZON_TAG}"
        return "#"

    @property
    def tag_list(self):
        if self.tags:
            return [t.strip() for t in self.tags.split(',')]
        return []


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    slug = db.Column(db.String(300), unique=True, nullable=False)
    excerpt = db.Column(db.String(500))
    content = db.Column(db.Text)
    cover_image = db.Column(db.String(500))
    pinterest_image = db.Column(db.String(500))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    view_count = db.Column(db.Integer, default=0)
    meta_title = db.Column(db.String(300))
    meta_description = db.Column(db.String(500))


class ArticleProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    position = db.Column(db.Integer, default=0)
    article = db.relationship('Article', backref='article_products')
    product = db.relationship('Product', backref='article_products')


class Click(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(300))
    referrer = db.Column(db.String(500))
    product = db.relationship('Product', backref='clicks')


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')


def is_admin():
    return request.cookies.get('admin_session') == app.config['SECRET_KEY'][:32]


# ─── PUBLIC ROUTES ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    featured = Product.query.filter_by(is_featured=True).limit(6).all()
    categories = Category.query.all()
    recent_articles = Article.query.filter_by(is_published=True)\
        .order_by(Article.created_at.desc()).limit(3).all()
    top_products = Product.query.order_by(Product.click_count.desc()).limit(8).all()
    return render_template('index.html',
                           featured=featured,
                           categories=categories,
                           recent_articles=recent_articles,
                           top_products=top_products)


@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)
    sort = request.args.get('sort', 'relevance')

    products = Product.query
    if q:
        products = products.filter(
            db.or_(
                Product.name.ilike(f'%{q}%'),
                Product.description.ilike(f'%{q}%'),
                Product.tags.ilike(f'%{q}%')
            )
        )
    if category_id:
        products = products.filter_by(category_id=category_id)

    if sort == 'price_asc':
        products = products.order_by(Product.price.asc())
    elif sort == 'price_desc':
        products = products.order_by(Product.price.desc())
    elif sort == 'popular':
        products = products.order_by(Product.click_count.desc())
    elif sort == 'rating':
        products = products.order_by(Product.rating.desc())

    products = products.all()
    categories = Category.query.all()
    return render_template('search.html', products=products, query=q,
                           categories=categories, selected_cat=category_id, sort=sort)


@app.route('/category/<slug>')
def category(slug):
    cat = Category.query.filter_by(slug=slug).first_or_404()
    products = Product.query.filter_by(category_id=cat.id).all()
    articles = Article.query.filter_by(category_id=cat.id, is_published=True).all()
    return render_template('category.html', category=cat, products=products, articles=articles)


@app.route('/article/<slug>')
def article(slug):
    art = Article.query.filter_by(slug=slug, is_published=True).first_or_404()
    art.view_count += 1
    db.session.commit()
    linked = ArticleProduct.query\
        .filter_by(article_id=art.id)\
        .order_by(ArticleProduct.position)\
        .all()
    products = [ap.product for ap in linked]
    return render_template('article.html', article=art, products=products)


@app.route('/product/<int:product_id>')
def product(product_id):
    p = Product.query.get_or_404(product_id)
    related = Product.query.filter_by(category_id=p.category_id)\
        .filter(Product.id != p.id).limit(4).all()
    return render_template('product.html', product=p, related=related)


# ─── CLICK TRACKING ───────────────────────────────────────────────────────────

@app.route('/track/<int:product_id>')
def track_click(product_id):
    p = Product.query.get_or_404(product_id)
    article_id = request.args.get('article', type=int)
    click = Click(
        product_id=product_id,
        article_id=article_id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string[:300],
        referrer=request.referrer or ''
    )
    p.click_count += 1
    db.session.add(click)
    db.session.commit()
    return redirect(p.affiliate_url)


# ─── ADMIN AUTH ───────────────────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            response = redirect(url_for('admin_dashboard'))
            response.set_cookie('admin_session', app.config['SECRET_KEY'][:32],
                                httponly=True, max_age=86400)
            return response
        flash('Wrong password.', 'error')
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    response = redirect(url_for('index'))
    response.delete_cookie('admin_session')
    return response


# ─── ADMIN DASHBOARD ──────────────────────────────────────────────────────────

@app.route('/admin')
def admin_dashboard():
    if not is_admin():
        return redirect(url_for('admin_login'))

    total_products = Product.query.count()
    total_articles = Article.query.count()
    total_clicks = Click.query.count()
    total_views = db.session.query(db.func.sum(Article.view_count)).scalar() or 0

    from sqlalchemy import func
    daily_clicks = db.session.query(
        func.date(Click.timestamp).label('day'),
        func.count(Click.id).label('count')
    ).group_by('day').order_by('day').limit(14).all()

    top_products = Product.query.order_by(Product.click_count.desc()).limit(10).all()
    recent_clicks = Click.query.order_by(Click.timestamp.desc()).limit(20).all()

    return render_template('admin/dashboard.html',
                           total_products=total_products,
                           total_articles=total_articles,
                           total_clicks=total_clicks,
                           total_views=total_views,
                           daily_clicks=daily_clicks,
                           top_products=top_products,
                           recent_clicks=recent_clicks)


# ─── ADMIN: PRODUCTS ──────────────────────────────────────────────────────────

@app.route('/admin/products')
def admin_products():
    if not is_admin():
        return redirect(url_for('admin_login'))
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=products)


@app.route('/admin/products/new', methods=['GET', 'POST'])
def admin_product_new():
    if not is_admin():
        return redirect(url_for('admin_login'))
    categories = Category.query.all()

    if request.method == 'POST':
        p = Product(
            name=request.form['name'],
            description=request.form.get('description', ''),
            price=float(request.form.get('price', 0) or 0),
            image_url=request.form.get('image_url', ''),
            amazon_asin=request.form.get('amazon_asin', '').strip().upper(),
            category_id=request.form.get('category_id', type=int),
            rating=float(request.form.get('rating', 4.5)),
            review_count=int(request.form.get('review_count', 0) or 0),
            is_featured='is_featured' in request.form,
            tags=request.form.get('tags', '')
        )
        db.session.add(p)
        db.session.commit()
        flash(f'Product "{p.name}" added!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/product_form.html', product=None, categories=categories)


@app.route('/admin/products/<int:pid>/edit', methods=['GET', 'POST'])
def admin_product_edit(pid):
    if not is_admin():
        return redirect(url_for('admin_login'))
    p = Product.query.get_or_404(pid)
    categories = Category.query.all()

    if request.method == 'POST':
        p.name = request.form['name']
        p.description = request.form.get('description', '')
        p.price = float(request.form.get('price', 0) or 0)
        p.image_url = request.form.get('image_url', '')
        p.amazon_asin = request.form.get('amazon_asin', '').strip().upper()
        p.category_id = request.form.get('category_id', type=int)
        p.rating = float(request.form.get('rating', 4.5))
        p.review_count = int(request.form.get('review_count', 0) or 0)
        p.is_featured = 'is_featured' in request.form
        p.tags = request.form.get('tags', '')
        db.session.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/product_form.html', product=p, categories=categories)


@app.route('/admin/products/<int:pid>/delete', methods=['POST'])
def admin_product_delete(pid):
    if not is_admin():
        abort(403)
    p = Product.query.get_or_404(pid)
    ArticleProduct.query.filter_by(product_id=pid).delete()
    Click.query.filter_by(product_id=pid).delete()
    db.session.delete(p)
    db.session.commit()
    flash('Product deleted.', 'info')
    return redirect(url_for('admin_products'))


# ─── ADMIN: ARTICLES ──────────────────────────────────────────────────────────

@app.route('/admin/articles')
def admin_articles():
    if not is_admin():
        return redirect(url_for('admin_login'))
    articles = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('admin/articles.html', articles=articles)


@app.route('/admin/articles/new', methods=['GET', 'POST'])
def admin_article_new():
    if not is_admin():
        return redirect(url_for('admin_login'))
    categories = Category.query.all()
    all_products = Product.query.all()

    if request.method == 'POST':
        title = request.form['title']
        slug = slugify(title)
        base_slug = slug
        i = 1
        while Article.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{i}"
            i += 1

        art = Article(
            title=title,
            slug=slug,
            excerpt=request.form.get('excerpt', ''),
            content=request.form.get('content', ''),
            cover_image=request.form.get('cover_image', ''),
            pinterest_image=request.form.get('pinterest_image', ''),
            category_id=request.form.get('category_id', type=int),
            is_published='is_published' in request.form,
            meta_title=request.form.get('meta_title', title),
            meta_description=request.form.get('meta_description', '')
        )
        db.session.add(art)
        db.session.flush()

        product_ids = request.form.getlist('product_ids')
        for i, pid in enumerate(product_ids):
            ap = ArticleProduct(article_id=art.id, product_id=int(pid), position=i)
            db.session.add(ap)

        db.session.commit()
        flash(f'Article "{art.title}" created!', 'success')
        return redirect(url_for('admin_articles'))

    return render_template('admin/article_form.html', article=None,
                           categories=categories, all_products=all_products)


@app.route('/admin/articles/<int:aid>/edit', methods=['GET', 'POST'])
def admin_article_edit(aid):
    if not is_admin():
        return redirect(url_for('admin_login'))
    art = Article.query.get_or_404(aid)
    categories = Category.query.all()
    all_products = Product.query.all()
    linked_ids = [ap.product_id for ap in art.article_products]

    if request.method == 'POST':
        art.title = request.form['title']
        art.excerpt = request.form.get('excerpt', '')
        art.content = request.form.get('content', '')
        art.cover_image = request.form.get('cover_image', '')
        art.pinterest_image = request.form.get('pinterest_image', '')
        art.category_id = request.form.get('category_id', type=int)
        art.is_published = 'is_published' in request.form
        art.meta_title = request.form.get('meta_title', art.title)
        art.meta_description = request.form.get('meta_description', '')

        ArticleProduct.query.filter_by(article_id=art.id).delete()
        product_ids = request.form.getlist('product_ids')
        for i, pid in enumerate(product_ids):
            ap = ArticleProduct(article_id=art.id, product_id=int(pid), position=i)
            db.session.add(ap)

        db.session.commit()
        flash('Article updated!', 'success')
        return redirect(url_for('admin_articles'))

    return render_template('admin/article_form.html', article=art,
                           categories=categories, all_products=all_products,
                           linked_ids=linked_ids)


@app.route('/admin/articles/<int:aid>/delete', methods=['POST'])
def admin_article_delete(aid):
    if not is_admin():
        abort(403)
    art = Article.query.get_or_404(aid)
    ArticleProduct.query.filter_by(article_id=art.id).delete()
    db.session.delete(art)
    db.session.commit()
    flash('Article deleted.', 'info')
    return redirect(url_for('admin_articles'))


# ─── ADMIN: CATEGORIES ────────────────────────────────────────────────────────

@app.route('/admin/categories', methods=['GET', 'POST'])
def admin_categories():
    if not is_admin():
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        name = request.form['name']
        cat = Category(
            name=name,
            slug=slugify(name),
            description=request.form.get('description', ''),
            icon=request.form.get('icon', '🛍️')
        )
        db.session.add(cat)
        db.session.commit()
        flash(f'Category "{cat.name}" added!', 'success')
        return redirect(url_for('admin_categories'))

    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)


# ─── API ──────────────────────────────────────────────────────────────────────

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '')
    results = Product.query.filter(
        Product.name.ilike(f'%{q}%')
    ).limit(10).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': p.price,
        'image_url': p.image_url,
        'affiliate_url': url_for('track_click', product_id=p.id)
    } for p in results])


# ─── SEED DATA ────────────────────────────────────────────────────────────────

def seed_demo_data():
    if Category.query.first():
        return

    cats = [
        Category(name='Home & Kitchen', slug='home-kitchen',
                 description='Top-rated kitchen gadgets and home essentials', icon='🏠'),
        Category(name='Tech & Gadgets', slug='tech-gadgets',
                 description='The best tech for everyday life', icon='💻'),
        Category(name='Books', slug='books',
                 description='Must-read books across every genre', icon='📚'),
        Category(name='Fitness', slug='fitness',
                 description='Gear to level up your workouts', icon='💪'),
    ]
    for c in cats:
        db.session.add(c)
    db.session.flush()

    home_id = cats[0].id
    tech_id = cats[1].id
    fit_id  = cats[3].id

    products = [
        Product(name='Instant Pot Duo 7-in-1',
                description='The best-selling pressure cooker that replaces 7 kitchen appliances.',
                price=99.95, amazon_asin='B00FLYWNYQ',
                image_url='https://images-na.ssl-images-amazon.com/images/I/71WtwEvYDOS._AC_SL1500_.jpg',
                category_id=home_id, rating=4.7, review_count=115234,
                is_featured=True, tags='cooking,pressure cooker,instant pot,kitchen'),
        Product(name='Ninja Foodi Personal Blender',
                description='Compact yet powerful for smoothies, protein shakes, and sauces.',
                price=49.99, amazon_asin='B07FDBG7JT',
                image_url='https://images-na.ssl-images-amazon.com/images/I/71q8gegxKlL._AC_SL1500_.jpg',
                category_id=home_id, rating=4.6, review_count=43210,
                is_featured=True, tags='blender,smoothie,kitchen,ninja'),
        Product(name='Anker 65W USB-C Charger',
                description='Fast charge your laptop, phone, and tablet simultaneously.',
                price=35.99, amazon_asin='B08T8SRJF1',
                image_url='https://images-na.ssl-images-amazon.com/images/I/61TTbcPuGIL._AC_SL1500_.jpg',
                category_id=tech_id, rating=4.8, review_count=28904,
                is_featured=True, tags='charger,usb-c,anker,laptop'),
        Product(name='Echo Dot 5th Gen',
                description='Our best Echo Dot yet with improved audio and smarter home control.',
                price=49.99, amazon_asin='B09B8V1LZ3',
                image_url='https://images-na.ssl-images-amazon.com/images/I/714Rq4k05UL._AC_SL1500_.jpg',
                category_id=tech_id, rating=4.7, review_count=89421,
                is_featured=True, tags='echo,alexa,smart home,amazon'),
        Product(name='Resistance Bands Set 11 pcs',
                description='Full workout in one set with handles, door anchor, and ankle straps.',
                price=29.99, amazon_asin='B01AVDVHTI',
                image_url='https://images-na.ssl-images-amazon.com/images/I/81ZBLLN+YFL._AC_SL1500_.jpg',
                category_id=fit_id, rating=4.5, review_count=61293,
                is_featured=False, tags='resistance bands,fitness,workout,exercise'),
        Product(name='Adjustable Dumbbell Set 5-52.5 lbs',
                description='Replace an entire rack with these space-saving adjustable dumbbells.',
                price=349.00, amazon_asin='B001ARYU58',
                image_url='https://images-na.ssl-images-amazon.com/images/I/81Y3IFf0SQL._AC_SL1500_.jpg',
                category_id=fit_id, rating=4.8, review_count=32100,
                is_featured=True, tags='dumbbells,fitness,weights,home gym'),
    ]
    for p in products:
        db.session.add(p)
    db.session.flush()

    art = Article(
        title='10 Best Kitchen Gadgets Under $100 in 2024',
        slug='best-kitchen-gadgets-under-100-2024',
        excerpt='Transform your cooking with these top-rated Amazon kitchen gadgets all under $100.',
        content='''
<p>Whether you are a student cooking in a dorm or a home chef upgrading your kitchen, these gadgets will change the way you cook.</p>
<h2>1. The Instant Pot: A Kitchen Revolution</h2>
<p>The Instant Pot Duo is consistently one of Amazon best-selling products for good reason. It combines a pressure cooker, slow cooker, rice cooker, steamer, saute pan, yogurt maker, and warmer into one device.</p>
<h2>2. Ninja Blender: Smoothies in 60 Seconds</h2>
<p>The Ninja Personal Blender punches well above its price point. The cups double as travel mugs. It handles ice, frozen fruit, and even nut butter without breaking a sweat.</p>
        ''',
        cover_image='https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=1200',
        pinterest_image='https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=735&h=1102&fit=crop',
        category_id=home_id,
        is_published=True,
        meta_title='10 Best Kitchen Gadgets Under $100 2024 Amazon Picks',
        meta_description='Upgrade your kitchen without breaking the bank. Top 10 Amazon kitchen gadgets under $100.'
    )
    db.session.add(art)
    db.session.flush()

    db.session.add(ArticleProduct(article_id=art.id, product_id=products[0].id, position=0))
    db.session.add(ArticleProduct(article_id=art.id, product_id=products[1].id, position=1))
    db.session.commit()
    print('✅ Demo data seeded!')


# ─── INIT ─────────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()
    seed_demo_data()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
