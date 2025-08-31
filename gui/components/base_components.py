"""
Composants UI réutilisables pour l'application.
Basés sur CustomTkinter avec le thème personnalisé.
"""

import customtkinter as ctk
from typing import Optional, Callable, List, Any
from ..utils.theme import AppTheme
class ThemedButton(ctk.CTkButton):
    """Bouton avec thème géodésique moderne."""
    
    def __init__(self, parent, text: str, variant: str = 'primary', 
                 size: str = 'medium', command: Optional[Callable] = None, **kwargs):
        
        # Récupérer les couleurs du variant
        colors = AppTheme.get_button_colors(variant)
        
        # Tailles de boutons
        button_heights = {
            'small': AppTheme.SIZES['button_height_small'],
            'medium': AppTheme.SIZES['button_height'],
            'large': AppTheme.SIZES['button_height'] + 12
        }
        
        button_fonts = {
            'small': AppTheme.FONTS['button'],
            'medium': AppTheme.FONTS['button'],
            'large': AppTheme.FONTS['button_large']
        }
        
        # Configuration par défaut moderne
        defaults = {
            'height': button_heights.get(size, button_heights['medium']),
            'corner_radius': AppTheme.SIZES['border_radius'],
            'font': button_fonts.get(size, button_fonts['medium']),
            'fg_color': colors['fg_color'],
            'hover_color': colors['hover_color'],
            'text_color': colors['text_color'],
            'border_width': 1 if variant in ['outline', 'glass'] else 0,
            'border_color': colors['border_color'],
            'cursor': 'hand2',  # Curseur Windows
        }
        
        # Fusionner avec les kwargs
        config = {**defaults, **kwargs}
        
        super().__init__(parent, text=text, command=command, **config)

class ThemedLabel(ctk.CTkLabel):
    """Label avec thème géodésique moderne."""
    
    def __init__(self, parent, text: str, style: str = 'body', **kwargs):
        
        # Couleurs automatiques selon le style
        style_colors = {
            'display': AppTheme.COLORS['primary'],
            'title': AppTheme.COLORS['text'],
            'heading': AppTheme.COLORS['primary'],
            'subheading': AppTheme.COLORS['secondary'],
            'body': AppTheme.COLORS['text'],
            'small': AppTheme.COLORS['text_secondary'],
            'caption': AppTheme.COLORS['text_muted'],
        }
        
        defaults = {
            'font': AppTheme.FONTS.get(style, AppTheme.FONTS['body']),
            'text_color': style_colors.get(style, AppTheme.COLORS['text']),
        }
        
        config = {**defaults, **kwargs}
        super().__init__(parent, text=text, **config)

class ThemedEntry(ctk.CTkEntry):
    """Champ de saisie avec style moderne."""
    
    def __init__(self, parent, placeholder: str = "", **kwargs):
        
        input_style = AppTheme.get_input_style()
        defaults = {
            **input_style,
            'placeholder_text_color': AppTheme.COLORS['text_muted'],
            'cursor': 'xterm',  # Curseur de saisie
        }
        
        config = {**defaults, **kwargs}
        super().__init__(parent, placeholder_text=placeholder, **config)

class ThemedFrame(ctk.CTkFrame):
    """Frame avec style de carte moderne."""
    
    def __init__(self, parent, elevated: bool = False, glass: bool = False, **kwargs):
        
        if glass:
            # Style glassmorphism
            defaults = {
                'fg_color': AppTheme.COLORS['glass_bg'],
                'corner_radius': AppTheme.SIZES['card_radius'],
                'border_width': 1,
                'border_color': AppTheme.COLORS['glass_border']
            }
        else:
            defaults = AppTheme.get_card_style(elevated=elevated)
        
        config = {**defaults, **kwargs}
        super().__init__(parent, **config)

