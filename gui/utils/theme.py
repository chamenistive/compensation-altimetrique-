"""
Configuration du thème et des couleurs pour l'application.

Palette de couleurs utilisateur :
- Bleu principal: #7671FA
- Blanc/Gris clair: #E5EAF3  
- Bleu foncé: #07244C
- Gris: #7E7F9C
"""

import customtkinter as ctk
from typing import Dict, Tuple

class AppTheme:
    """Configuration centralisée du thème de l'application."""
    
    # Palette de couleurs principale
    COLORS = {
        'primary': '#7671FA',      # Bleu principal
        'primary_dark': '#5A54E6', # Bleu principal foncé (hover)
        'secondary': '#07244C',    # Bleu foncé
        'background': '#E5EAF3',   # Blanc/Gris clair
        'surface': '#FFFFFF',      # Blanc pur
        'text': '#07244C',         # Texte principal (bleu foncé)
        'text_secondary': '#7E7F9C', # Texte secondaire (gris)
        'accent': '#7671FA',       # Accent (même que primary)
        'success': '#4CAF50',      # Vert pour succès
        'warning': '#FF9800',      # Orange pour avertissements
        'error': '#F44336',        # Rouge pour erreurs
        'border': '#D0D5DD',       # Bordures subtiles
    }
    
    # Configuration CustomTkinter
    CTK_THEME = {
        'color_theme': 'blue',  # Thème de base
        'appearance_mode': 'light'  # Mode clair
    }
    
    # Tailles et espacements
    SPACING = {
        'xs': 4,
        'sm': 8,
        'md': 16,
        'lg': 24,
        'xl': 32,
        'xxl': 48
    }
    
    # Polices
    FONTS = {
        'title': ('Segoe UI', 24, 'bold'),
        'heading': ('Segoe UI', 18, 'bold'),
        'subheading': ('Segoe UI', 14, 'bold'),
        'body': ('Segoe UI', 12, 'normal'),
        'small': ('Segoe UI', 10, 'normal'),
        'button': ('Segoe UI', 12, 'bold'),
    }
    
    # Dimensions des composants
    SIZES = {
        'button_height': 40,
        'input_height': 36,
        'card_corner_radius': 12,
        'button_corner_radius': 8,
        'window_min_width': 900,
        'window_min_height': 600,
        'sidebar_width': 250,
    }

    @classmethod
    def apply_theme(cls):
        """Applique le thème à CustomTkinter."""
        ctk.set_appearance_mode(cls.CTK_THEME['appearance_mode'])
        ctk.set_default_color_theme(cls.CTK_THEME['color_theme'])
    
    @classmethod
    def get_button_colors(cls, variant: str = 'primary') -> Dict[str, str]:
        """Retourne les couleurs pour les boutons selon le variant."""
        variants = {
            'primary': {
                'fg_color': cls.COLORS['primary'],
                'hover_color': cls.COLORS['primary_dark'],
                'text_color': '#FFFFFF',
                'border_color': cls.COLORS['primary']
            },
            'secondary': {
                'fg_color': cls.COLORS['secondary'],
                'hover_color': '#0A2F5C',
                'text_color': '#FFFFFF',
                'border_color': cls.COLORS['secondary']
            },
            'outline': {
                'fg_color': 'transparent',
                'hover_color': cls.COLORS['background'],
                'text_color': cls.COLORS['primary'],
                'border_color': cls.COLORS['primary']
            },
            'ghost': {
                'fg_color': 'transparent',
                'hover_color': cls.COLORS['background'],
                'text_color': cls.COLORS['text'],
                'border_color': 'transparent'
            }
        }
        return variants.get(variant, variants['primary'])
    
    @classmethod
    def get_card_style(cls) -> Dict[str, any]:
        """Style pour les cartes/panneaux."""
        return {
            'fg_color': cls.COLORS['surface'],
            'corner_radius': cls.SIZES['card_corner_radius'],
            'border_width': 1,
            'border_color': cls.COLORS['border']
        }


# Fonctions utilitaires pour les couleurs
def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convertit une couleur hex en RGB."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convertit RGB en hex."""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def lighten_color(hex_color: str, factor: float = 0.2) -> str:
    """Éclaircit une couleur."""
    rgb = hex_to_rgb(hex_color)
    rgb = tuple(min(255, int(c + (255 - c) * factor)) for c in rgb)
    return rgb_to_hex(rgb)

def darken_color(hex_color: str, factor: float = 0.2) -> str:
    """Assombrit une couleur."""
    rgb = hex_to_rgb(hex_color)
    rgb = tuple(max(0, int(c * (1 - factor))) for c in rgb)
    return rgb_to_hex(rgb)