"""
Configuration du thème et des couleurs pour l'application.
Système de Compensation Altimétrique - Desktop Windows

Palette de couleurs géodésiques professionnelles :
- Bleu géodésique: #2E86AB (Primaire)
- Magenta technique: #A23B72 (Secondaire) 
- Orange précision: #F18F01 (Accent)
- Background moderne: #F8FAFC
"""

import customtkinter as ctk
from typing import Dict, Tuple

class AppTheme:
    """Configuration centralisée du thème géodésique professionnel."""
    
    # Palette de couleurs géodésiques moderne
    COLORS = {
        # Couleurs principales géodésiques
        'primary': '#2E86AB',          # Bleu géodésique
        'primary_dark': '#1F5F85',     # Bleu géodésique foncé (hover)
        'primary_light': '#4DA3C7',    # Bleu géodésique clair
        'secondary': '#A23B72',        # Magenta technique  
        'secondary_dark': '#7A2B56',   # Magenta foncé
        'accent': '#F18F01',           # Orange précision
        'accent_dark': '#CC7700',      # Orange foncé
        
        # Couleurs de surface modernes
        'background': '#F8FAFC',       # Gris très clair moderne
        'surface': '#FFFFFF',          # Blanc pur
        'surface_elevated': '#FDFDFD', # Surface surélevée
        'card_bg': '#FFFFFF',          # Arrière-plan des cartes
        
        # Couleurs de texte
        'text': '#1E293B',             # Texte principal (gris foncé)
        'text_secondary': '#64748B',   # Texte secondaire
        'text_muted': '#94A3B8',       # Texte atténué
        'text_on_primary': '#FFFFFF',  # Texte sur fond primaire
        
        # États de validation
        'success': '#10B981',          # Vert validation
        'success_light': '#D1FAE5',    # Vert clair
        'warning': '#F59E0B',          # Jaune avertissement
        'warning_light': '#FEF3C7',    # Jaune clair
        'error': '#EF4444',            # Rouge critique
        'error_light': '#FEE2E2',      # Rouge clair
        'info': '#3B82F6',             # Bleu information
        'info_light': '#DBEAFE',       # Bleu clair
        
        # Bordures et séparateurs
        'border': '#E2E8F0',           # Bordures principales
        'border_light': '#F1F5F9',     # Bordures légères
        'border_dark': '#CBD5E1',      # Bordures accentuées
        'divider': '#E5E7EB',          # Séparateurs
        
        # Effets glassmorphism
        'glass_bg': '#FFFFFF99',       # Fond verre (transparence)
        'glass_border': '#FFFFFF33',   # Bordure verre
        'shadow_light': '#0000000A',   # Ombre légère
        'shadow_medium': '#00000015',  # Ombre moyenne
        'shadow_strong': '#00000025',  # Ombre forte
    }
    
    # Configuration CustomTkinter optimisée Windows
    CTK_THEME = {
        'color_theme': 'blue',  # Base CustomTkinter
        'appearance_mode': 'light',  # Mode clair par défaut
        'scaling': 1.0  # Échelle Windows (sera ajustée selon DPI)
    }
    
    # Espacements hiérarchiques modernes
    SPACING = {
        'xs': 4,    # Micro-espacements
        'sm': 8,    # Petits espacements
        'md': 16,   # Espacements moyens
        'lg': 24,   # Grands espacements
        'xl': 32,   # Très grands espacements
        'xxl': 48,  # Espacements maximaux
        'section': 20,  # Entre sections
        'component': 12,  # Entre composants
    }
    
    # Typographie hiérarchique Windows
    FONTS = {
        # Titres et en-têtes
        'display': ('Segoe UI', 32, 'bold'),      # Titre principal
        'title': ('Segoe UI', 24, 'bold'),        # Titres de pages
        'heading': ('Segoe UI', 18, 'bold'),      # Titres de sections
        'subheading': ('Segoe UI', 14, 'bold'),   # Sous-titres
        
        # Corps de texte
        'body': ('Segoe UI', 12, 'normal'),       # Texte principal
        'body_medium': ('Segoe UI', 12, '500'),   # Texte moyen
        'small': ('Segoe UI', 10, 'normal'),      # Petit texte
        'caption': ('Segoe UI', 9, 'normal'),     # Légendes
        
        # Éléments interactifs
        'button': ('Segoe UI', 12, 'bold'),       # Boutons
        'button_large': ('Segoe UI', 14, 'bold'), # Gros boutons
        'input': ('Segoe UI', 11, 'normal'),      # Champs de saisie
        
        # Données techniques
        'monospace': ('Consolas', 10, 'normal'),  # Code et données
        'monospace_bold': ('Consolas', 10, 'bold'), # Code en gras
    }
    
    # Dimensions adaptées Windows Desktop
    SIZES = {
        # Fenêtre principale
        'window_min_width': 1024,     # Largeur minimale
        'window_min_height': 768,     # Hauteur minimale
        'window_default_width': 1200, # Largeur par défaut
        'window_default_height': 900, # Hauteur par défaut
        
        # Composants interactifs
        'button_height': 44,          # Hauteur boutons (tactile-friendly)
        'button_height_small': 32,    # Petits boutons
        'input_height': 40,           # Champs de saisie
        'dropdown_height': 40,        # Listes déroulantes
        
        # Bordures et coins
        'border_radius': 8,           # Radius standard
        'border_radius_small': 4,     # Petits radius
        'border_radius_large': 12,    # Grands radius
        'card_radius': 16,            # Cartes modernes
        
        # Espacement des cartes
        'card_padding': 20,           # Padding des cartes
        'card_margin': 16,            # Marge des cartes
        
        # Barres latérales
        'sidebar_width': 280,         # Largeur sidebar
        'sidebar_collapsed_width': 60, # Sidebar collapsée
        
        # Éléments de navigation
        'tab_height': 48,             # Hauteur des onglets
        'header_height': 80,          # Hauteur en-tête
        'statusbar_height': 32,       # Barre de statut
        
        # Indicateurs
        'progress_height': 8,         # Barres de progression
        'indicator_size': 12,         # Taille indicateurs
        'icon_size_small': 16,        # Petites icônes
        'icon_size_medium': 20,       # Icônes moyennes
        'icon_size_large': 24,        # Grandes icônes
    }

    @classmethod
    def apply_theme(cls):
        """Applique le thème géodésique à CustomTkinter."""
        ctk.set_appearance_mode(cls.CTK_THEME['appearance_mode'])
        ctk.set_default_color_theme(cls.CTK_THEME['color_theme'])
        
        # Configuration Windows DPI-aware
        try:
            import tkinter as tk
            root = tk._default_root or tk._get_temp_root()
            if root:
                root.tk.call('tk', 'scaling', cls.CTK_THEME['scaling'])
        except:
            pass  # Fallback si pas de root
    
    @classmethod
    def get_button_colors(cls, variant: str = 'primary') -> Dict[str, str]:
        """Retourne les couleurs modernes pour les boutons selon le variant."""
        variants = {
            'primary': {
                'fg_color': cls.COLORS['primary'],
                'hover_color': cls.COLORS['primary_dark'],
                'text_color': cls.COLORS['text_on_primary'],
                'border_color': cls.COLORS['primary'],
                'disabled_color': cls.COLORS['text_muted']
            },
            'secondary': {
                'fg_color': cls.COLORS['secondary'],
                'hover_color': cls.COLORS['secondary_dark'],
                'text_color': cls.COLORS['text_on_primary'],
                'border_color': cls.COLORS['secondary'],
                'disabled_color': cls.COLORS['text_muted']
            },
            'accent': {
                'fg_color': cls.COLORS['accent'],
                'hover_color': cls.COLORS['accent_dark'],
                'text_color': cls.COLORS['text_on_primary'],
                'border_color': cls.COLORS['accent'],
                'disabled_color': cls.COLORS['text_muted']
            },
            'success': {
                'fg_color': cls.COLORS['success'],
                'hover_color': '#059669',  # Plus foncé
                'text_color': cls.COLORS['text_on_primary'],
                'border_color': cls.COLORS['success'],
                'disabled_color': cls.COLORS['text_muted']
            },
            'outline': {
                'fg_color': 'transparent',
                'hover_color': cls.COLORS['background'],
                'text_color': cls.COLORS['primary'],
                'border_color': cls.COLORS['primary'],
                'disabled_color': cls.COLORS['text_muted']
            },
            'ghost': {
                'fg_color': 'transparent',
                'hover_color': cls.COLORS['surface_elevated'],
                'text_color': cls.COLORS['text'],
                'border_color': 'transparent',
                'disabled_color': cls.COLORS['text_muted']
            },
            'glass': {
                'fg_color': cls.COLORS['glass_bg'],
                'hover_color': cls.COLORS['surface_elevated'],
                'text_color': cls.COLORS['text'],
                'border_color': cls.COLORS['glass_border'],
                'disabled_color': cls.COLORS['text_muted']
            }
        }
        return variants.get(variant, variants['primary'])
    
    @classmethod
    def get_card_style(cls, elevated: bool = False) -> Dict[str, any]:
        """Style moderne pour les cartes/panneaux avec effet glassmorphism."""
        base_style = {
            'fg_color': cls.COLORS['surface_elevated'] if elevated else cls.COLORS['card_bg'],
            'corner_radius': cls.SIZES['card_radius'],
            'border_width': 1,
            'border_color': cls.COLORS['border_light']
        }
        return base_style
    
    @classmethod
    def get_input_style(cls) -> Dict[str, any]:
        """Style pour les champs de saisie."""
        return {
            'height': cls.SIZES['input_height'],
            'corner_radius': cls.SIZES['border_radius'],
            'border_width': 1,
            'border_color': cls.COLORS['border'],
            'fg_color': cls.COLORS['surface'],
            'text_color': cls.COLORS['text'],
            'font': cls.FONTS['input']
        }
    
    @classmethod
    def get_shadow_style(cls, level: str = 'medium') -> str:
        """Retourne le style d'ombre selon le niveau."""
        shadows = {
            'light': cls.COLORS['shadow_light'],
            'medium': cls.COLORS['shadow_medium'], 
            'strong': cls.COLORS['shadow_strong']
        }
        return shadows.get(level, shadows['medium'])


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