class TabButton(ctk.CTkButton):
    """Bouton d'onglet avec styles actif/inactif."""
    
    def __init__(self, parent, text: str, tab_index: int, callback: Optional[Callable] = None, **kwargs):
        self.tab_index = tab_index
        self.callback = callback
        self.is_active = False
        self.is_disabled = False
        
        # Configuration initiale (inactif)
        defaults = {
            'height': 40,
            'corner_radius': 8,  # CustomTkinter ne supporte que des radius uniformes
            'font': AppTheme.FONTS['button'],
            'fg_color': AppTheme.COLORS['surface'],
            'hover_color': AppTheme.COLORS['surface_elevated'],
            'text_color': AppTheme.COLORS['text_secondary'],
            'border_width': 1,
            'border_color': AppTheme.COLORS['border'],
            'cursor': 'hand2',
        }
        
        config = {**defaults, **kwargs}
        super().__init__(parent, text=text, command=self._on_click, **config)
    
    def _on_click(self):
        """Gestion du clic sur l'onglet."""
        if not self.is_disabled and self.callback:
            self.callback(self.tab_index)
    
    def set_active(self, active: bool):
        """Active ou désactive visuellement l'onglet."""
        self.is_active = active
        if active:
            self.configure(
                fg_color=AppTheme.COLORS['card_bg'],
                text_color=AppTheme.COLORS['primary'],
                border_color=AppTheme.COLORS['primary']
            )
        else:
            self.configure(
                fg_color=AppTheme.COLORS['surface'],
                text_color=AppTheme.COLORS['text_secondary'],
                border_color=AppTheme.COLORS['border']
            )
    
    def set_disabled(self, disabled: bool):
        """Active ou désactive l'onglet."""
        self.is_disabled = disabled
        if disabled:
            self.configure(
                fg_color=AppTheme.COLORS['background'],
                text_color=AppTheme.COLORS['text_muted'],
                cursor='arrow'
            )
        else:
            self.configure(cursor='hand2')
            self.set_active(self.is_active)

class TabFrame(ThemedFrame):
    """Container pour système d'onglets avec contenu."""
    
    def __init__(self, parent, tabs: List[str], **kwargs):
        super().__init__(parent, **kwargs)
        
        self.tabs = tabs
        self.current_tab = 0
        self.tab_buttons = []
        self.tab_contents = []
        self.tab_callbacks = []
        
        # Configuration du layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self._create_tab_bar()
        self._create_tab_contents()
    
    def _create_tab_bar(self):
        """Crée la barre d'onglets."""
        self.tab_bar = ThemedFrame(self)
        self.tab_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.tab_bar.configure(fg_color=AppTheme.COLORS['background'])
        
        # Créer les boutons d'onglets
        for i, tab_name in enumerate(self.tabs):
            tab_btn = TabButton(
                self.tab_bar, 
                text=tab_name,
                tab_index=i,
                callback=self._switch_tab
            )
            tab_btn.grid(row=0, column=i, padx=(0, 2), pady=5, sticky="ew")
            self.tab_buttons.append(tab_btn)
        
        # Activer le premier onglet
        if self.tab_buttons:
            self.tab_buttons[0].set_active(True)
    
    def _create_tab_contents(self):
        """Crée les conteneurs de contenu des onglets."""
        self.content_frame = ThemedFrame(self)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Créer un frame de contenu pour chaque onglet
        for i in range(len(self.tabs)):
            content = ThemedFrame(self.content_frame)
            content.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            content.grid_rowconfigure(0, weight=1)
            content.grid_columnconfigure(0, weight=1)
            self.tab_contents.append(content)
            
            # Masquer tous sauf le premier
            if i > 0:
                content.grid_remove()
    
    def _switch_tab(self, tab_index: int):
        """Change l'onglet actif."""
        if tab_index == self.current_tab:
            return
            
        # Désactiver l'ancien onglet
        if 0 <= self.current_tab < len(self.tab_buttons):
            self.tab_buttons[self.current_tab].set_active(False)
            self.tab_contents[self.current_tab].grid_remove()
        
        # Activer le nouvel onglet
        self.current_tab = tab_index
        self.tab_buttons[tab_index].set_active(True)
        self.tab_contents[tab_index].grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Appeler le callback si défini
        if tab_index < len(self.tab_callbacks) and self.tab_callbacks[tab_index]:
            self.tab_callbacks[tab_index]()
    
    def get_tab_content(self, tab_index: int) -> 'ThemedFrame':
        """Retourne le frame de contenu d'un onglet."""
        if 0 <= tab_index < len(self.tab_contents):
            return self.tab_contents[tab_index]
        return None
    
    def set_tab_callback(self, tab_index: int, callback: Callable):
        """Définit un callback pour un onglet."""
        while len(self.tab_callbacks) <= tab_index:
            self.tab_callbacks.append(None)
        self.tab_callbacks[tab_index] = callback
    
    def set_tab_disabled(self, tab_index: int, disabled: bool):
        """Active ou désactive un onglet."""
        if 0 <= tab_index < len(self.tab_buttons):
            self.tab_buttons[tab_index].set_disabled(disabled)
    
    def switch_to_tab(self, tab_index: int):
        """Force le passage à un onglet (méthode publique)."""
        if 0 <= tab_index < len(self.tabs):
            self._switch_tab(tab_index)

