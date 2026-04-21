# Smart Wardrobe - Intelligent Outfit Recommendation System

A web application that analyses your personal colourimetry from a photo and recommends outfits adapted to the weather and your preferences.

---

## What does it do?

1. Analyses your photo - Detects your skin tone, eye colour and hair colour
2. Determines your colourimetry - Classifies you as Spring, Summer, Autumn or Winter
3. Recommends outfits - Suggests garments based on climate, occasion and your flattering colours
4. Explains it by voice - Generates audio describing the recommended outfit

---

## Quick Installation

### 1. Requirements
See `requirements.txt`

### 2. Install

```bash
# Clone the repository
git clone https://github.com/lucianistal/armario-inteligente.git
cd armario-inteligente

# Create virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create required directories
mkdir -p data/wardrobes data/history data/colorimetry
mkdir -p static/audio static/user_clothing
```

### 3. Run

```bash
python3 app.py
```

Open your browser at: `http://localhost:5003`

---

## Project Structure

```
smart-wardrobe/
├── app.py                      # Flask server + KBS inference engine
├── colorimetry_analyzer.py     # Colourimetry analysis (OpenCV + K-means + CIELAB)
├── clothing_database.py        # Generic clothing database (91 items)
├── outfit_generator.py         # Rule-based outfit generation + TTS audio
├── wardrobe_manager.py         # Virtual wardrobe CRUD
├── requirements.txt
│
├── data/
│   ├── clothing_items.json    # ~91 clothing items
│   ├── clima_provincias.xlsx  # Historical climate data (52 Spanish provinces)
│   └── wardrobes/             # Per-user wardrobe files
│
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   ├── clothing_images/       # Garment images
│   └── audio/                 # Generated audio files
│
└── templates/
    └── *.html                 # 9 pages
```

---

## How It Works

### Colourimetry Analysis

The system analyses three facial features:

1. Skin tone - Uses CIELAB colour space to detect warm or cool undertone
2. Eye colour - Classified using K-means clustering on the iris region
3. Hair colour - Determines blonde, brown, black or red

With this information it calculates:
- Contrast: Difference in lightness between skin and hair
- Saturation: Intensity of eye and hair colours

And classifies you into a season:

| Season | Characteristics |
|--------|----------------|
| Spring  | Warm + low contrast + high saturation |
| Summer  | Cool + low contrast + low saturation  |
| Autumn  | Warm + high contrast + low saturation |
| Winter  | Cool + high contrast + high saturation |

### KBS Outfit Generation (Forward Chaining)

The inference engine applies rules in the following order:

1. Searches your virtual wardrobe first (priority)
2. Scores each candidate garment: occasion (+50 pts) + climate (+30 pts) + season (+20 pts)
3. A garment is selected only if score >= 50 (occasion is mandatory)
4. If no user garment qualifies, falls back to the generic database
5. Applies gender filter rules and special climate rules (rain / cold)
6. Generates narrative and converts it to audio

---

## Technologies

| Technology | Purpose |
|---|---|
| Python 3.8+ | Main language |
| Flask | Web server |
| OpenCV | Image analysis |
| NumPy | Numerical processing |
| scikit-learn | K-means clustering |
| gTTS | Text-to-speech |
| pandas | Climate data |

---

## Basic Usage

### 1. Register
Create an account with your email and password.

### 2. Questionnaire (8 steps)
- Name and gender
- Province and month
- Occasion (formal / casual / sport)
- Fit preference
- Garments to avoid
- Face photo
- Confirm

### 3. View Results
- Personalised colour palette
- Recommended outfit with images
- Voice explanation
- Analysis details

### 4. Virtual Wardrobe (optional)
- Add your own garments
- The system will prioritise them in future recommendations

---

## Academic Context

Course: Intelligent Systems - Spring 2026
University: Universidad Intercontinental de la Empresa (UIE)
Unit: IV - Logical Agents and Knowledge-Based Systems
Professor: Yago Fontenla Seco 