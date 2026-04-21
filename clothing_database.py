import json
import os

class ClothingDatabase:
    """
    Generic clothing database (91 items) used as the KBS fallback source.
    When the user's personal wardrobe contains no garment that scores >= 50
    in the inference engine, items are retrieved from this database instead.

    Supports advanced search by garment type, occasion, climate, season and colour.
    """

    def __init__(self):
        self.db_file   = 'data/clothing_items.json'
        self.images_dir = 'static/clothing_images'
        self._ensure_structure()
        self._load_database()

    def _ensure_structure(self):
        """Create required directory structure if it does not exist."""
        os.makedirs('data', exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        for t in ['superior', 'inferior', 'vestido', 'calzado', 'complemento']:
            os.makedirs(f'{self.images_dir}/{t}', exist_ok=True)

    def _load_database(self):
        """Load the clothing database from JSON, or create a default one."""
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r', encoding='utf-8') as f:
                self.items = json.load(f)
        else:
            self.items = self._create_default_database()
            self._save_database()

    def _save_database(self):
        """Persist the database to JSON."""
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.items, f, indent=2, ensure_ascii=False)

    def _create_default_database(self):
        """Create a minimal default database (used only if clothing_items.json is missing)."""
        return {
            "superior": [
                {"id": "sup_001", "nombre": "Basic White T-shirt",  "nombre_corto": "white t-shirt",
                 "color": ["white"],  "ocasion": ["casual","deportiva"], "clima": ["calor","templado"],
                 "estacion": ["Primavera","Verano"],  "fit": "normal",  "imagen": "superior/camiseta_blanca.jpg"},
                {"id": "sup_002", "nombre": "Sky Blue Silk Blouse", "nombre_corto": "blue blouse",
                 "color": ["blue"],   "ocasion": ["formal","casual"],   "clima": ["templado","calor"],
                 "estacion": ["Verano","Primavera"],  "fit": "normal",  "imagen": "superior/blusa_azul.jpg"},
                {"id": "sup_003", "nombre": "Grey Knit Jumper",     "nombre_corto": "grey jumper",
                 "color": ["grey"],   "ocasion": ["casual","formal"],   "clima": ["frio","templado"],
                 "estacion": ["Otono","Invierno"],    "fit": "normal",  "imagen": "superior/jersey_gris.jpg"},
                {"id": "sup_004", "nombre": "Olive Green Shirt",    "nombre_corto": "olive shirt",
                 "color": ["green"],  "ocasion": ["casual"],           "clima": ["templado"],
                 "estacion": ["Otono","Primavera"],   "fit": "normal",  "imagen": "superior/camisa_verde.jpg"},
                {"id": "sup_005", "nombre": "Coral Top",            "nombre_corto": "coral top",
                 "color": ["coral"],  "ocasion": ["casual","formal"],  "clima": ["calor"],
                 "estacion": ["Primavera","Verano"],  "fit": "ajustada","imagen": "superior/top_coral.jpg"}
            ],
            "inferior": [
                {"id": "inf_001", "nombre": "Dark Blue Jeans",      "nombre_corto": "jeans",
                 "color": ["blue"],   "ocasion": ["casual"],          "clima": ["templado","frio"],
                 "estacion": ["Otono","Primavera","Invierno"],        "fit": "normal", "imagen": "inferior/vaqueros_azul.jpg"},
                {"id": "inf_002", "nombre": "Black Dress Trousers",  "nombre_corto": "black trousers",
                 "color": ["black"],  "ocasion": ["formal"],          "clima": ["templado","frio"],
                 "estacion": ["Invierno","Otono"],   "fit": "ajustada","imagen": "inferior/pantalon_negro.jpg"},
                {"id": "inf_003", "nombre": "Beige Midi Skirt",      "nombre_corto": "beige skirt",
                 "color": ["beige"],  "ocasion": ["casual","formal"], "clima": ["calor","templado"],
                 "estacion": ["Primavera","Verano"], "fit": "normal",  "imagen": "inferior/falda_beige.jpg"},
                {"id": "inf_004", "nombre": "White Shorts",          "nombre_corto": "white shorts",
                 "color": ["white"],  "ocasion": ["casual","deportiva"],"clima": ["calor"],
                 "estacion": ["Verano"],             "fit": "normal",  "imagen": "inferior/shorts_blancos.jpg"}
            ],
            "vestido": [
                {"id": "ves_001", "nombre": "Short Black Dress",     "nombre_corto": "black dress",
                 "color": ["black"],  "ocasion": ["formal"],          "clima": ["templado","calor"],
                 "estacion": ["Invierno","Verano"],  "fit": "ajustada","imagen": "vestido/vestido_negro.jpg"},
                {"id": "ves_002", "nombre": "Pink Floral Dress",     "nombre_corto": "floral dress",
                 "color": ["pink"],   "ocasion": ["casual"],          "clima": ["calor"],
                 "estacion": ["Primavera","Verano"], "fit": "normal",  "imagen": "vestido/vestido_floral.jpg"}
            ],
            "calzado": [
                {"id": "cal_001", "nombre": "White Trainers",        "nombre_corto": "trainers",
                 "color": ["white"],  "ocasion": ["casual","deportiva"],"clima": ["calor","templado"],
                 "estacion": ["Primavera","Verano","Otono"],"fit": "normal","imagen": "calzado/zapatillas_blancas.jpg"},
                {"id": "cal_002", "nombre": "Black Heels",           "nombre_corto": "heels",
                 "color": ["black"],  "ocasion": ["formal"],          "clima": ["templado"],
                 "estacion": ["Invierno","Otono","Primavera"],"fit": "ajustada","imagen": "calzado/tacones_negros.jpg"},
                {"id": "cal_003", "nombre": "Brown Boots",           "nombre_corto": "boots",
                 "color": ["brown"],  "ocasion": ["casual","formal"], "clima": ["frio","templado"],
                 "estacion": ["Otono","Invierno"],   "fit": "normal",  "imagen": "calzado/botas_marrones.jpg"}
            ],
            "complemento": [
                {"id": "com_001", "nombre": "Black Leather Handbag", "nombre_corto": "black handbag",
                 "color": ["black"],  "ocasion": ["formal","casual"], "clima": ["templado","frio"],
                 "estacion": ["Invierno","Otono"],   "fit": "normal",  "imagen": "complemento/bolso_negro.jpg"},
                {"id": "com_002", "nombre": "Sunglasses",            "nombre_corto": "sunglasses",
                 "color": ["black"],  "ocasion": ["casual","deportiva"],"clima": ["calor"],
                 "estacion": ["Verano","Primavera"], "fit": "normal",  "imagen": "complemento/gafas_sol.jpg"},
                {"id": "com_003", "nombre": "Gold Necklace",         "nombre_corto": "gold necklace",
                 "color": ["gold"],   "ocasion": ["formal"],          "clima": ["templado","calor"],
                 "estacion": ["Primavera","Verano"], "fit": "normal",  "imagen": "complemento/collar_dorado.jpg"}
            ]
        }

    def search_items(self, tipo=None, ocasion=None, clima=None, estacion=None, color=None):
        """
        Search the database with optional filters.

        Args:
            tipo     : garment type  (superior / inferior / vestido / calzado / complemento)
            ocasion  : occasion      (formal / casual / deportiva)
            clima    : climate       (calor / templado / frio)
            estacion : season        (Primavera / Verano / Otono / Invierno)
            color    : colour string (partial match, case-insensitive)

        Returns:
            list of matching garment dicts (each includes a 'tipo' key)
        """
        results = []
        items_to_search = {tipo: self.items.get(tipo, [])} if tipo else self.items

        for item_type, items in items_to_search.items():
            for item in items:
                match = True
                if ocasion  and ocasion  not in item.get('ocasion', []):  match = False
                if clima    and clima    not in item.get('clima', []):    match = False
                if estacion and estacion not in item.get('estacion', []): match = False
                if color:
                    if not any(color.lower() in c.lower() for c in item.get('color', [])):
                        match = False
                if match:
                    item_copy = item.copy()
                    item_copy['tipo'] = item_type
                    results.append(item_copy)

        return results

    def get_outfit_suggestion(self, ocasion, clima, estacion, colores_favorables):
        """
        Build a complete outfit suggestion from the database.
        Garments whose colour matches the user's palette are prioritised.
        """
        outfit = {}

        # Extract palette keywords for colour matching
        color_keywords = set()
        for name in colores_favorables:
            color_keywords.update(name.lower().split())

        def best_match(candidates):
            """Return the candidate with the best colour-palette match."""
            favoured = [c for c in candidates
                        if any(any(kw in col.lower() for kw in color_keywords)
                               for col in c.get('color', []))]
            return favoured[0] if favoured else (candidates[0] if candidates else None)

        tops = self.search_items(tipo='superior', ocasion=ocasion, clima=clima, estacion=estacion)
        if tops:
            outfit['superior'] = best_match(tops)

        dresses  = self.search_items(tipo='vestido',  ocasion=ocasion, clima=clima, estacion=estacion)
        bottoms  = self.search_items(tipo='inferior', ocasion=ocasion, clima=clima, estacion=estacion)
        if dresses and ocasion == 'formal':
            outfit['vestido'] = dresses[0]
        elif bottoms:
            outfit['inferior'] = best_match(bottoms)

        footwear = self.search_items(tipo='calzado',     ocasion=ocasion, clima=clima)
        if footwear:
            outfit['calzado'] = footwear[0]

        accessories = self.search_items(tipo='complemento', ocasion=ocasion, clima=clima)
        if accessories:
            outfit['complemento'] = accessories[0]

        return outfit

    def get_item_by_id(self, item_id):
        """Retrieve a single garment by its ID."""
        for tipo, items in self.items.items():
            for item in items:
                if item['id'] == item_id:
                    item_copy = item.copy()
                    item_copy['tipo'] = tipo
                    return item_copy
        return None


if __name__ == "__main__":
    db = ClothingDatabase()
    print("Clothing database loaded successfully.")
    for tipo, items in db.items.items():
        print(f"   {tipo}: {len(items)} items")
    print("\nSearch test — casual items for warm weather:")
    for item in db.search_items(ocasion='casual', clima='calor')[:3]:
        print(f"   - {item['nombre']} ({item['tipo']})")