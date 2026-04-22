from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
from datetime import datetime
import hashlib
import pandas as pd
from werkzeug.utils import secure_filename

from colorimetry_analyzer import ColorimetryAnalyzer
from outfit_generator import OutfitGenerator
from wardrobe_manager import WardrobeManager
from clothing_database import ClothingDatabase
from gtts import gTTS

app = Flask(__name__)
app.secret_key = 'smart-wardrobe-uie-2025-SECRET-KEY-CHANGE-THIS'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Create required directories
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('data/wardrobes', exist_ok=True)
os.makedirs('data/history', exist_ok=True)
os.makedirs('data/colorimetry', exist_ok=True)
os.makedirs('static/audio', exist_ok=True)
os.makedirs('static/clothing_images', exist_ok=True)
os.makedirs('static/user_clothing', exist_ok=True)

USERS_FILE = 'data/users.json'

# Initialise modules
colorimetry_analyzer = ColorimetryAnalyzer()
outfit_generator     = OutfitGenerator()
clothing_db          = ClothingDatabase()

# ========== USER FUNCTIONS ==========

def load_users():
    """Load users from JSON file."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """Save users to JSON file."""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

# ========== SAVED COLORIMETRY FUNCTIONS ==========

def get_user_colorimetry(user_email):
    """Retrieve saved colorimetry result for a user (valid for up to 6 months)."""
    color_file = f'data/colorimetry/{_sanitize_email(user_email)}.json'
    if os.path.exists(color_file):
        try:
            with open(color_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                saved_date = datetime.fromisoformat(data.get('saved_at', '2000-01-01'))
                if (datetime.now() - saved_date).days < 180:
                    return data.get('colorimetry_result')
        except:
            pass
    return None

def save_user_colorimetry(user_email, colorimetry_result):
    """Save a user's colorimetry result to disk."""
    color_file = f'data/colorimetry/{_sanitize_email(user_email)}.json'
    with open(color_file, 'w', encoding='utf-8') as f:
        json.dump({
            'saved_at': datetime.now().isoformat(),
            'colorimetry_result': colorimetry_result
        }, f, indent=2, ensure_ascii=False)

def _sanitize_email(email):
    """Convert an email address into a safe filename."""
    return email.replace('@', '_at_').replace('.', '_')

# ========== HISTORY FUNCTIONS ==========

def save_to_history(user_email, result_data):
    """Save a recommendation query to the user's history (max 20 entries)."""
    history_file = f'data/history/{_sanitize_email(user_email)}.json'
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []

    history.append({
        'timestamp': datetime.now().isoformat(),
        'result': result_data
    })

    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history[-20:], f, indent=2, ensure_ascii=False)

def get_user_history(user_email):
    """Retrieve the recommendation history for a user."""
    history_file = f'data/history/{_sanitize_email(user_email)}.json'
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

# ========== CLIMATE FUNCTIONS ==========

def load_climate_data():
    """Load historical climate data from the Excel file (52 Spanish provinces)."""
    try:
        df = pd.read_excel('data/clima_provincias.xlsx')
        print("DEBUG: clima_provincias.xlsx loaded successfully.")
        return df
    except FileNotFoundError:
        print("WARNING: clima_provincias.xlsx not found.")
        return None
    except Exception as e:
        print(f"ERROR: Failed to load clima_provincias.xlsx. Reason: {e}")
        return None