class ThemedProgressBar(ctk.CTkProgressBar):
    """Barre de progression moderne avec animation."""
    
    def __init__(self, parent, variant: str = 'primary', **kwargs):
        
        # Couleurs selon le variant
        progress_colors = {
            'primary': AppTheme.COLORS['primary'],
            'success': AppTheme.COLORS['success'],
            'warning': AppTheme.COLORS['warning'],
            'accent': AppTheme.COLORS['accent']
        }
        
        defaults = {
            'progress_color': progress_colors.get(variant, AppTheme.COLORS['primary']),
            'fg_color': AppTheme.COLORS['border_light'],
            'corner_radius': AppTheme.SIZES['progress_height'] // 2,
            'height': AppTheme.SIZES['progress_height'],
        }
        
        config = {**defaults, **kwargs}
        super().__init__(parent, **config)

class StepIndicator(ctk.CTkFrame):
    """Indicateur d'étapes moderne avec design géodésique."""
    
    def __init__(self, parent, steps: List[str], current_step: int = 0):
        super().__init__(parent, fg_color='transparent')
        
        self.steps = steps
        self.current_step = current_step
        self.step_widgets = []
        
        self.create_widgets()
    
    def create_widgets(self):
        """Crée les widgets de l'indicateur moderne."""
        for i, step in enumerate(self.steps):
            # Frame pour chaque étape
            step_frame = ctk.CTkFrame(self, fg_color='transparent')
            step_frame.pack(side='left', padx=AppTheme.SPACING['md'], fill='y')
            
            # État de l'étape
            is_current = i == self.current_step
            is_completed = i < self.current_step
            
            # Couleurs modernes selon l'état
            if is_completed:
                circle_color = AppTheme.COLORS['success']
                text_color = AppTheme.COLORS['text_on_primary']
                circle_text = "✓"
                border_color = AppTheme.COLORS['success']
            elif is_current:
                circle_color = AppTheme.COLORS['primary']
                text_color = AppTheme.COLORS['text_on_primary']
                circle_text = str(i + 1)
                border_color = AppTheme.COLORS['primary']
            else:
                circle_color = AppTheme.COLORS['surface']
                text_color = AppTheme.COLORS['text_muted']
                circle_text = str(i + 1)
                border_color = AppTheme.COLORS['border']
            
            # Cercle avec bordure moderne
            circle = ctk.CTkLabel(
                step_frame,
                text=circle_text,
                width=36,
                height=36,
                fg_color=circle_color,
                text_color=text_color,
                font=AppTheme.FONTS['body_medium'],
                corner_radius=18
            )
            circle.pack(pady=(0, AppTheme.SPACING['sm']))
            
            # Label de l'étape avec meilleure hiérarchie
            if is_current:
                label_color = AppTheme.COLORS['primary']
                font_style = 'body_medium'
            elif is_completed:
                label_color = AppTheme.COLORS['text']
                font_style = 'small'
            else:
                label_color = AppTheme.COLORS['text_muted']
                font_style = 'small'
            
            label = ThemedLabel(
                step_frame,
                text=step,
                style=font_style,
                text_color=label_color
            )
            label.pack()
            
            self.step_widgets.append((circle, label))
            
            # Ligne de connexion moderne (sauf pour le dernier)
            if i < len(self.steps) - 1:
                line_color = AppTheme.COLORS['primary'] if is_completed else AppTheme.COLORS['border_light']
                line_height = 3 if is_completed else 2
                
                line = ctk.CTkFrame(
                    self,
                    width=60,
                    height=line_height,
                    fg_color=line_color,
                    corner_radius=line_height//2
                )
                line.pack(side='left', padx=AppTheme.SPACING['sm'], pady=(18, 0))
    
    def update_step(self, new_step: int):
        """Met à jour l'étape courante avec animation."""
        if new_step == self.current_step:
            return
            
        self.current_step = new_step
        
        # Détruire et recréer les widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        self.step_widgets.clear()
        self.create_widgets()

