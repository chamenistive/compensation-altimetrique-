"""
Composants UI réutilisables pour l'application.
Basés sur CustomTkinter avec le thème personnalisé.
"""

import customtkinter as ctk
from typing import Optional, Callable, List, Any
from ..utils.theme import AppTheme

class ThemedButton(ctk.CTkButton):
    """Bouton avec thème personnalisé."""
    
    def __init__(self, parent, text: str, variant: str = 'primary', 
                 command: Optional[Callable] = None, **kwargs):
        
        # Récupérer les couleurs du variant
        colors = AppTheme.get_button_colors(variant)
        
        # Configuration par défaut
        defaults = {
            'height': AppTheme.SIZES['button_height'],
            'corner_radius': AppTheme.SIZES['button_corner_radius'],
            'font': AppTheme.FONTS['button'],
            'fg_color': colors['fg_color'],
            'hover_color': colors['hover_color'],
            'text_color': colors['text_color'],
            'border_width': 2 if variant == 'outline' else 0,
            'border_color': colors['border_color'],
        }
        
        # Fusionner avec les kwargs
        config = {**defaults, **kwargs}
        
        super().__init__(parent, text=text, command=command, **config)

class ThemedLabel(ctk.CTkLabel):
    """Label avec thème personnalisé."""
    
    def __init__(self, parent, text: str, style: str = 'body', **kwargs):
        
        defaults = {
            'font': AppTheme.FONTS[style],
            'text_color': AppTheme.COLORS['text'],
        }
        
        config = {**defaults, **kwargs}
        super().__init__(parent, text=text, **config)

class ThemedEntry(ctk.CTkEntry):
    """Champ de saisie avec thème personnalisé."""
    
    def __init__(self, parent, placeholder: str = "", **kwargs):
        
        defaults = {
            'height': AppTheme.SIZES['input_height'],
            'corner_radius': AppTheme.SIZES['button_corner_radius'],
            'font': AppTheme.FONTS['body'],
            'fg_color': AppTheme.COLORS['surface'],
            'border_color': AppTheme.COLORS['border'],
            'text_color': AppTheme.COLORS['text'],
            'placeholder_text_color': AppTheme.COLORS['text_secondary'],
        }
        
        config = {**defaults, **kwargs}
        super().__init__(parent, placeholder_text=placeholder, **config)

class ThemedFrame(ctk.CTkFrame):
    """Frame avec style de carte."""
    
    def __init__(self, parent, **kwargs):
        
        defaults = AppTheme.get_card_style()
        config = {**defaults, **kwargs}
        
        super().__init__(parent, **config)

class ThemedProgressBar(ctk.CTkProgressBar):
    """Barre de progression avec thème."""
    
    def __init__(self, parent, **kwargs):
        
        defaults = {
            'progress_color': AppTheme.COLORS['primary'],
            'fg_color': AppTheme.COLORS['background'],
            'corner_radius': 4,
            'height': 8,
        }
        
        config = {**defaults, **kwargs}
        super().__init__(parent, **config)