def get_climate_info(provincia, mes):
    """
    Return temperature and rain probability for a given province and month.
    Falls back to approximate Spanish averages if the Excel file is unavailable.
    """
    df = load_climate_data()

    # Default fallback values (approximate Spanish averages)
    defaults_by_month = {
        'Diciembre':  {'temperatura': 11, 'prob_lluvia': 60},
        'Enero':      {'temperatura': 10, 'prob_lluvia': 55},
        'Febrero':    {'temperatura': 11, 'prob_lluvia': 50},
        'Marzo':      {'temperatura': 13, 'prob_lluvia': 45},
        'Abril':      {'temperatura': 15, 'prob_lluvia': 50},
        'Mayo':       {'temperatura': 18, 'prob_lluvia': 45},
        'Junio':      {'temperatura': 22, 'prob_lluvia': 30},
        'Julio':      {'temperatura': 25, 'prob_lluvia': 20},
        'Agosto':     {'temperatura': 25, 'prob_lluvia': 20},
        'Septiembre': {'temperatura': 23, 'prob_lluvia': 35},
        'Octubre':    {'temperatura': 18, 'prob_lluvia': 50},
        'Noviembre':  {'temperatura': 13, 'prob_lluvia': 60}
    }

    if df is None:
        return defaults_by_month.get(mes, {"temperatura": 18, "prob_lluvia": 40})

    try:
        row = df[(df['Provincia'] == provincia) & (df['Mes'] == mes)]
        if not row.empty:
            return {
                "temperatura": int(row.iloc[0]['Temp_media']),
                "prob_lluvia": int(row.iloc[0]['Prob_lluvia'])
            }
    except Exception as e:
        print(f"Error retrieving climate data: {e}")

    return defaults_by_month.get(mes, {"temperatura": 18, "prob_lluvia": 40})

# ========== AUDIO FUNCTIONS ==========

def generate_audio(text, filename):
    """Generate an MP3 audio file from text using gTTS."""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        audio_path = f'static/audio/{filename}'
        tts.save(audio_path)
        return audio_path
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None

# ========== MAIN ROUTES ==========

@app.route('/')
def welcome():
    """Welcome / landing page."""
    return render_template('welcome.html')

@app.route('/index')
def index():
    """Root index — redirects based on session state."""
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('welcome'))

@app.route('/dashboard')
def dashboard():
    """User dashboard (requires authentication)."""
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user_email=session['user'])

# ========== AUTHENTICATION ROUTES ==========

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if request.method == 'POST':
        try:
            data     = request.get_json()
            email    = data.get('email', '').strip().lower()
            password = data.get('password', '')

            if not email or not password:
                return jsonify({'success': False, 'message': 'Email and password are required'}), 400

            users = load_users()

            if email in users:
                stored_hash = users[email]['password']
                input_hash  = hash_password(password)

                if stored_hash == input_hash:
                    session['user'] = email
                    return jsonify({'success': True, 'message': 'Login successful'})
                else:
                    return jsonify({'success': False, 'message': 'Incorrect password'}), 401
            else:
                return jsonify({'success': False, 'message': 'User not found'}), 404

        except Exception as e:
            print(f"Login error: {e}")
            return jsonify({'success': False, 'message': 'Server error'}), 500

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if request.method == 'POST':
        try:
            data             = request.get_json()
            email            = data.get('email', '').strip().lower()
            password         = data.get('password', '')
            confirm_password = data.get('confirm_password', '')

            if not email or not password:
                return jsonify({'success': False, 'message': 'Email and password are required'}), 400
            if len(password) < 6:
                return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
            if password != confirm_password:
                return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
            if '@' not in email or '.' not in email:
                return jsonify({'success': False, 'message': 'Invalid email address'}), 400

            users = load_users()

            if email in users:
                return jsonify({'success': False, 'message': 'User already exists'}), 409

            users[email] = {
                'password':   hash_password(password),
                'created_at': datetime.now().isoformat()
            }
            save_users(users)

            session['user'] = email
            return jsonify({'success': True, 'message': 'Registration successful'})

        except Exception as e:
            print(f"Registration error: {e}")
            return jsonify({'success': False, 'message': 'Server error'}), 500

    return render_template('register.html')

@app.route('/logout')
def logout():
    """Log the user out and redirect to the welcome page."""
    session.pop('user', None)
    return redirect(url_for('welcome'))

# ========== APPLICATION ROUTES ==========

@app.route('/recommendation')
def recommendation():
    """Recommendation / analysis page."""
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('onboarding.html')

@app.route('/wardrobe')
def wardrobe():
    """Virtual wardrobe management page."""
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('wardrobe.html', user_email=session['user'])

@app.route('/history')
def history():
    """Recommendation history page."""
    if 'user' not in session:
        return redirect(url_for('login'))
    user_history = get_user_history(session['user'])
    return render_template('history.html', history=user_history)

@app.route('/results')
def results():
    """Results page."""
    if 'user' not in session:
        return redirect(url_for('login'))
    result_data = session.get('last_result', {})
    return render_template('results.html', data=result_data)