class StatusBar(ctk.CTkFrame):
    """Barre d'état moderne avec indicateurs visuels."""
    
    def __init__(self, parent):
        super().__init__(
            parent,
            height=AppTheme.SIZES['statusbar_height'],
            fg_color=AppTheme.COLORS['surface_elevated'],
            corner_radius=0,
            border_width=1,
            border_color=AppTheme.COLORS['border_light']
        )
        
        # Frame pour les éléments de gauche
        left_frame = ctk.CTkFrame(self, fg_color='transparent')
        left_frame.pack(side='left', fill='both', padx=AppTheme.SPACING['md'])
        
        # Indicateur de statut avec couleur
        self.status_indicator = ctk.CTkLabel(
            left_frame,
            text="●",
            width=12,
            font=AppTheme.FONTS['caption'],
            text_color=AppTheme.COLORS['success']
        )
        self.status_indicator.pack(side='left', pady=AppTheme.SPACING['xs'])
        
        # Label de statut
        self.status_label = ThemedLabel(
            left_frame,
            text="Prêt",
            style='caption',
            text_color=AppTheme.COLORS['text_secondary']
        )
        self.status_label.pack(side='left', padx=(AppTheme.SPACING['xs'], 0), pady=AppTheme.SPACING['xs'])
        
        # Frame pour les éléments de droite
        right_frame = ctk.CTkFrame(self, fg_color='transparent')
        right_frame.pack(side='right', fill='both', padx=AppTheme.SPACING['md'])
        
        # Label de version
        self.version_label = ThemedLabel(
            right_frame,
            text="Compensation Altimétrique v2.0",
            style='caption',
            text_color=AppTheme.COLORS['text_muted']
        )
        self.version_label.pack(side='right', pady=AppTheme.SPACING['xs'])
    
    def set_status(self, message: str, status_type: str = 'info'):
        """Met à jour le message de statut avec type."""
        self.status_label.configure(text=message)
        
        # Couleurs selon le type
        status_colors = {
            'success': AppTheme.COLORS['success'],
            'warning': AppTheme.COLORS['warning'], 
            'error': AppTheme.COLORS['error'],
            'info': AppTheme.COLORS['primary'],
            'idle': AppTheme.COLORS['text_muted']
        }
        
        color = status_colors.get(status_type, AppTheme.COLORS['primary'])
        self.status_indicator.configure(text_color=color)

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

