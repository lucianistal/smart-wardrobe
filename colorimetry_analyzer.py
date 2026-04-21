import cv2
import numpy as np
from sklearn.cluster import KMeans

class ColorimetryAnalyzer:
    """
    Colorimetry analyser using computer vision.

    Pipeline:
      1. Illumination normalisation (CLAHE in CIELAB space)
      2. Face detection (Haar Cascade)
      3. Skin-tone analysis  — CIELAB subtone (warm / cool / neutral)
      4. Eye-colour analysis — HSV + K-means clustering on iris ROI
      5. Hair-colour analysis — HSV + K-means on hair region above face
      6. Contrast and saturation calculation
      7. Season classification — forward-chaining decision rules

    Decision rules (Knowledge Base):
        Warm + light / medium saturation           → Spring
        Warm + deep / low saturation               → Autumn
        Cool + high contrast or high saturation    → Winter
        Cool + low contrast and low saturation     → Summer
    """

    def __init__(self):
        cascade_path     = cv2.data.haarcascades
        self.face_cascade = cv2.CascadeClassifier(cascade_path + 'haarcascade_frontalface_default.xml')
        self.eye_cascade  = cv2.CascadeClassifier(cascade_path + 'haarcascade_eye.xml')

        # Knowledge Base — recommended colour palettes per season (hex codes + text names)
        self.palettes = {
            "Primavera": {
                "colores": [
                    "#FFD700", "#FF6347", "#90EE90", "#FFB6C1",
                    "#FFDAB9", "#98FB98", "#F0E68C", "#FFA07A"
                ],
                "descripcion": "Warm and vibrant tones (golden yellow, coral orange, light green, light pink)",
                "colores_texto": ["golden yellow", "coral orange", "light green", "light pink", "peach", "mint green"]
            },
            "Verano": {
                "colores": [
                    "#B0E0E6", "#FFB6C1", "#F5DEB3", "#E6E6FA",
                    "#AFEEEE", "#FFFACD", "#D8BFD8", "#B2DFDB"
                ],
                "descripcion": "Soft and cool tones (powder blue, pastel pink, lavender, aqua green)",
                "colores_texto": ["powder blue", "pastel pink", "nude beige", "lavender", "light turquoise", "aqua green"]
            },
            "Otono": {
                "colores": [
                    "#8B4513", "#FF8C00", "#556B2F", "#F5DEB3",
                    "#CD853F", "#A0522D", "#DC143C", "#B8860B"
                ],
                "descripcion": "Earthy and warm tones (brown, orange, olive green, warm beige, red, bronze)",
                "colores_texto": ["brown", "orange", "olive green", "warm beige", "red", "bronze"]
            },
            "Invierno": {
                "colores": [
                    "#000000", "#FFFFFF", "#C0C0C0", "#000080",
                    "#4682B4", "#2E8B57", "#696969", "#191970"
                ],
                "descripcion": "Cool and intense tones (black, white, silver grey, navy, steel blue, emerald)",
                "colores_texto": ["black", "white", "grey", "navy blue", "steel blue", "emerald"]
            }
        }

    def analyze_image(self, image_path):
        """Run the full colorimetry analysis pipeline on a face photo."""
        try:
            print(f"Loading image: {image_path}")
            img = cv2.imread(image_path)
            if img is None:
                print("Could not load image.")
                return self._get_default_result()

            # Step 1 — Illumination normalisation
            print("Normalising illumination...")
            img = self._normalize_illumination(img)

            gray  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) == 0:
                print("No face detected.")
                return self._get_default_result()

            print(f"Face detected ({len(faces)} face(s))")
            (x, y, w, h) = faces[0]
            face_roi  = img[y:y+h, x:x+w]
            gray_face = gray[y:y+h, x:x+w]

            # Step 2 — Skin tone
            print("Analysing skin tone...")
            skin_tone, skin_lightness, skin_lab = self._analyze_skin_tone_cielab(face_roi)
            print(f"   Skin: {skin_tone} (L={int(skin_lightness)})")

            # Step 3 — Eye colour
            print("Analysing eye colour...")
            eye_analysis  = self._analyze_eye_color(face_roi, gray_face)
            eye_category  = self._categorize_eye_color(eye_analysis)
            print(f"   Eyes: {eye_category}")

            # Step 4 — Hair colour
            print("Analysing hair colour...")
            hair_color    = self._analyze_hair_color(img, (x, y, w, h))
            hair_category = self._categorize_hair_color(hair_color)
            print(f"   Hair: {hair_category}")

            # Step 5 — Contrast and saturation
            print("Calculating contrast and saturation...")
            contrast   = self._calculate_contrast(skin_lightness, eye_analysis, hair_color)
            saturation = self._calculate_saturation(eye_analysis, hair_color)
            print(f"   Contrast: {contrast}, Saturation: {saturation}")

            # Step 6 — Season classification (KBS decision rules)
            print("Classifying season...")
            season = self._classify_season(skin_tone, eye_analysis, hair_color, contrast, saturation)
            print(f"Result: {season}")

            return {
                'season':          season,
                'skin_tone':       skin_tone,
                'skin_lightness':  int(skin_lightness),
                'skin_lab':        {'L': int(skin_lab[0]), 'a': int(skin_lab[1]), 'b': int(skin_lab[2])},
                'eye_color': {
                    'category':   eye_category,
                    'hue':        eye_analysis['hue'],
                    'saturation': eye_analysis['saturation'],
                    'value':      eye_analysis['value']
                },
                'hair_color': {
                    'category':   hair_category,
                    'hue':        hair_color['hue'],
                    'saturation': hair_color['saturation'],
                    'value':      hair_color['value']
                },
                'contrast':           contrast,
                'saturation':         saturation,
                'palette':            self.palettes[season]['colores'],
                'palette_description':self.palettes[season]['descripcion'],
                'palette_names':      self.palettes[season]['colores_texto'],
                'confidence':         0.90,
                'detailed_analysis': {
                    'skin':       f"Undertone: {skin_tone}",
                    'eyes':       f"Eyes: {eye_category}",
                    'hair':       f"Hair: {hair_category}",
                    'conclusion': f"Season: {season}"
                }
            }

        except Exception as e:
            print(f"Critical error in colorimetry analysis: {e}")
            import traceback
            traceback.print_exc()
            return self._get_default_result()

    def _normalize_illumination(self, img):
        """Apply CLAHE normalisation in CIELAB space to reduce lighting variability."""
        lab     = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe   = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l       = clahe.apply(l)
        return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)

    def _analyze_skin_tone_cielab(self, face_roi):
        """
        Analyse skin undertone using CIELAB colour space.
        The 'b' channel (yellow–blue axis) determines warmth:
          b > 5  → warm undertone
          b < -5 → cool undertone
          else   → neutral
        """
        h, w = face_roi.shape[:2]

        # Sample three skin ROIs: forehead, left cheek, right cheek
        forehead    = face_roi[int(h*0.15):int(h*0.35), int(w*0.25):int(w*0.75)]
        left_cheek  = face_roi[int(h*0.45):int(h*0.65), int(w*0.1):int(w*0.4)]
        right_cheek = face_roi[int(h*0.45):int(h*0.65), int(w*0.6):int(w*0.9)]

        skin_pixels = []
        for region in [forehead, left_cheek, right_cheek]:
            if region.size > 0:
                lab    = cv2.cvtColor(region, cv2.COLOR_BGR2LAB)
                pixels = lab.reshape(-1, 3)
                mask   = (pixels[:, 0] > 50) & (pixels[:, 0] < 220)
                skin_pixels.extend(pixels[mask])

        skin_pixels = np.array(skin_pixels)
        if len(skin_pixels) < 10:
            return 'warm', 150, np.array([150, 128, 135])

        mean_l = np.mean(skin_pixels[:, 0])
        mean_a = np.mean(skin_pixels[:, 1])
        mean_b = np.mean(skin_pixels[:, 2])

        # Warmth rule: CIELAB b* axis (128 = neutral midpoint)
        warmth = mean_b - 128
        if warmth > 5:
            undertone = 'warm'
        elif warmth < -5:
            undertone = 'cool'
        else:
            undertone = 'neutral'

        return undertone, mean_l, np.array([mean_l, mean_a, mean_b])

    def _analyze_eye_color(self, face_roi, face_gray):
        """Detect the dominant iris colour using K-means clustering on the eye ROI."""
        eyes = self.eye_cascade.detectMultiScale(face_gray, 1.05, 8, minSize=(30, 30))
        if len(eyes) == 0:
            return {'hue': 90, 'saturation': 60, 'value': 100, 'brightness': 100}

        eyes = sorted(eyes, key=lambda e: e[2]*e[3], reverse=True)
        (ex, ey, ew, eh) = eyes[0]
        eye_roi = face_roi[ey:ey+eh, ex:ex+ew]
        if eye_roi.size == 0:
            return {'hue': 90, 'saturation': 60, 'value': 100, 'brightness': 100}

        hsv    = cv2.cvtColor(eye_roi, cv2.COLOR_BGR2HSV)
        h, w   = eye_roi.shape[:2]
        center = hsv[int(h*0.3):int(h*0.7), int(w*0.3):int(w*0.7)]
        pixels = center.reshape(-1, 3)
        valid  = pixels[(pixels[:, 2] > 50) & (pixels[:, 2] < 220)]

        if len(valid) < 20:
            return {'hue': 90, 'saturation': 60, 'value': 100, 'brightness': 100}

        kmeans   = KMeans(n_clusters=2, random_state=42, n_init=10)
        kmeans.fit(valid)
        dominant = kmeans.cluster_centers_[np.argmax(np.bincount(kmeans.labels_))]

        return {
            'hue':        int(dominant[0]),
            'saturation': int(dominant[1]),
            'value':      int(dominant[2]),
            'brightness': int(np.mean(valid[:, 2]))
        }

    def _categorize_eye_color(self, eye_data):
        """Classify eye colour into a descriptive category."""
        h, s, v = eye_data['hue'], eye_data['saturation'], eye_data['value']
        if v < 70:
            return 'dark brown'
        elif h < 20 or h > 160:
            return 'brown' if s > 50 else 'amber'
        elif 20 <= h <= 80:
            return 'green' if s > 60 else 'hazel'
        else:
            return 'blue' if s > 50 else 'grey'

    def _analyze_hair_color(self, img, face_coords):
        """Extract the dominant hair colour from the region above the detected face."""
        x, y, w, h  = face_coords
        hair_top    = max(0, y - int(h * 0.6))
        hair_roi    = img[hair_top:y, max(0, x-int(w*0.1)):min(img.shape[1], x+w+int(w*0.1))]

        if hair_roi.size == 0:
            return {'hue': 15, 'saturation': 60, 'value': 80}

        hsv        = cv2.cvtColor(hair_roi, cv2.COLOR_BGR2HSV)
        lower_skin = np.array([0, 15, 60])
        upper_skin = np.array([30, 170, 255])
        mask_skin  = cv2.inRange(hsv, lower_skin, upper_skin)
        mask_hair  = cv2.bitwise_not(mask_skin)

        hair_pixels = hsv[mask_hair > 0]
        hair_pixels = hair_pixels[hair_pixels[:, 2] > 25]

        if len(hair_pixels) < 100:
            return {'hue': 15, 'saturation': 60, 'value': 80}

        kmeans   = KMeans(n_clusters=2, random_state=42, n_init=10)
        kmeans.fit(hair_pixels)
        dominant = kmeans.cluster_centers_[np.argmax(np.bincount(kmeans.labels_))]

        return {
            'hue':        int(dominant[0]),
            'saturation': int(dominant[1]),
            'value':      int(dominant[2])
        }

    def _categorize_hair_color(self, hair_data):
        """Classify hair colour into a descriptive category."""
        v, h, s = hair_data['value'], hair_data['hue'], hair_data['saturation']
        if v < 40:
            return 'black'
        elif v < 70:
            return 'dark brown'
        elif v < 100:
            return 'brown'
        elif h <= 25 and s > 70:
            return 'red'
        elif v > 140:
            return 'blonde'
        else:
            return 'light brown'

    def _calculate_contrast(self, skin_l, eye_data, hair_data):
        """
        Calculate overall contrast between skin, eyes and hair lightness.
        high   : average difference > 80
        medium : average difference > 45
        low    : average difference <= 45
        """
        diffs = [
            abs(skin_l - eye_data['value']),
            abs(skin_l - hair_data['value']),
            abs(eye_data['value'] - hair_data['value'])
        ]
        avg = np.mean(diffs)
        return 'high' if avg > 80 else 'medium' if avg > 45 else 'low'

    def _calculate_saturation(self, eye_data, hair_data):
        """
        Calculate average colour saturation from eyes and hair.
        high   : average saturation > 110
        medium : average saturation > 65
        low    : average saturation <= 65
        """
        avg = (eye_data['saturation'] + hair_data['saturation']) / 2
        return 'high' if avg > 110 else 'medium' if avg > 65 else 'low'

    def _classify_season(self, skin, eye, hair, contrast, saturation):
        """
        KBS classification rule — forward chaining over four facts:
          skin undertone, eye warmth, hair warmth, contrast, saturation.

        Rules:
          IF warm (score >= 2/3) AND (saturation high/medium OR light eyes/hair)
              THEN Spring
          IF warm (score >= 2/3) AND saturation low AND dark
              THEN Autumn
          IF cool AND (contrast high OR saturation high)
              THEN Winter
          IF cool AND contrast low AND saturation low
              THEN Summer
        """
        eye_warm  = (eye['hue'] < 40 or eye['hue'] > 150)
        hair_warm = (hair['hue'] < 50 or hair['hue'] > 330)
        eye_light  = eye['value'] > 110
        hair_light = hair['value'] > 110

        warmth_score = sum([skin == 'warm', eye_warm, hair_warm])
        is_warm      = warmth_score >= 2

        if is_warm:
            if saturation in ['high', 'medium'] and (eye_light or hair_light):
                return "Primavera"
            else:
                return "Otono"
        else:
            if contrast == 'high' or saturation == 'high':
                return "Invierno"
            else:
                return "Verano"

    def _get_default_result(self):
        """Return a default Spring result when face detection fails."""
        return {
            'season':          "Primavera",
            'skin_tone':       'warm',
            'skin_lightness':  150,
            'skin_lab':        {'L': 150, 'a': 128, 'b': 135},
            'eye_color':       {'category': 'brown',  'hue': 20,  'saturation': 70, 'value': 100},
            'hair_color':      {'category': 'brown',  'hue': 15,  'saturation': 60, 'value': 80},
            'contrast':        'medium',
            'saturation':      'medium',
            'palette':         self.palettes["Primavera"]['colores'],
            'palette_description': self.palettes["Primavera"]['descripcion'],
            'palette_names':   self.palettes["Primavera"]['colores_texto'],
            'confidence':      0.50,
            'detailed_analysis': {
                'conclusion': 'Default result — no face detected'
            }
        }