# ========== KBS INFERENCE ENGINE ==========

def detect_masculine_preference(no_dresses, no_skirts, no_tops, gender=None):
    """
    KBS rule: detect masculine garment preference.
    Triggered when the user explicitly marks dresses + skirts + tops as unwanted,
    or when gender is set to 'hombre'.
    """
    if gender and gender.lower() == 'hombre':
        return True
    if no_dresses and no_skirts and no_tops:
        print("    Masculine preference detected (no dresses + no skirts + no tops)")
        return True
    return False

def filter_feminine_garments(items, category):
    """
    KBS rule: remove garments considered feminine from a candidate list.
    Applied to footwear (sandals) and accessories (handbags, earrings, etc.)
    when masculine preference is detected.
    """
    feminine_keywords = {
        'calzado':     ['alpargata', 'sandalia'],
        'complemento': ['bolso', 'bolsa', 'cartera', 'collar', 'pendiente',
                        'diadema', 'horquilla', 'pañuelo']
    }

    if category not in feminine_keywords:
        return items

    filtered = []
    for item in items:
        name = item.get('nombre', '').lower()
        is_feminine = any(kw in name for kw in feminine_keywords[category])
        if not is_feminine:
            filtered.append(item)
        else:
            print(f"    Filtered (feminine): {item.get('nombre')}")
    return filtered