class ModernCard(ThemedFrame):
    """Carte moderne avec en-tête et contenu."""
    
    def __init__(self, parent, title: str = "", icon: str = "", **kwargs):
        super().__init__(parent, elevated=True, **kwargs)
        
        self.title = title
        self.icon = icon
        
        # Padding interne
        self.configure(
            padx=AppTheme.SIZES['card_padding'],
            pady=AppTheme.SIZES['card_padding']
        )
        
        # En-tête si titre fourni
        if title:
            self.header = self._create_header()
            
        # Container pour le contenu
        self.content_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.content_frame.pack(fill='both', expand=True, pady=(AppTheme.SPACING['md'], 0) if title else 0)
    
    def _create_header(self):
        """Crée l'en-tête de la carte."""
        header_frame = ctk.CTkFrame(self, fg_color='transparent')
        header_frame.pack(fill='x', pady=(0, AppTheme.SPACING['md']))
        
        # Icône + titre
        title_frame = ctk.CTkFrame(header_frame, fg_color='transparent')
        title_frame.pack(side='left', fill='x', expand=True)
        
        if self.icon:
            icon_label = ThemedLabel(
                title_frame,
                text=self.icon,
                style='subheading',
                text_color=AppTheme.COLORS['primary']
            )
            icon_label.pack(side='left')
        
        title_label = ThemedLabel(
            title_frame,
            text=self.title,
            style='subheading',
            text_color=AppTheme.COLORS['text']
        )
        title_label.pack(side='left', padx=(AppTheme.SPACING['sm'], 0) if self.icon else 0)
        
        return header_frame
    
    def add_content(self, widget):
        """Ajoute du contenu à la carte."""
        widget.pack(in_=self.content_frame, fill='both', expand=True)

class MetricCard(ModernCard):
    """Carte pour afficher une métrique avec valeur et description."""
    
    def __init__(self, parent, title: str, value: str, description: str = "", 
                 icon: str = "", variant: str = 'primary', **kwargs):
        super().__init__(parent, title=title, icon=icon, **kwargs)
        
        # Couleurs selon le variant
        variant_colors = {
            'primary': AppTheme.COLORS['primary'],
            'success': AppTheme.COLORS['success'],
            'warning': AppTheme.COLORS['warning'],
            'error': AppTheme.COLORS['error'],
            'accent': AppTheme.COLORS['accent']
        }
        
        color = variant_colors.get(variant, AppTheme.COLORS['primary'])
        
        # Valeur principale
        value_label = ThemedLabel(
            self.content_frame,
            text=value,
            style='display',
            text_color=color
        )
        value_label.pack(pady=(AppTheme.SPACING['sm'], 0))
        
        # Description si fournie
        if description:
            desc_label = ThemedLabel(
                self.content_frame,
                text=description,
                style='small',
                text_color=AppTheme.COLORS['text_secondary']
            )
            desc_label.pack(pady=(AppTheme.SPACING['xs'], 0))

class NotificationBanner(ctk.CTkFrame):
    """Bannière de notification moderne."""
    
    def __init__(self, parent, message: str, notification_type: str = 'info', 
                 dismissible: bool = True, **kwargs):
        
        # Couleurs selon le type
        type_styles = {
            'success': {
                'bg': AppTheme.COLORS['success_light'],
                'border': AppTheme.COLORS['success'],
                'text': AppTheme.COLORS['success'],
                'icon': '✅'
            },
            'warning': {
                'bg': AppTheme.COLORS['warning_light'],
                'border': AppTheme.COLORS['warning'],
                'text': AppTheme.COLORS['warning'],
                'icon': '⚠️'
            },
            'error': {
                'bg': AppTheme.COLORS['error_light'],
                'border': AppTheme.COLORS['error'],
                'text': AppTheme.COLORS['error'],
                'icon': '❌'
            },
            'info': {
                'bg': AppTheme.COLORS['info_light'],
                'border': AppTheme.COLORS['info'],
                'text': AppTheme.COLORS['info'],
                'icon': 'ℹ️'
            }
        }
        
        style = type_styles.get(notification_type, type_styles['info'])
        
        super().__init__(
            parent,
            fg_color=style['bg'],
            border_width=1,
            border_color=style['border'],
            corner_radius=AppTheme.SIZES['border_radius'],
            **kwargs
        )
        
        # Frame interne avec padding
        inner_frame = ctk.CTkFrame(self, fg_color='transparent')
        inner_frame.pack(fill='both', expand=True, padx=AppTheme.SPACING['md'], pady=AppTheme.SPACING['sm'])
        
        # Icône
        icon_label = ThemedLabel(
            inner_frame,
            text=style['icon'],
            style='body',
        )
        icon_label.pack(side='left', padx=(0, AppTheme.SPACING['sm']))
        
        # Message
        message_label = ThemedLabel(
            inner_frame,
            text=message,
            style='body',
            text_color=style['text']
        )
        message_label.pack(side='left', fill='x', expand=True)
        
        # Bouton de fermeture
        if dismissible:
            close_button = ThemedButton(
                inner_frame,
                text="×",
                variant='white',
                size='small',
                width=24,
                command=self.dismiss
            )
            close_button.pack(side='right')
    
    def dismiss(self):
        """Ferme la notification."""
        self.destroy()


