import json
import os
from datetime import datetime

class WardrobeManager:
    """
    Virtual wardrobe manager — per-user CRUD operations on clothing items.

    Each user's wardrobe is stored as a JSON file under data/wardrobes/.
    Items added by the user are given priority over the generic clothing database
    by the KBS inference engine (they receive the first chance to score >= 50).
    """

    def __init__(self, user_email):
        self.user_email   = user_email
        self.wardrobe_file = f"data/wardrobes/{self._sanitize_email(user_email)}.json"
        self._ensure_file_exists()

    def _sanitize_email(self, email):
        """Convert an email address to a safe filename."""
        return email.replace('@', '_at_').replace('.', '_')

    def _ensure_file_exists(self):
        """Create the wardrobe file if it does not exist."""
        os.makedirs('data/wardrobes', exist_ok=True)
        if not os.path.exists(self.wardrobe_file):
            with open(self.wardrobe_file, 'w') as f:
                json.dump({'items': [], 'created_at': datetime.now().isoformat()}, f)

    def add_item(self, item_data):
        """
        Add a garment to the wardrobe.

        Required fields:
            nombre          : str   — garment name
            tipo            : str   — superior / inferior / vestido / calzado / complemento
            color           : str or list
            ocasion         : str or list  — formal / casual / deportiva
            clima_apropiado : str or list  — calor / templado / frio
        Optional fields:
            fit    : str  — ajustada / normal / holgada
            imagen : str  — filename of uploaded photo
            notas  : str  — free-text notes

        Returns the generated item ID.
        """
        wardrobe = self._load_wardrobe()

        item_data['id']       = self._generate_item_id()
        item_data['added_at'] = datetime.now().isoformat()

        required_fields = ['nombre', 'tipo', 'color', 'ocasion', 'clima_apropiado']
        for field in required_fields:
            if field not in item_data:
                raise ValueError(f"Required field missing: {field}")

        # Normalise JSON-encoded string fields to Python lists
        for field in ['color', 'ocasion', 'clima_apropiado']:
            if isinstance(item_data.get(field), str):
                try:
                    item_data[field] = json.loads(item_data[field])
                except:
                    pass  # Leave as string — match_item handles both

        wardrobe['items'].append(item_data)
        self._save_wardrobe(wardrobe)
        return item_data['id']

    def get_all_items(self):
        """Return all garments in the wardrobe."""
        return self._load_wardrobe()['items']

    def get_item_by_id(self, item_id):
        """Return a single garment by ID, or None if not found."""
        for item in self.get_all_items():
            if item['id'] == item_id:
                return item
        return None

    def update_item(self, item_id, updated_data):
        """Update an existing garment. Returns True on success."""
        wardrobe = self._load_wardrobe()
        for i, item in enumerate(wardrobe['items']):
            if item['id'] == item_id:
                wardrobe['items'][i].update(updated_data)
                wardrobe['items'][i]['updated_at'] = datetime.now().isoformat()
                self._save_wardrobe(wardrobe)
                return True
        return False

    def delete_item(self, item_id):
        """Remove a garment from the wardrobe. Returns True on success."""
        wardrobe        = self._load_wardrobe()
        original_length = len(wardrobe['items'])
        wardrobe['items'] = [item for item in wardrobe['items'] if item['id'] != item_id]
        if len(wardrobe['items']) < original_length:
            self._save_wardrobe(wardrobe)
            return True
        return False

    def search_items(self, **filters):
        """
        Search wardrobe items by arbitrary field filters.
        Both string and list field values are handled.

        Example:
            search_items(tipo='superior', ocasion='formal')
        """
        results = []
        for item in self.get_all_items():
            match = True
            for key, value in filters.items():
                item_value = item.get(key)
                if isinstance(item_value, list):
                    if value not in item_value:
                        match = False
                        break
                else:
                    if item_value != value:
                        match = False
                        break
            if match:
                results.append(item)
        return results

    def get_outfit_suggestions(self, ocasion, clima, fit_preference, season_colors):
        """
        Suggest an outfit from the wardrobe for a given occasion, climate and season palette.
        Garments whose colour matches the palette are prioritised.

        Returns a dict of {garment_type: item} or None if nothing suitable is found.
        """
        all_items = self.get_all_items()
        suitable  = []

        for item in all_items:
            item_ocasiones = item.get('ocasion', [])
            if isinstance(item_ocasiones, str):
                item_ocasiones = [item_ocasiones]
            item_climas = item.get('clima_apropiado', [])
            if isinstance(item_climas, str):
                item_climas = [item_climas]
            if ocasion in item_ocasiones and clima in item_climas:
                suitable.append(item)

        if not suitable:
            return None

        # Apply fit preference filter
        if fit_preference:
            fit_items = [i for i in suitable if i.get('fit') == fit_preference]
            if fit_items:
                suitable = fit_items

        # Sort by colour-palette match
        color_matched = []
        other_items   = []
        for item in suitable:
            item_colors = item.get('color', [])
            if isinstance(item_colors, str):
                item_colors = [item_colors]
            if any(c.lower() in [sc.lower() for sc in season_colors] for c in item_colors):
                color_matched.append(item)
            else:
                other_items.append(item)
        suitable = color_matched + other_items

        # Build outfit — one item per category
        outfit = {}
        for tipo in ['superior', 'inferior', 'vestido', 'calzado', 'complemento']:
            for item in suitable:
                if item.get('tipo') == tipo and tipo not in outfit:
                    outfit[tipo] = item
                    break

        return outfit if outfit else None

    def get_statistics(self):
        """Return counts of wardrobe items grouped by type, occasion, climate and colour."""
        items = self.get_all_items()
        stats = {
            'total_items': len(items),
            'by_type':     {},
            'by_occasion': {},
            'by_climate':  {},
            'by_color':    {}
        }
        for item in items:
            # By type
            tipo = item.get('tipo', 'unknown')
            stats['by_type'][tipo] = stats['by_type'].get(tipo, 0) + 1

            # By occasion
            occ = item.get('ocasion', [])
            if isinstance(occ, str): occ = [occ]
            for o in occ:
                stats['by_occasion'][o] = stats['by_occasion'].get(o, 0) + 1

            # By climate
            clm = item.get('clima_apropiado', [])
            if isinstance(clm, str): clm = [clm]
            for c in clm:
                stats['by_climate'][c] = stats['by_climate'].get(c, 0) + 1

            # By colour
            col = item.get('color', [])
            if isinstance(col, str): col = [col]
            for c in col:
                stats['by_color'][c] = stats['by_color'].get(c, 0) + 1

        return stats

    def suggest_missing_items(self):
        """
        Analyse the wardrobe and suggest missing garment categories or occasions.
        Returns a list of suggestion strings.
        """
        stats       = self.get_statistics()
        suggestions = []

        basic = {
            'superior':    ['basic t-shirt', 'shirt', 'jumper'],
            'inferior':    ['trousers', 'jeans'],
            'calzado':     ['trainers', 'formal shoes'],
            'complemento': ['bag', 'belt']
        }
        for tipo, examples in basic.items():
            if stats['by_type'].get(tipo, 0) < 3:
                suggestions.append(
                    f"Consider adding more {tipo} items (e.g. {', '.join(examples)})"
                )

        for ocasion in ['formal', 'casual', 'deportiva']:
            if stats['by_occasion'].get(ocasion, 0) < 2:
                suggestions.append(f"You have few options for {ocasion} occasions")

        for clima in ['calor', 'templado', 'frio']:
            if stats['by_climate'].get(clima, 0) < 2:
                suggestions.append(f"Add more garments suitable for {clima} weather")

        return suggestions

    def _generate_item_id(self):
        """Generate a unique item ID based on current timestamp."""
        import time
        return f"item_{int(time.time() * 1000)}"

    def _load_wardrobe(self):
        """Load the wardrobe from its JSON file."""
        with open(self.wardrobe_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_wardrobe(self, wardrobe_data):
        """Persist the wardrobe to its JSON file."""
        with open(self.wardrobe_file, 'w', encoding='utf-8') as f:
            json.dump(wardrobe_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    wm = WardrobeManager('test@example.com')
    wm.add_item({
        'nombre': 'White Cotton Shirt', 'tipo': 'superior',
        'color': 'white', 'ocasion': ['formal','casual'],
        'clima_apropiado': ['templado','calor'], 'fit': 'normal'
    })
    print(f"Wardrobe items: {len(wm.get_all_items())}")
    print(f"Statistics: {wm.get_statistics()}")