def generate_smart_outfit(user_items, db_items, ocasion, clima, temperatura, prob_lluvia,
                           estacion, palette_colors, fit_preference,
                           no_vestidos, no_faldas, no_pantalones, no_tops=False, genero=None):
    """
    KBS Inference Engine — forward-chaining outfit selection.

    Scoring rules applied to each candidate garment:
        +50 pts  occasion match  (mandatory — garment excluded if score < 50)
        +30 pts  climate match
        +20 pts  colorimetry season match

    Selection priority:
        1. User wardrobe items (scored and sorted by colour palette match)
        2. Generic clothing database (fallback if no user item scores >= 50)

    Special climate rules:
        - Rain probability > 60%  → prefer boots for footwear
        - Temperature < 10°C      → prefer scarf/hat as accessory

    Gender filter rules:
        - Masculine preference detected → remove feminine footwear and accessories
        - no_faldas flag              → exclude skirts from bottom candidates
        - no_pantalones flag          → exclude trousers from bottom candidates
        - no_vestidos flag            → skip dress category entirely
    """
    outfit = {}

    masculine_pref = detect_masculine_preference(no_vestidos, no_faldas, no_tops, genero)

    def _normalize_field(value):
        """Normalise a garment field value to a list of lowercase strings."""
        if isinstance(value, str):
            try:
                import json as _json
                value = _json.loads(value)
            except:
                value = [value]
        if not isinstance(value, list):
            value = [value]
        return [str(v).lower() for v in value]

    def score_garment(item, ocasion, clima, estacion):
        """
        Forward-chaining scoring function (KBS Inference Engine).

        Scoring rules:
            +50 pts  occasion match  — mandatory; garment is discarded if score < 50
            +30 pts  climate match   — bonus
            +20 pts  season match    — bonus
        Maximum possible score: 100 pts.

        A garment is selected only if score >= 50 (i.e. occasion must match).
        Climate and season add bonus points that determine ranking priority
        but do not discard an otherwise valid garment on their own.
        """
        score = 0

        # --- Occasion rule (mandatory, +50 pts) ---
        item_ocasiones = _normalize_field(item.get('ocasion', []))
        if ocasion.lower() in item_ocasiones:
            score += 50
        else:
            return 0  # discard immediately — occasion is mandatory

        # --- Climate rule (+30 pts bonus) ---
        item_climas = _normalize_field(item.get('clima_apropiado', item.get('clima', [])))
        if clima.lower() in item_climas:
            score += 30

        # --- Season rule (+20 pts bonus) ---
        if 'estacion' in item:
            item_estaciones = _normalize_field(item.get('estacion', []))
            if estacion.lower() in item_estaciones:
                score += 20

        return score  # range: 50 / 80 / 100 (or 0 if discarded)

    def color_match_score(item, palette_colors):
        """
        Returns a colour-palette match score (0–100) for sorting candidates.
        Higher score = better match with the user's colorimetry palette.
        """
        item_colors = item.get('color', [])
        if isinstance(item_colors, str):
            try:
                import json
                item_colors = json.loads(item_colors)
            except:
                item_colors = [item_colors]
        if not isinstance(item_colors, list):
            item_colors = [item_colors]

        palette_keywords = set()
        for color_name in palette_colors:
            palette_keywords.update(color_name.lower().split())

        matches = sum(1 for c in item_colors
                      if any(kw in c.lower() for kw in palette_keywords))
        return (matches / max(len(item_colors), 1)) * 100

    # --- Rule 1: DRESS (only for formal/casual; skipped if no_vestidos) ---
    if not no_vestidos and ocasion in ['formal', 'casual']:
        dresses_user = [i for i in user_items
                        if i.get('tipo') == 'vestido' and score_garment(i, ocasion, clima, estacion) >= 50]
        if dresses_user:
            dresses_user.sort(key=lambda x: color_match_score(x, palette_colors), reverse=True)
            outfit['vestido'] = dresses_user[0]
            print(f"   ✓ Dress (USER): {outfit['vestido'].get('nombre')}")
        else:
            dresses_db = db_items.search_items(tipo='vestido', ocasion=ocasion, clima=clima, estacion=estacion)
            if dresses_db:
                dresses_db.sort(key=lambda x: color_match_score(x, palette_colors), reverse=True)
                outfit['vestido'] = dresses_db[0]

    # --- Rule 2: TOP + BOTTOM (if no dress selected) ---
    if 'vestido' not in outfit:
        # TOP
        tops_user = [i for i in user_items
                     if i.get('tipo') == 'superior' and score_garment(i, ocasion, clima, estacion) >= 50]
        if tops_user:
            tops_user.sort(key=lambda x: color_match_score(x, palette_colors), reverse=True)
            outfit['superior'] = tops_user[0]
            print(f"   ✓ Top (USER): {outfit['superior'].get('nombre')}")
        else:
            tops_db = db_items.search_items(tipo='superior', ocasion=ocasion, clima=clima, estacion=estacion)
            if tops_db:
                tops_db.sort(key=lambda x: color_match_score(x, palette_colors), reverse=True)
                outfit['superior'] = tops_db[0]

        # BOTTOM
        bottoms_user = [i for i in user_items
                        if i.get('tipo') == 'inferior' and score_garment(i, ocasion, clima, estacion) >= 50]
        if no_faldas:
            bottoms_user = [i for i in bottoms_user if 'falda' not in i.get('nombre', '').lower()]
        if no_pantalones:
            bottoms_user = [i for i in bottoms_user if 'pantalon' not in i.get('nombre', '').lower()]

        if bottoms_user:
            bottoms_user.sort(key=lambda x: color_match_score(x, palette_colors), reverse=True)
            outfit['inferior'] = bottoms_user[0]
            print(f"   ✓ Bottom (USER): {outfit['inferior'].get('nombre')}")
        else:
            bottoms_db = db_items.search_items(tipo='inferior', ocasion=ocasion, clima=clima, estacion=estacion)
            if bottoms_db:
                bottoms_db.sort(key=lambda x: color_match_score(x, palette_colors), reverse=True)
                outfit['inferior'] = bottoms_db[0]

    # --- Rule 3: FOOTWEAR (rain rule: prob > 60% → prefer boots) ---
    footwear_user = [i for i in user_items
                     if i.get('tipo') == 'calzado' and score_garment(i, ocasion, clima, estacion) >= 50]
    if masculine_pref:
        footwear_user = filter_feminine_garments(footwear_user, 'calzado')
    if prob_lluvia >= 60 and footwear_user:
        boots = [i for i in footwear_user if 'bota' in i.get('nombre', '').lower()]
        if boots:
            footwear_user = boots
            print(f"    Rain {prob_lluvia}% → boots preferred")

    if footwear_user:
        footwear_user.sort(key=lambda x: color_match_score(x, palette_colors), reverse=True)
        outfit['calzado'] = footwear_user[0]
        print(f"   ✓ Footwear (USER): {outfit['calzado'].get('nombre')}")
    else:
        footwear_db = db_items.search_items(tipo='calzado', ocasion=ocasion, clima=clima)
        if footwear_db:
            if masculine_pref:
                footwear_db = filter_feminine_garments(footwear_db, 'calzado')
            if footwear_db:
                footwear_db.sort(key=lambda x: color_match_score(x, palette_colors), reverse=True)
                outfit['calzado'] = footwear_db[0]

    # --- Rule 4: ACCESSORY (cold rule: temp < 10°C → prefer scarf/hat) ---
    acc_user = [i for i in user_items
                if i.get('tipo') == 'complemento' and score_garment(i, ocasion, clima, estacion) >= 50]
    if masculine_pref:
        acc_user = filter_feminine_garments(acc_user, 'complemento')
    if temperatura < 10 and acc_user:
        warm_acc = [i for i in acc_user
                    if 'bufanda' in i.get('nombre', '').lower() or 'gorro' in i.get('nombre', '').lower()]
        if warm_acc:
            acc_user = warm_acc
            print(f"    Cold {temperatura}°C → scarf/hat preferred")

    if acc_user:
        acc_user.sort(key=lambda x: color_match_score(x, palette_colors), reverse=True)
        outfit['complemento'] = acc_user[0]
        print(f"   ✓ Accessory (USER): {outfit['complemento'].get('nombre')}")
    else:
        acc_db = db_items.search_items(tipo='complemento', ocasion=ocasion, clima=clima)
        if acc_db:
            if masculine_pref:
                acc_db = filter_feminine_garments(acc_db, 'complemento')
            if acc_db:
                acc_db.sort(key=lambda x: color_match_score(x, palette_colors), reverse=True)
                outfit['complemento'] = acc_db[0]

    return outfit