class StatusCard(ThemedFrame):
    """Carte de statut pour métriques avec icône et valeur."""
    
    def __init__(self, parent, title: str, value: str, icon: str = "", 
                 color: str = None, **kwargs):
        super().__init__(parent, elevated=True, **kwargs)
        
        # Couleur par défaut
        if color is None:
            color = AppTheme.COLORS['primary']
        
        # Container principal
        content_frame = ctk.CTkFrame(self, fg_color='transparent')
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # En-tête avec icône
        header_frame = ctk.CTkFrame(content_frame, fg_color='transparent')
        header_frame.pack(fill='x', pady=(0, 10))
        
        # Icône colorée
        if icon:
            icon_frame = ctk.CTkFrame(
                header_frame,
                width=40,
                height=40,
                corner_radius=20,
                fg_color=color
            )
            icon_frame.pack(side='left')
            icon_frame.pack_propagate(False)
            
            icon_label = ThemedLabel(
                icon_frame,
                text=icon,
                style='subheading',
                text_color='white'
            )
            icon_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Titre
        title_label = ThemedLabel(
            content_frame,
            text=title,
            style='small',
            text_color=AppTheme.COLORS['text_secondary']
        )
        title_label.pack(anchor='w', pady=(0, 5))
        
        # Valeur principale
        value_label = ThemedLabel(
            content_frame,
            text=value,
            style='heading',
            text_color=color
        )
        value_label.pack(anchor='w')


class ProgressCard(ThemedFrame):
    """Carte de progression avec barre et pourcentage."""
    
    def __init__(self, parent, title: str, progress: float = 0.0, 
                 description: str = "", **kwargs):
        super().__init__(parent, elevated=True, **kwargs)
        
        # Container principal
        content_frame = ctk.CTkFrame(self, fg_color='transparent')
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Titre
        title_label = ThemedLabel(
            content_frame,
            text=title,
            style='subheading',
            text_color=AppTheme.COLORS['text']
        )
        title_label.pack(anchor='w', pady=(0, 10))
        
        # Barre de progression
        self.progress_bar = ThemedProgressBar(content_frame)
        self.progress_bar.pack(fill='x', pady=(0, 8))
        self.progress_bar.set(progress)
        
        # Frame pour pourcentage et description
        info_frame = ctk.CTkFrame(content_frame, fg_color='transparent')
        info_frame.pack(fill='x')
        
        # Pourcentage
        percent_label = ThemedLabel(
            info_frame,
            text=f"{progress*100:.0f}%",
            style='body_medium',
            text_color=AppTheme.COLORS['primary']
        )
        percent_label.pack(side='right')
        
        # Description
        if description:
            desc_label = ThemedLabel(
                info_frame,
                text=description,
                style='small',
                text_color=AppTheme.COLORS['text_secondary']
            )
            desc_label.pack(side='left')
    
    def update_progress(self, progress: float, description: str = None):
        """Met à jour la progression."""
        self.progress_bar.set(progress)
        
        # Mettre à jour les labels
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkFrame):  # info_frame
                        for subchild in child.winfo_children():
                            if isinstance(subchild, ThemedLabel):
                                if "%" in subchild.cget("text"):
                                    subchild.configure(text=f"{progress*100:.0f}%")
                                elif description and subchild.cget("text") != description:
                                    subchild.configure(text=description)