class StepIndicator(ctk.CTkFrame):
    """Indicateur d'étapes pour l'assistant."""
    
    def __init__(self, parent, steps: List[str], current_step: int = 0):
        super().__init__(parent, fg_color='transparent')
        
        self.steps = steps
        self.current_step = current_step
        self.step_widgets = []
        
        self.create_widgets()
    
    def create_widgets(self):
        """Crée les widgets de l'indicateur."""
        for i, step in enumerate(self.steps):
            # Frame pour chaque étape
            step_frame = ctk.CTkFrame(self, fg_color='transparent')
            step_frame.pack(side='left', padx=AppTheme.SPACING['sm'], fill='y')
            
            # Cercle numéroté
            is_current = i == self.current_step
            is_completed = i < self.current_step
            
            if is_completed:
                circle_color = AppTheme.COLORS['success']
                text_color = '#FFFFFF'
                circle_text = "✓"
            elif is_current:
                circle_color = AppTheme.COLORS['primary']
                text_color = '#FFFFFF'
                circle_text = str(i + 1)
            else:
                circle_color = AppTheme.COLORS['background']
                text_color = AppTheme.COLORS['text_secondary']
                circle_text = str(i + 1)
            
            # Cercle
            circle = ctk.CTkLabel(
                step_frame,
                text=circle_text,
                width=30,
                height=30,
                fg_color=circle_color,
                text_color=text_color,
                font=AppTheme.FONTS['small'],
                corner_radius=15
            )
            circle.pack(pady=(0, AppTheme.SPACING['xs']))
            
            # Label de l'étape
            label_color = AppTheme.COLORS['text'] if is_current else AppTheme.COLORS['text_secondary']
            font_style = 'subheading' if is_current else 'small'
            
            label = ThemedLabel(
                step_frame,
                text=step,
                style=font_style,
                text_color=label_color
            )
            label.pack()
            
            self.step_widgets.append((circle, label))
            
            # Ligne de connexion (sauf pour le dernier)
            if i < len(self.steps) - 1:
                line_color = AppTheme.COLORS['primary'] if is_completed else AppTheme.COLORS['border']
                line = ctk.CTkFrame(
                    self,
                    width=40,
                    height=2,
                    fg_color=line_color
                )
                line.pack(side='left', padx=AppTheme.SPACING['xs'], pady=(15, 0))
    
    def update_step(self, new_step: int):
        """Met à jour l'étape courante."""
        self.current_step = new_step
        
        # Détruire et recréer les widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        self.step_widgets.clear()
        self.create_widgets()

class StatusBar(ctk.CTkFrame):
    """Barre d'état en bas de l'application."""
    
    def __init__(self, parent):
        super().__init__(
            parent,
            height=30,
            fg_color=AppTheme.COLORS['background'],
            corner_radius=0
        )
        
        # Label de statut
        self.status_label = ThemedLabel(
            self,
            text="Prêt",
            style='small',
            text_color=AppTheme.COLORS['text_secondary']
        )
        self.status_label.pack(side='left', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['xs'])
        
        # Label de version (à droite)
        self.version_label = ThemedLabel(
            self,
            text="v1.0",
            style='small',
            text_color=AppTheme.COLORS['text_secondary']
        )
        self.version_label.pack(side='right', padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['xs'])
    
    def set_status(self, message: str):
        """Met à jour le message de statut."""
        self.status_label.configure(text=message)

class FileDropFrame(ThemedFrame):
    """Zone de glisser-déposer pour les fichiers."""
    
    def __init__(self, parent, callback: Optional[Callable] = None):
        super().__init__(parent)
        
        self.callback = callback
        self.configure(height=150)
        
        # Label d'instruction
        self.drop_label = ThemedLabel(
            self,
            text="📁 Glissez votre fichier Excel ici\\nou cliquez pour sélectionner",
            style='body',
            text_color=AppTheme.COLORS['text_secondary']
        )
        self.drop_label.pack(expand=True)
        
        # Bind pour le clic
        self.bind("<Button-1>", self._on_click)
        self.drop_label.bind("<Button-1>", self._on_click)
        
        # Effet hover
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_click(self, event):
        """Ouvre le dialogue de sélection de fichier."""
        if self.callback:
            self.callback()
    
    def _on_enter(self, event):
        """Effet hover."""
        self.configure(fg_color=AppTheme.COLORS['background'])
    
    def _on_leave(self, event):
        """Fin effet hover."""
        self.configure(fg_color=AppTheme.COLORS['surface'])
    
    def set_file_selected(self, filename: str):
        """Indique qu'un fichier a été sélectionné."""
        self.drop_label.configure(
            text=f"✅ Fichier sélectionné:\\n{filename}",
            text_color=AppTheme.COLORS['success']
        )