# ========== RECOMMENDATION API ==========

@app.route('/api/onboarding', methods=['POST'])
def onboarding():
    """
    Main recommendation endpoint.
    Orchestrates the full KBS pipeline:
      1. Colorimetry analysis (or load cached result)
      2. Climate data lookup
      3. KBS inference engine (generate_smart_outfit)
      4. Narrative generation (outfit_generator)
      5. Audio generation (gTTS)
    """
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        data       = request.form.to_dict()
        user_email = session['user']

        # Step 1 — Colorimetry
        saved_colorimetry = get_user_colorimetry(user_email)
        photo_path        = None
        colorimetry_result = saved_colorimetry

        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename:
                filename   = secure_filename(f"{user_email}_{datetime.now().timestamp()}.jpg")
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(photo_path)
                print("Analysing colorimetry...")
                colorimetry_result = colorimetry_analyzer.analyze_image(photo_path)
                print(f"Analysis complete: {colorimetry_result['season']}")
                save_user_colorimetry(user_email, colorimetry_result)

        if colorimetry_result is None:
            colorimetry_result = colorimetry_analyzer._get_default_result()
            print("Using default colorimetry result")
        else:
            print(f"Using colorimetry: {colorimetry_result['season']}")

        # Step 2 — Climate data
        clima_info = get_climate_info(data.get('provincia'), data.get('mes'))
        temp = clima_info.get('temperatura', 20)
        if temp > 25:
            clima_cat = 'calor'
        elif temp > 15:
            clima_cat = 'templado'
        else:
            clima_cat = 'frio'

        # Step 3 — KBS inference engine
        season         = colorimetry_result['season']
        palette_colors = colorimetry_result.get('palette_names', [])
        print(f"Palette for {season}: {', '.join(palette_colors[:4])}")

        wardrobe   = WardrobeManager(user_email)
        user_items = wardrobe.get_all_items()

        print("Generating smart outfit...")
        print(f"   - User wardrobe items: {len(user_items)}")
        print(f"   - Occasion: {data.get('ocasion', 'casual')}")
        print(f"   - Climate: {clima_cat} ({clima_info.get('temperatura')}°C)")
        print(f"   - Rain probability: {clima_info.get('prob_lluvia')}%")

        outfit_items = generate_smart_outfit(
            user_items     = user_items,
            db_items       = clothing_db,
            ocasion        = data.get('ocasion', 'casual').lower(),
            clima          = clima_cat,
            temperatura    = clima_info.get('temperatura', 20),
            prob_lluvia    = clima_info.get('prob_lluvia', 30),
            estacion       = season,
            palette_colors = palette_colors,
            fit_preference = data.get('fit'),
            no_vestidos    = data.get('no_vestidos', False),
            no_faldas      = data.get('no_faldas', False),
            no_pantalones  = data.get('no_pantalones', False),
            no_tops        = data.get('no_tops', False),
            genero         = data.get('genero')
        )

        outfit_source = ("user" if any(item.get('id', '').startswith('item_')
                          for item in outfit_items.values()) else "database")
        print(f"Outfit sourced from: {outfit_source}")

        # Step 4 — Narrative generation
        print("Generating outfit narrative...")
        outfit_result    = outfit_generator.generate_outfit_complete(
            user_data          = data,
            clima_info         = clima_info,
            colorimetry_result = colorimetry_result,
            outfit_items       = outfit_items
        )
        outfit_narrative = outfit_result['outfit_narrative']
        outfit_simple    = generate_simple_outfit_text(outfit_items)

        # Step 5 — Audio
        audio_filename = f"recommendation_{user_email}_{datetime.now().timestamp()}.mp3"
        audio_path     = generate_audio(outfit_narrative, audio_filename)

        # Build result
        result = {
            'success':          True,
            'usuario':          data.get('nombre'),
            'colorimetria':     translate_season(season),
            'paleta':           colorimetry_result['palette'],
            'outfit_narrative': outfit_narrative,
            'outfit_simple':    outfit_simple,
            'outfit_items':     outfit_items,
            'outfit_source':    outfit_source,
            'clima':            f"{data.get('provincia')}, {data.get('mes')}",
            'temperatura':      clima_info.get('temperatura'),
            'prob_lluvia':      clima_info.get('prob_lluvia'),
            'ocasion':          translate_occasion(data.get('ocasion')),
            'preferencia':      data.get('fit'),
            'audio_url':        f"/static/audio/{audio_filename}" if audio_path else None,
            'confidence':       colorimetry_result.get('confidence', 0.85),
            'colorimetry_saved': saved_colorimetry is not None,
            'skin_analysis': {
                'undertone':   colorimetry_result.get('skin_tone'),
                'lightness':   colorimetry_result.get('skin_lightness'),
                'description': colorimetry_result.get('detailed_analysis', {}).get('skin', '')
            },
            'eye_analysis': {
                'category':    colorimetry_result.get('eye_color', {}).get('category', 'unknown'),
                'hue':         colorimetry_result.get('eye_color', {}).get('hue', 0),
                'description': colorimetry_result.get('detailed_analysis', {}).get('eyes', '')
            },
            'hair_analysis': {
                'category':    colorimetry_result.get('hair_color', {}).get('category', 'unknown'),
                'hue':         colorimetry_result.get('hair_color', {}).get('hue', 0),
                'description': colorimetry_result.get('detailed_analysis', {}).get('hair', '')
            },
            'detailed_explanation': colorimetry_result.get('detailed_analysis', {})
        }

        save_to_history(user_email, result)
        session['last_result'] = result
        return jsonify(result)

    except Exception as e:
        print(f"ERROR in onboarding: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

def translate_garment_name(name):
    """Translate a Spanish garment name to English word by word."""
    if not name:
        return name
    translations = {
        'camiseta': 't-shirt', 'camisa': 'shirt', 'blusa': 'blouse',
        'jersey': 'jumper', 'sudadera': 'sweatshirt', 'blazer': 'blazer',
        'chaqueta': 'jacket', 'abrigo': 'coat', 'chaleco': 'vest',
        'top': 'top', 'traje': 'suit', 'pantalon': 'trousers',
        'vaqueros': 'jeans', 'falda': 'skirt', 'shorts': 'shorts',
        'mallas': 'leggings', 'leggings': 'leggings', 'vestido': 'dress',
        'zapatillas': 'trainers', 'botas': 'boots', 'tacones': 'heels',
        'sandalias': 'sandals', 'mocasines': 'loafers', 'zapatos': 'shoes',
        'botines': 'ankle boots', 'alpargatas': 'espadrilles',
        'bolso': 'handbag', 'bolsa': 'bag', 'cinturón': 'belt',
        'bufanda': 'scarf', 'gorro': 'hat', 'sombrero': 'hat',
        'pañuelo': 'scarf', 'gafas': 'sunglasses', 'collar': 'necklace',
        'mochila': 'backpack', 'reloj': 'watch',
        'blanco': 'white', 'negro': 'black', 'gris': 'grey',
        'azul': 'blue', 'rojo': 'red', 'verde': 'green',
        'marron': 'brown', 'beige': 'beige', 'rosa': 'pink',
        'coral': 'coral', 'dorado': 'gold', 'marino': 'navy',
        'naranja': 'orange', 'amarillo': 'yellow', 'morado': 'purple',
        'oscuro': 'dark', 'claro': 'light', 'nude': 'nude',
        'bronce': 'bronze', 'lavanda': 'lavender', 'esmeralda': 'emerald',
        'turquesa': 'turquoise', 'plata': 'silver', 'acero': 'steel',
        'oliva': 'olive', 'blanca': 'white', 'negra': 'black',
        'roja': 'red', 'amarilla': 'yellow',
        'blancos': 'white', 'negros': 'black', 'grises': 'grey',
        'azules': 'blue', 'rojos': 'red', 'verdes': 'green',
        'marrones': 'brown', 'beiges': 'beige', 'rosas': 'pink',
        'corales': 'coral', 'dorados': 'gold', 'marinos': 'navy',
        'naranjas': 'orange', 'amarillos': 'yellow', 'morados': 'purple',
        'negras': 'black', 'blancas': 'white', 'rojas': 'red',
        'basica': 'basic', 'basico': 'basic', 'elegante': 'elegant',
        'deportivo': 'sports', 'deportiva': 'sports',
        'deportivos': 'sports', 'deportivas': 'sports',
        'formal': 'formal', 'formales': 'formal',
        'tecnica': 'technical', 'running': 'running', 'floral': 'floral',
        'lino': 'linen', 'oxford': 'oxford', 'pana': 'corduroy',
        'pastel': 'pastel', 'midi': 'midi', 'larga': 'long',
        'corta': 'short', 'clasico': 'classic',
        'verano': '', 'otoño': '', 'invierno': '', 'primavera': '',
        'de': '', 'sol': 'sun',
    }
    import unicodedata
    def strip_accents(s):
        return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    words = name.lower().split()
    result = []
    for w in words:
        t = translations.get(w) or translations.get(strip_accents(w), w)
        if t:
            result.append(t)
    return ' '.join(result).strip()

def translate_type(tipo):
    """Translate garment category key to English label."""
    return {
        'superior': 'Top', 'inferior': 'Bottom', 'vestido': 'Dress',
        'calzado': 'Footwear', 'complemento': 'Accessory'
    }.get(tipo, tipo.capitalize())

def translate_season(season):
    return {'Primavera': 'Spring', 'Verano': 'Summer',
            'Otono': 'Autumn', 'Invierno': 'Winter'}.get(season, season)

def translate_occasion(ocasion):
    return {'Formal': 'Formal', 'formal': 'Formal',
            'Casual': 'Casual', 'casual': 'Casual',
            'Deportiva': 'Sport', 'deportiva': 'Sport'}.get(ocasion, ocasion)

def generate_simple_outfit_text(outfit_items):
    """Generate a short English display string listing all selected garment names."""
    if not outfit_items:
        return "Could not generate outfit"

    parts = []
    if 'vestido' in outfit_items:
        parts.append(translate_garment_name(outfit_items['vestido'].get('nombre_corto', outfit_items['vestido'].get('nombre', 'dress'))))
    else:
        if 'superior' in outfit_items:
            parts.append(translate_garment_name(outfit_items['superior'].get('nombre_corto', outfit_items['superior'].get('nombre', 'top'))))
        if 'inferior' in outfit_items:
            parts.append(translate_garment_name(outfit_items['inferior'].get('nombre_corto', outfit_items['inferior'].get('nombre', 'bottom'))))
    if 'calzado' in outfit_items:
        parts.append(translate_garment_name(outfit_items['calzado'].get('nombre_corto', outfit_items['calzado'].get('nombre', 'footwear'))))
    if 'complemento' in outfit_items:
        parts.append(translate_garment_name(outfit_items['complemento'].get('nombre_corto', outfit_items['complemento'].get('nombre', 'accessory'))))

    return " + ".join(parts) if parts else "Personalised outfit"

# ========== WARDROBE API ==========

@app.route('/api/wardrobe/items', methods=['GET', 'POST'])
def wardrobe_items():
    """Get or add items to the user's virtual wardrobe."""
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    user_email = session['user']
    wardrobe   = WardrobeManager(user_email)

    if request.method == 'POST':
        try:
            if 'imagen' in request.files:
                photo = request.files['imagen']
                if photo.filename:
                    filename  = secure_filename(f"{user_email}_{datetime.now().timestamp()}_{photo.filename}")
                    photo_path = os.path.join('static/user_clothing', filename)
                    photo.save(photo_path)
                    item_data = request.form.to_dict()
                    item_data['imagen'] = filename
                else:
                    item_data = request.get_json()
            else:
                item_data = request.get_json()

            item_id = wardrobe.add_item(item_data)
            return jsonify({'success': True, 'item_id': item_id})
        except Exception as e:
            print(f"Error adding item: {e}")
            return jsonify({'success': False, 'message': str(e)}), 400
    else:
        items = wardrobe.get_all_items()
        return jsonify({'success': True, 'items': items})

@app.route('/api/wardrobe/items/<item_id>', methods=['DELETE'])
def delete_wardrobe_item(item_id):
    """Delete a garment from the user's wardrobe."""
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    wardrobe = WardrobeManager(session['user'])
    if wardrobe.delete_item(item_id):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Item not found'}), 404

@app.route('/api/wardrobe/stats')
def wardrobe_stats():
    """Return wardrobe statistics and suggestions."""
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    wardrobe    = WardrobeManager(session['user'])
    stats       = wardrobe.get_statistics()
    suggestions = wardrobe.suggest_missing_items()
    return jsonify({'success': True, 'stats': stats, 'suggestions': suggestions})

# ========== HISTORY API ==========

@app.route('/api/history')
def api_history():
    """Return the user's recommendation history."""
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    return jsonify({'success': True, 'history': get_user_history(session['user'])})

@app.route('/api/colorimetry')
def api_colorimetry():
    """Return the user's saved colorimetry result."""
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    colorimetry = get_user_colorimetry(session['user'])
    return jsonify({
        'success':         True,
        'has_colorimetry': colorimetry is not None,
        'colorimetry':     colorimetry
    })

# ========== HEALTH / STATS ROUTES ==========

@app.route('/api/health')
def health():
    """System health check endpoint."""
    return jsonify({
        'status':                 'ok',
        'colorimetry_ready':      colorimetry_analyzer is not None,
        'climate_data_ready':     load_climate_data() is not None,
        'outfit_generator_ready': outfit_generator is not None,
        'clothing_db_ready':      clothing_db is not None,
        'total_clothing_items':   sum(len(v) for v in clothing_db.items.values())
    })

@app.route('/api/dashboard/stats')
def dashboard_stats():
    """Return quick statistics for the user dashboard."""
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    user_email = session['user']
    history    = get_user_history(user_email)
    wardrobe   = WardrobeManager(user_email)
    colorimetry = get_user_colorimetry(user_email)

    return jsonify({
        'success': True,
        'stats': {
            'consultas': len(history),
            'prendas':   len(wardrobe.get_all_items()),
            'outfits':   sum(1 for h in history if h.get('result', {}).get('outfit_items')),
            'colores':   len(colorimetry.get('palette', [])) if colorimetry else 0
        }
    })

# ========== START SERVER ==========

if __name__ == '__main__':
    print("=" * 60)
    print("  SMART WARDROBE — Server v2.0")
    print("=" * 60)
    print("  Colorimetry analyser : ACTIVE")
    print("  Outfit generator     : ACTIVE")
    print("  Clothing database    : ACTIVE")
    print("  Authentication       : ACTIVE")
    print("  History system       : ACTIVE")
    print("  Saved colorimetry    : ACTIVE")

    if load_climate_data() is not None:
        print("  Climate data         : LOADED")
    else:
        print("  Climate data         : NOT AVAILABLE")

    print(f"  Total clothing items : {sum(len(v) for v in clothing_db.items.values())}")
    print("=" * 60)
    print("  Access at: http://localhost:5003")
    print("=" * 60)

    app.run(debug=True, port=5003)
