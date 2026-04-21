# PROJECT REPORT - SMART WARDROBE
**Author:** Lucía Nistal Palacios
**Course:** Intelligent Systems - Spring 2026
**University:** Universidad Intercontinental de la Empresa (UIE)
**Unit:** IV - Logical Agents and Knowledge-Based Systems
**Professor:** Yago Fontenla Seco

---

## 1. SUMMARY

Smart Wardrobe is a web-based outfit recommendation system built as a Knowledge-Based System (KBS), the core topic of Unit IV of the Intelligent Systems course. The system encodes expert fashion knowledge as logical rules, collects contextual facts from the user at query time, and applies a forward-chaining inference engine to produce personalised outfit recommendations.

The system additionally uses computer vision (OpenCV + K-means) to perform colourimetry analysis from a face photo, and historical climate data (Excel, 52 Spanish provinces) to adapt recommendations to the weather.

Technologies: Python, Flask, OpenCV, NumPy, scikit-learn, gTTS

---

## 2. ALIGNMENT WITH UNIT IV - KNOWLEDGE-BASED SYSTEMS

This project directly implements the three core components of a Rule-Based System as defined in the course slides:

### 2.1 Knowledge Base
The Knowledge Base encodes expert fashion and colourimetry rules in code:

- Occasion rules: each garment is tagged with the occasions it is suitable for (formal, casual, sport)
- Climate rules: garments are tagged with the climate conditions they suit (hot, mild, cold)
- Colourimetry rules: each season (Spring, Summer, Autumn, Winter) maps to a recommended colour palette
- Special rules:
  - If rain probability > 60%, prefer boots as footwear
  - If temperature < 10°C, prefer scarf or hat as accessory
  - If a dress is selected, do not search for a separate top or bottom
  - If the user marks dresses, skirts and tops as uncomfortable, filter out feminine footwear and accessories

### 2.2 Fact Base
The Fact Base is populated at query time from user input:

- Province and month → temperature and rain probability (from Excel data)
- Face photo → colourimetry season (Spring / Summer / Autumn / Winter)
- Occasion, fit preference, garments to avoid, gender

### 2.3 Inference Engine (Forward Chaining)
The inference engine follows a forward-chaining strategy: it starts from the known facts and fires rules until a complete outfit is reached. This maps directly to the CLIPS-style forward chaining described in the course.

Each candidate garment is scored against the current facts:

```
score = 0
if occasion matches:  score += 50   (mandatory - garment discarded if score < 50)
if climate matches:   score += 30
if season matches:    score += 20

if score >= 50: garment is selected
else:           fallback to generic database
```

The engine processes garment categories in order: dress → top → bottom → footwear → accessory, applying the relevant rules at each step.

This scoring approach evolved through three versions (see Section 8), moving from a simple exact-match rule to a weighted forward-chaining system that mirrors the inference algorithms studied in class.

### 2.4 Colourimetry as a Logical Classification Rule
The colourimetry analysis module also implements a rule-based classifier. Given the facts extracted from the photo (skin undertone, contrast, saturation), the following decision rules are applied:

```
IF warm AND (high or medium saturation) AND (light eyes or light hair) THEN Spring
IF warm AND low saturation AND dark features                           THEN Autumn
IF cool AND (high contrast OR high saturation)                        THEN Winter
IF cool AND low contrast AND low saturation                           THEN Summer
```

This is a direct application of propositional logic with modus ponens inference, as covered in the course.

---

## 3. CHANGES VS INITIAL PLAN

| Aspect | Initial | Final |
|--------|---------|-------|
| Flow | Welcome → Questionnaire → Results | Welcome → Login → Dashboard → Questionnaire/Wardrobe/History → Results |
| Authentication | NO | Login/Registration |
| Persistence | NO | Analysis cache + History |
| Personal wardrobe | NO | Full CRUD |
| Prioritisation | Generic DB only | User wardrobe first → DB fallback |
| Filtering | NO | Automatic by gender |

**Reason for changes:** Without a user system it would not be possible to save analyses or personalise recommendations.

---

## 4. PROBLEMS SOLVED

### 4.1 Colourimetry analysis
- RGB: Sensitive to lighting → CIELAB: Better colour separation
- Skin only: Imprecise → Skin + eyes + hair: Full contrast analysis

### 4.2 Database
- Excel averages covering 52 Spanish provinces by month