class ProjectCard(ThemedFrame):
    """Carte de projet avec informations et actions."""
    
    def __init__(self, parent, project_data: dict, callback=None, **kwargs):
        super().__init__(parent, elevated=True, **kwargs)
        
        self.project_data = project_data
        self.callback = callback
        
        # Effet hover
        self.configure(cursor='hand2')
        self.bind('<Button-1>', self._on_click)
        
        # Container principal
        content_frame = ctk.CTkFrame(self, fg_color='transparent')
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        content_frame.bind('<Button-1>', self._on_click)
        
        # En-tête du projet
        header_frame = ctk.CTkFrame(content_frame, fg_color='transparent')
        header_frame.pack(fill='x', pady=(0, 12))
        header_frame.bind('<Button-1>', self._on_click)
        
        # Nom du projet
        name_label = ThemedLabel(
            header_frame,
            text=project_data.get('name', 'Projet sans nom'),
            style='subheading',
            text_color=AppTheme.COLORS['text']
        )
        name_label.pack(anchor='w')
        name_label.bind('<Button-1>', self._on_click)
        
        # Badge de statut
        status = project_data.get('status', 'draft')
        status_colors = {
            'completed': AppTheme.COLORS['success'],
            'in_progress': AppTheme.COLORS['warning'],
            'draft': AppTheme.COLORS['text_muted']
        }
        status_texts = {
            'completed': 'Terminé',
            'in_progress': 'En cours', 
            'draft': 'Brouillon'
        }
        
        status_badge = ctk.CTkFrame(
            header_frame,
            fg_color=status_colors.get(status, AppTheme.COLORS['text_muted']),
            corner_radius=10,
            height=20
        )
        status_badge.pack(side='right')
        
        status_label = ThemedLabel(
            status_badge,
            text=status_texts.get(status, status.capitalize()),
            style='caption',
            text_color='white'
        )
        status_label.pack(padx=8, pady=2)
        
        # Description
        if project_data.get('description'):
            desc_label = ThemedLabel(
                content_frame,
                text=project_data['description'],
                style='small',
                text_color=AppTheme.COLORS['text_secondary']
            )
            desc_label.pack(anchor='w', pady=(0, 12))
            desc_label.bind('<Button-1>', self._on_click)
        
        # Métriques du projet
        metrics_frame = ctk.CTkFrame(content_frame, fg_color='transparent')
        metrics_frame.pack(fill='x', pady=(0, 12))
        metrics_frame.bind('<Button-1>', self._on_click)
        
        # Points traités
        points_count = project_data.get('points_count', 0)
        points_metric = ThemedLabel(
            metrics_frame,
            text=f"📍 {points_count} points",
            style='small',
            text_color=AppTheme.COLORS['text_secondary']
        )
        points_metric.pack(side='left', padx=(0, 15))
        points_metric.bind('<Button-1>', self._on_click)
        
        # Précision si disponible
        precision = project_data.get('precision_achieved')
        if precision:
            precision_metric = ThemedLabel(
                metrics_frame,
                text=f"🎯 {precision:.1f}mm",
                style='small', 
                text_color=AppTheme.COLORS['success']
            )
            precision_metric.pack(side='left')
            precision_metric.bind('<Button-1>', self._on_click)
        
        # Date de modification
        import datetime
        try:
            modified_date = datetime.datetime.fromisoformat(project_data.get('modified_date', ''))
            date_str = modified_date.strftime('%d/%m/%Y')
        except:
            date_str = 'Date inconnue'
        
        date_label = ThemedLabel(
            content_frame,
            text=f"Modifié le {date_str}",
            style='caption',
            text_color=AppTheme.COLORS['text_muted']
        )
        date_label.pack(anchor='w')
        date_label.bind('<Button-1>', self._on_click)
        
        # Effet hover sur la carte
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
    
    def _on_click(self, event):
        """Gestion du clic sur la carte."""
        if self.callback:
            self.callback(self.project_data)
    
    def _on_enter(self, event):
        """Effet hover."""
        self.configure(fg_color=AppTheme.COLORS['background'])
    
    def _on_leave(self, event):
        """Fin effet hover."""
        self.configure(fg_color=AppTheme.COLORS['surface_elevated'])