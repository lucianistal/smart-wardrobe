import random

class OutfitGenerator:
    """
    Outfit generator using a rule-based Knowledge-Based System (KBS).

    Knowledge Base: Fashion rules encoded in intros_audio, colour explanations,
                    fit advice, and rain/temperature thresholds.
    Fact Base:      Per-request user data (occasion, climate, colorimetry season,
                    fit preference) passed into generate_outfit_complete().
    Inference Engine: Forward-chaining scoring — occasion match (+50 pts),
                      climate match (+30 pts), colorimetry season match (+20 pts).
                      A garment is selected only if score >= 50 (occasion is mandatory).
                      If no garment in the user wardrobe reaches the threshold,
                      the system falls back to the generic clothing database.

    Outputs:
        - outfit_simple:    Short text listing selected garments (shown with images).
        - outfit_narrative: Detailed narrative for text-to-speech audio.
    Both outputs are always synchronised — they describe the same garments.
    """

    # Translation dictionary: Spanish garment/colour names → English
    TRANSLATIONS = {
        'camiseta': 't-shirt', 'camisa': 'shirt', 'blusa': 'blouse',
        'jersey': 'jumper', 'sudadera': 'sweatshirt', 'blazer': 'blazer',
        'chaqueta': 'jacket', 'abrigo': 'coat', 'chaleco': 'vest',
        'top': 'top', 'traje': 'suit', 'pantalon': 'trousers',
        'vaqueros': 'jeans', 'falda': 'skirt', 'shorts': 'shorts',
        'mallas': 'leggings', 'leggings': 'leggings', 'vestido': 'dress',
        'zapatillas': 'trainers', 'botas': 'boots', 'tacones': 'heels',
        'sandalias': 'sandals', 'mocasines': 'loafers', 'zapatos': 'shoes',
        'botines': 'ankle boots', 'alpargatas': 'espadrilles',
        'bolso': 'handbag', 'bolsa': 'bag', 'cinturon': 'belt',
        'bufanda': 'scarf', 'panuelo': 'scarf', 'gorro': 'hat',
        'sombrero': 'hat', 'gafas': 'sunglasses', 'collar': 'necklace',
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
        'corta': 'short', 'clasico': 'classic', 'plateado': 'silver',
        'verano': '', 'otono': '', 'invierno': '', 'primavera': '',
        'de': '', 'sol': 'sun',
    }

    def _translate_name(self, name):
        """Translate a Spanish garment name to English word by word."""
        if not name:
            return name
        import unicodedata
        def strip_accents(s):
            return ''.join(c for c in unicodedata.normalize('NFD', s)
                           if unicodedata.category(c) != 'Mn')
        words = name.lower().split()
        result = []
        for w in words:
            t = self.TRANSLATIONS.get(w) or self.TRANSLATIONS.get(strip_accents(w), w)
            if t:
                result.append(t)
        return ' '.join(result).strip()


    def __init__(self):
        # Knowledge Base: introductory phrases per occasion (used in audio narrative)
        self.intros_audio = {
            'formal': [
                "For your formal event, here is an elegant look:",
                "To look impeccable on this formal occasion:",
                "A sophisticated outfit perfectly suited for you:"
            ],
            'casual': [
                "For your everyday look, here is a comfortable yet stylish suggestion:",
                "To stay relaxed and on trend:",
                "My casual recommendation for you is:"
            ],
            'deportiva': [
                "For your sports activity, the ideal outfit is:",
                "To stay active in comfort:",
                "A perfect set for your workout:"
            ]
        }

        # Knowledge Base: colorimetry season explanations
        self.colour_explanations = {
            'Primavera': "As a Spring type, warm and vibrant tones brighten your complexion.",
            'Verano':    "Your Summer colouring works best with soft, cool tones that harmonise with your rosy undertone.",
            'Otono':     "As an Autumn type, earthy and warm tones enhance your natural warmth.",
            'Invierno':  "Your Winter colouring shines with intense, cool colours that highlight your natural contrast."
        }

    # =========================
    # ENSURE COMPLETE OUTFIT
    # =========================
    def ensure_complete_outfit(self, outfit_items, gender='mujer'):
        """
        Inference rule: every outfit must have at minimum a top (or dress),
        a bottom (unless a dress is present), and footwear.
        If any mandatory category is missing, a neutral fallback garment is added.
        """
        is_woman = 'mujer' in gender.lower()

        if 'vestido' not in outfit_items and 'superior' not in outfit_items:
            outfit_items['superior'] = {
                'nombre': 'basic blouse' if is_woman else 'basic shirt',
                'nombre_corto': 'blouse' if is_woman else 'shirt',
                'color': 'white'
            }

        if 'vestido' not in outfit_items and 'inferior' not in outfit_items:
            outfit_items['inferior'] = {
                'nombre': 'black skirt' if is_woman else 'black trousers',
                'nombre_corto': 'skirt' if is_woman else 'trousers',
                'color': 'black'
            }

        if 'calzado' not in outfit_items:
            outfit_items['calzado'] = {
                'nombre': 'heels' if is_woman else 'trainers',
                'nombre_corto': 'heels' if is_woman else 'trainers',
                'color': 'white'
            }

        return outfit_items

    # =========================
    # ARTICLE HELPER
    # =========================
    def _get_garment_description(self, garment, gender='mujer'):
        """Returns a grammatically correct article + garment name in English."""
        if isinstance(garment, dict):
            raw_name = garment.get('nombre_corto') or garment.get('nombre', 'garment')
            name = self._translate_name(raw_name)
            first_word = name.split()[0].lower()
            plural_words = ['sandals', 'boots', 'trainers', 'heels', 'loafers', 'shoes',
                            'jeans', 'leggings', 'trousers', 'glasses', 'shorts', 'tights']
            if first_word in plural_words or (first_word.endswith('s') and first_word not in ['dress', 'blouse']):
                article = 'some'
            else:
                article = 'an' if name[0].lower() in ('a','e','i','o','u') else 'a'
            return f"{article} {name}"
        return "a garment"

    # =========================
    # MAIN ENTRY POINT
    # =========================
    def generate_outfit_complete(self, user_data, clima_info, colorimetry_result, outfit_items):
        """Main KBS inference method."""
        outfit_items = self.ensure_complete_outfit(outfit_items, user_data.get('genero', 'mujer'))
        outfit_simple    = self._generate_outfit_simple(outfit_items, user_data.get('genero', 'mujer'))
        outfit_narrative = self._generate_outfit_narrative(
            outfit_items=outfit_items,
            user_data=user_data,
            clima_info=clima_info,
            colorimetry_result=colorimetry_result
        )
        return {
            'outfit_simple':    outfit_simple,
            'outfit_narrative': outfit_narrative,
            'outfit_items':     outfit_items
        }

    # =========================
    # OUTFIT SIMPLE TEXT
    # =========================
    def _generate_outfit_simple(self, outfit_items, gender='mujer'):
        if not outfit_items:
            return "Personalised outfit"
        parts = []
        if 'vestido' in outfit_items:
            parts.append(self._get_garment_description(outfit_items['vestido'], gender))
        else:
            if 'superior' in outfit_items:
                parts.append(self._get_garment_description(outfit_items['superior'], gender))
            if 'inferior' in outfit_items:
                parts.append(self._get_garment_description(outfit_items['inferior'], gender))
        if 'calzado' in outfit_items:
            parts.append(self._get_garment_description(outfit_items['calzado'], gender))
        if 'complemento' in outfit_items:
            parts.append(self._get_garment_description(outfit_items['complemento'], gender))
        return " + ".join(parts) if parts else "Personalised outfit"

    def _get_item_short_name(self, item):
        if isinstance(item, dict):
            raw = item.get('nombre_corto') or item.get('nombre', 'garment')
            name = self._translate_name(raw)
            return " ".join(name.lower().split()[:3])
        return str(item).lower()

    # =========================
    # OUTFIT NARRATIVE (audio)
    # =========================
    def _generate_outfit_narrative(self, outfit_items, user_data, clima_info, colorimetry_result):
        """
        Generates the audio narrative by applying KBS rules in sequence:
          1. Occasion rule  — selects the introductory phrase.
          2. Climate rules  — adds temperature context and rain warning (threshold > 60%).
          3. Colorimetry rule — appends palette explanation based on detected season.
          4. Fit rule       — appends style advice based on fit preference.
        """
        ocasion       = user_data.get('ocasion', 'casual').lower()
        temperatura   = clima_info.get('temperatura', 20)
        prob_lluvia   = clima_info.get('prob_lluvia', 30)
        season        = colorimetry_result.get('season', 'Primavera')
        nombre        = user_data.get('nombre', 'there')
        fit           = user_data.get('fit', 'Normal').lower()
        gender        = user_data.get('genero', 'mujer')
        palette_names = colorimetry_result.get('palette_names', [])

        # Climate category rule
        if temperatura > 25:
            temp_desc = 'this warm day'
        elif temperatura > 15:
            temp_desc = 'this mild weather'
        else:
            temp_desc = 'this cold day'

        narrative  = f"Hello {nombre}. "
        narrative += random.choice(self.intros_audio.get(ocasion, self.intros_audio['casual'])) + "\n\n"

        if 'vestido' in outfit_items:
            narrative += f"I suggest {self._get_garment_description(outfit_items['vestido'], gender)}. "
        else:
            if 'superior' in outfit_items:
                narrative += f"Pair {self._get_garment_description(outfit_items['superior'], gender)} "
            if 'inferior' in outfit_items:
                narrative += f"with {self._get_garment_description(outfit_items['inferior'], gender)}. "

        if 'calzado' in outfit_items:
            narrative += f"Complete the look with {self._get_garment_description(outfit_items['calzado'], gender)}. "
        if 'complemento' in outfit_items:
            narrative += f"Don't forget {self._get_garment_description(outfit_items['complemento'], gender)}. "

        narrative += f"\n\nThis outfit is perfect for {temp_desc}. "

        # Rain threshold rule (Knowledge Base rule)
        if prob_lluvia > 60:
            narrative += f"Important: there is a {prob_lluvia}% chance of rain — bring an umbrella. "
        elif prob_lluvia > 30:
            narrative += f"Consider bringing an umbrella, there is a {prob_lluvia}% chance of rain. "

        # Colorimetry palette rule
        if palette_names:
            colours_text = ", ".join(palette_names[:3])
            narrative += f"\n\n{self.colour_explanations.get(season, '')} "
            narrative += f"Go for colours like {colours_text}. "

        # Fit preference rule
        fit_texts = {
            'ajustada': "Since you prefer a fitted cut, look for garments that define your silhouette without sacrificing comfort.",
            'holgada':  "Since you prefer loose clothing, opt for oversized pieces that give you freedom of movement.",
            'normal':   "A regular fit will let you play with different styles."
        }
        narrative += fit_texts.get(fit, "")

        return narrative

    # =========================
    # GENERIC OUTFIT FALLBACK
    # =========================
    def generate_generic_outfit(self, ocasion, temp_cat, genero, fit,
                                 no_v=None, no_f=None, no_t=None, no_p=None):
        """
        KBS fallback rule: if the user wardrobe contains no garment scoring >= 50,
        return a predefined generic outfit based on occasion, temperature and gender.
        """
        gender_key = 'mujer' if 'mujer' in genero.lower() else 'hombre'

        generic_outfits = {
            'casual': {
                'mujer': {
                    'calor':    {'superior': {'nombre': 'light top',    'nombre_corto': 'light top',  'color': 'white'},
                                 'inferior': {'nombre': 'shorts',        'nombre_corto': 'shorts',     'color': 'blue'},
                                 'calzado':  {'nombre': 'sandals',       'nombre_corto': 'sandals',    'color': 'beige'}},
                    'templado': {'superior': {'nombre': 'light jumper',  'nombre_corto': 'jumper',     'color': 'grey'},
                                 'inferior': {'nombre': 'jeans',         'nombre_corto': 'jeans',      'color': 'blue'},
                                 'calzado':  {'nombre': 'white trainers','nombre_corto': 'trainers',   'color': 'white'}},
                    'frio':     {'superior': {'nombre': 'thick sweater', 'nombre_corto': 'sweater',    'color': 'black'},
                                 'inferior': {'nombre': 'cord trousers', 'nombre_corto': 'trousers',   'color': 'brown'},
                                 'calzado':  {'nombre': 'boots',         'nombre_corto': 'boots',      'color': 'black'}}
                },
                'hombre': {
                    'calor':    {'superior': {'nombre': 'basic t-shirt', 'nombre_corto': 't-shirt',   'color': 'white'},
                                 'inferior': {'nombre': 'shorts',        'nombre_corto': 'shorts',    'color': 'beige'},
                                 'calzado':  {'nombre': 'trainers',      'nombre_corto': 'trainers',  'color': 'white'}},
                    'templado': {'superior': {'nombre': 't-shirt',       'nombre_corto': 't-shirt',   'color': 'grey'},
                                 'inferior': {'nombre': 'jeans',         'nombre_corto': 'jeans',     'color': 'blue'},
                                 'calzado':  {'nombre': 'trainers',      'nombre_corto': 'trainers',  'color': 'white'}},
                    'frio':     {'superior': {'nombre': 'jumper',        'nombre_corto': 'jumper',    'color': 'black'},
                                 'inferior': {'nombre': 'jeans',         'nombre_corto': 'jeans',     'color': 'dark blue'},
                                 'calzado':  {'nombre': 'boots',         'nombre_corto': 'boots',     'color': 'brown'}}
                }
            },
            'formal': {
                'mujer': {
                    'calor':    {'vestido':  {'nombre': 'elegant midi dress',   'nombre_corto': 'midi dress', 'color': 'blue'},
                                 'calzado':  {'nombre': 'heels',                'nombre_corto': 'heels',      'color': 'beige'}},
                    'templado': {'superior': {'nombre': 'blazer',               'nombre_corto': 'blazer',     'color': 'black'},
                                 'inferior': {'nombre': 'dress trousers',       'nombre_corto': 'trousers',   'color': 'black'},
                                 'calzado':  {'nombre': 'heels',                'nombre_corto': 'heels',      'color': 'black'}},
                    'frio':     {'superior': {'nombre': 'tailored suit jacket', 'nombre_corto': 'jacket',     'color': 'grey'},
                                 'inferior': {'nombre': 'dress trousers',       'nombre_corto': 'trousers',   'color': 'grey'},
                                 'calzado':  {'nombre': 'heeled boots',         'nombre_corto': 'boots',      'color': 'black'}}
                },
                'hombre': {
                    'calor':    {'superior': {'nombre': 'linen shirt',    'nombre_corto': 'shirt',    'color': 'white'},
                                 'inferior': {'nombre': 'light trousers', 'nombre_corto': 'trousers', 'color': 'beige'},
                                 'calzado':  {'nombre': 'loafers',        'nombre_corto': 'loafers',  'color': 'brown'}},
                    'templado': {'superior': {'nombre': 'suit jacket',    'nombre_corto': 'jacket',   'color': 'navy'},
                                 'inferior': {'nombre': 'dress trousers', 'nombre_corto': 'trousers', 'color': 'navy'},
                                 'calzado':  {'nombre': 'oxford shoes',   'nombre_corto': 'shoes',    'color': 'black'}},
                    'frio':     {'superior': {'nombre': 'suit jacket',    'nombre_corto': 'jacket',   'color': 'black'},
                                 'inferior': {'nombre': 'dress trousers', 'nombre_corto': 'trousers', 'color': 'black'},
                                 'calzado':  {'nombre': 'dress shoes',    'nombre_corto': 'shoes',    'color': 'black'}}
                }
            },
            'deportiva': {
                'mujer': {
                    'calor':    {'superior': {'nombre': 'sports top',     'nombre_corto': 'sports top', 'color': 'black'},
                                 'inferior': {'nombre': 'short leggings', 'nombre_corto': 'leggings',   'color': 'black'},
                                 'calzado':  {'nombre': 'running trainers','nombre_corto': 'trainers',  'color': 'white'}},
                    'templado': {'superior': {'nombre': 'technical t-shirt','nombre_corto': 't-shirt',  'color': 'grey'},
                                 'inferior': {'nombre': 'leggings',        'nombre_corto': 'leggings',  'color': 'black'},
                                 'calzado':  {'nombre': 'trainers',        'nombre_corto': 'trainers',  'color': 'white'}},
                    'frio':     {'superior': {'nombre': 'thermal top',     'nombre_corto': 'thermal top','color': 'black'},
                                 'inferior': {'nombre': 'thermal leggings','nombre_corto': 'leggings',  'color': 'black'},
                                 'calzado':  {'nombre': 'trainers',        'nombre_corto': 'trainers',  'color': 'grey'}}
                },
                'hombre': {
                    'calor':    {'superior': {'nombre': 'technical t-shirt',  'nombre_corto': 't-shirt',          'color': 'white'},
                                 'inferior': {'nombre': 'shorts',             'nombre_corto': 'shorts',           'color': 'black'},
                                 'calzado':  {'nombre': 'trainers',           'nombre_corto': 'trainers',         'color': 'white'}},
                    'templado': {'superior': {'nombre': 'long-sleeve t-shirt','nombre_corto': 't-shirt',          'color': 'grey'},
                                 'inferior': {'nombre': 'leggings',           'nombre_corto': 'leggings',         'color': 'black'},
                                 'calzado':  {'nombre': 'trainers',           'nombre_corto': 'trainers',         'color': 'white'}},
                    'frio':     {'superior': {'nombre': 'thermal top',        'nombre_corto': 'thermal top',      'color': 'black'},
                                 'inferior': {'nombre': 'tracksuit bottoms',  'nombre_corto': 'tracksuit bottoms','color': 'black'},
                                 'calzado':  {'nombre': 'trainers',           'nombre_corto': 'trainers',         'color': 'black'}}
                }
            }
        }

        return generic_outfits.get(ocasion, generic_outfits['casual']).get(gender_key, {}).get(temp_cat, {}) 