### 4.3 Garment matching
- Case-sensitive comparisons → `.lower()` normalisation
- Inconsistent JSON format → `normalize_field()` converts all values to arrays

### 4.4 Audio
- Incorrect grammatical articles → Article function produces correct output (e.g. "a white shirt")

### 4.5 Gender filtering
- Inappropriate garment suggestions → Automatic detection and filtering based on user preferences

---

## 5. PROJECT STRUCTURE

```
smart-wardrobe/
├── app.py                    # Flask server + KBS inference engine
├── colorimetry_analyzer.py   # OpenCV + K-means + CIELAB + season rules
├── clothing_database.py      # Generic clothing database (91 items)
├── outfit_generator.py       # Rule-based narrative generation + TTS
├── wardrobe_manager.py       # Virtual wardrobe CRUD
├── requirements.txt
│
├── data/
│   ├── clothing_items.json  # Generic database (fact base source)
│   ├── clima_provincias.xlsx # Climate data (fact base source)
│   ├── wardrobes/           # User wardrobes (fact base source)
│   ├── history/             # Query history
│   └── colorimetry/         # Cached colourimetry results
│
├── static/
│   ├── css/, js/
│   ├── clothing_images/     # Garment images
│   └── audio/               # Generated MP3s
│
└── templates/
    └── *.html               # 9 pages
```

---

## 6. EXECUTION INSTRUCTIONS

### Installation:
```bash
cd smart-wardrobe
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run:
```bash
python app.py
```
Open: `http://localhost:5003`

### Test credentials:
- Email: test@example.com
- Password: test123

### Photo requirements:
- Good lighting
- Neutral background
- Face clearly visible

---

## 7. KEY COMPONENTS

### 7.1 Colourimetry Analysis Pipeline
```
Photo → Face detection (Haar Cascade) → Extract ROIs (skin/eyes/hair)
      → K-means clustering → CIELAB undertone → Contrast + Saturation
      → Apply season classification rules → Spring / Summer / Autumn / Winter
```

### 7.2 KBS Inference Engine Flow
```
Facts: province + month → climate
       photo → colourimetry season
       user input → occasion, fit, exclusions

Rules applied in order:
  1. Dress rule (occasion: formal/casual only)
  2. Top rule
  3. Bottom rule (with skirt/trouser exclusion sub-rules)
  4. Footwear rule (rain threshold sub-rule)
  5. Accessory rule (cold threshold sub-rule)

Output: complete outfit + audio narrative
```

---

## 8. GARMENT SCORING ALGORITHM (Evolution)

### Version 1 (discarded):
```python
if prenda['ocasion'] == ocasion:
    return True
```
Problem: Did not consider climate or colourimetry.

### Version 2 (improved):
```python
if match_ocasion and match_clima and match_estacion:
    return True
```
Problem: Too restrictive — a garment was discarded if any single condition failed.

### Version 3 (current - forward chaining with weighted scoring):
```python
score = 0
if match_ocasion:  score += 50    # mandatory
if match_clima:    score += 30
if match_estacion: score += 20
return score >= 50
```
This version mirrors the forward-chaining algorithm from the course: facts are evaluated against rules, each contributing to a score, and a conclusion is reached when the minimum threshold is met. If no garment in the user wardrobe reaches the threshold, the system fires the fallback rule and consults the generic database.

---

## 9. LIMITATIONS

1. Analysis: Sensitive to extreme lighting conditions
2. Climate: Historical averages, not real-time data
3. Database: 91 generic items (user can expand via virtual wardrobe)
4. Photo: Single face only
5. Rules: The knowledge base was defined manually — it does not learn from data

---

## 10. CONCLUSION

Smart Wardrobe implements a complete Knowledge-Based System as studied in Unit IV of the Intelligent Systems course. The system has a clearly defined Knowledge Base (fashion and colourimetry rules), a Fact Base (user input and climate data), and an Inference Engine that applies forward chaining to produce a recommendation.

The colourimetry classifier is itself a rule-based logical agent that applies modus ponens over propositional facts extracted from the face photo. The outfit selection engine evolved from a simple exact-match rule to a weighted scoring system that reflects the forward-chaining mechanism covered in class.

Main achievements:
- Complete KBS implementation aligned with Unit IV content
- Scientifically grounded colourimetry analysis using CIELAB and K-means
- Intelligent user/database prioritisation via forward-chaining inference
- Gender filtering rules and inclusivity
- Grammatically correct audio output
- Intuitive web interface