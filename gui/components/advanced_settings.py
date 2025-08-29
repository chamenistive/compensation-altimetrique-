"""
Configuration avancée des paramètres pour le Système de Compensation Altimétrique.
Interface experte avec paramètres géodésiques, méthodes LSQ et optimisations.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .base_components import (
    ThemedButton, ThemedLabel, ThemedFrame, ThemedEntry,
    StatusCard, NotificationBanner
)
from ..utils.theme import AppTheme


class ParameterGroup(ThemedFrame):
    """Groupe de paramètres avec titre et description."""
    
    def __init__(self, parent, title: str, description: str = "", icon: str = "", **kwargs):
        super().__init__(parent, elevated=True, **kwargs)
        
        self.title = title
        self.description = description
        self.icon = icon
        self.parameters = {}
        
        self.create_group_interface()
    
    def create_group_interface(self):
        """Crée l'interface du groupe."""
        
        # En-tête du groupe
        header_frame = ctk.CTkFrame(self, fg_color='transparent')
        header_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        # Titre avec icône
        title_frame = ctk.CTkFrame(header_frame, fg_color='transparent')
        title_frame.pack(side='left')
        
        if self.icon:
            icon_label = ThemedLabel(
                title_frame,
                text=self.icon,
                style='subheading',
                text_color=AppTheme.COLORS['primary']
            )
            icon_label.pack(side='left', padx=(0, 10))
        
        title_label = ThemedLabel(
            title_frame,
            text=self.title,
            style='subheading',
            text_color=AppTheme.COLORS['text']
        )
        title_label.pack(side='left')
        
        # Description
        if self.description:
            desc_label = ThemedLabel(
                self,
                text=self.description,
                style='small',
                text_color=AppTheme.COLORS['text_secondary']
            )
            desc_label.pack(anchor='w', padx=20, pady=(0, 15))
        
        # Container pour les paramètres
        self.params_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.params_frame.pack(fill='x', padx=20, pady=(0, 20))
    
    def add_parameter(self, param_id: str, label: str, param_type: str = 'entry', 
                     default_value: Any = "", options: List = None, 
                     tooltip: str = "", unit: str = ""):
        """Ajoute un paramètre au groupe."""
        
        param_frame = ctk.CTkFrame(self.params_frame, fg_color='transparent')
        param_frame.pack(fill='x', pady=5)
        param_frame.grid_columnconfigure(1, weight=1)
        
        # Label avec unité
        label_text = f"{label}:" + (f" ({unit})" if unit else "")
        param_label = ThemedLabel(
            param_frame,
            text=label_text,
            style='body',
            text_color=AppTheme.COLORS['text']
        )
        param_label.grid(row=0, column=0, sticky='w', padx=(0, 15))
        
        # Widget selon le type
        if param_type == 'entry':
            widget = ThemedEntry(
                param_frame,
                placeholder=str(default_value)
            )
            widget.insert(0, str(default_value))
            widget.grid(row=0, column=1, sticky='ew', padx=(0, 10))
            
        elif param_type == 'dropdown':
            widget = ctk.CTkOptionMenu(
                param_frame,
                values=options or ["Option 1", "Option 2"],
                font=AppTheme.FONTS['body'],
                fg_color=AppTheme.COLORS['surface'],
                button_color=AppTheme.COLORS['primary']
            )
            if default_value in (options or []):
                widget.set(default_value)
            widget.grid(row=0, column=1, sticky='ew', padx=(0, 10))
            
        elif param_type == 'checkbox':
            var = ctk.BooleanVar(value=bool(default_value))
            widget = ctk.CTkCheckBox(
                param_frame,
                text="",
                variable=var,
                font=AppTheme.FONTS['body'],
                fg_color=AppTheme.COLORS['primary']
            )
            widget.grid(row=0, column=1, sticky='w', padx=(0, 10))
            
        elif param_type == 'slider':
            widget = ctk.CTkSlider(
                param_frame,
                from_=options[0] if options and len(options) >= 2 else 0,
                to=options[1] if options and len(options) >= 2 else 100,
                number_of_steps=options[2] if options and len(options) >= 3 else 100
            )
            widget.set(float(default_value) if default_value else 0)
            widget.grid(row=0, column=1, sticky='ew', padx=(0, 10))
        
        # Bouton d'aide si tooltip
        if tooltip:
            help_button = ThemedButton(
                param_frame,
                text="?",
                command=lambda: self.show_parameter_help(label, tooltip),
                variant='ghost',
                size='small',
                width=30
            )
            help_button.grid(row=0, column=2)
        
        # Stocker la référence
        self.parameters[param_id] = {
            'widget': widget,
            'type': param_type,
            'default': default_value,
            'label': label,
            'unit': unit
        }
    
    def show_parameter_help(self, label: str, tooltip: str):
        """Affiche l'aide pour un paramètre."""
        messagebox.showinfo(f"Aide - {label}", tooltip)
    
    def get_value(self, param_id: str) -> Any:
        """Récupère la valeur d'un paramètre."""
        if param_id not in self.parameters:
            return None
        
        param = self.parameters[param_id]
        widget = param['widget']
        param_type = param['type']
        
        try:
            if param_type == 'entry':
                return widget.get()
            elif param_type == 'dropdown':
                return widget.get()
            elif param_type == 'checkbox':
                return widget.cget('variable').get()
            elif param_type == 'slider':
                return widget.get()
        except:
            return param['default']
    
    def set_value(self, param_id: str, value: Any):
        """Définit la valeur d'un paramètre."""
        if param_id not in self.parameters:
            return
        
        param = self.parameters[param_id]
        widget = param['widget']
        param_type = param['type']
        
        try:
            if param_type == 'entry':
                widget.delete(0, 'end')
                widget.insert(0, str(value))
            elif param_type == 'dropdown':
                widget.set(str(value))
            elif param_type == 'checkbox':
                widget.cget('variable').set(bool(value))
            elif param_type == 'slider':
                widget.set(float(value))
        except:
            pass
    
    def get_all_values(self) -> Dict[str, Any]:
        """Récupère toutes les valeurs du groupe."""
        return {
            param_id: self.get_value(param_id)
            for param_id in self.parameters.keys()
        }


class PresetManager(ThemedFrame):
    """Gestionnaire de presets de configuration."""
    
    def __init__(self, parent, callback=None, **kwargs):
        super().__init__(parent, elevated=True, **kwargs)
        
        self.callback = callback
        self.presets_file = Path("data/configuration_presets.json")
        self.presets = self.load_presets()
        
        self.create_preset_interface()
    
    def create_preset_interface(self):
        """Crée l'interface de gestion des presets."""
        
        # En-tête
        header_frame = ctk.CTkFrame(self, fg_color='transparent')
        header_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        title_label = ThemedLabel(
            header_frame,
            text="💾 Presets de Configuration",
            style='subheading',
            text_color=AppTheme.COLORS['text']
        )
        title_label.pack(side='left')
        
        # Contrôles
        controls_frame = ctk.CTkFrame(header_frame, fg_color='transparent')
        controls_frame.pack(side='right')
        
        # Sélecteur de preset
        preset_names = list(self.presets.keys()) + ["Configuration personnalisée"]
        self.preset_var = ctk.StringVar(value=preset_names[0] if preset_names else "Aucun preset")
        
        self.preset_selector = ctk.CTkOptionMenu(
            controls_frame,
            variable=self.preset_var,
            values=preset_names,
            command=self.on_preset_selected,
            font=AppTheme.FONTS['body'],
            fg_color=AppTheme.COLORS['surface'],
            button_color=AppTheme.COLORS['primary']
        )
        self.preset_selector.pack(side='left', padx=(0, 10))
        
        # Boutons d'action
        save_button = ThemedButton(
            controls_frame,
            text="💾 Sauver",
            command=self.save_current_preset,
            variant='primary',
            size='small'
        )
        save_button.pack(side='left', padx=(0, 5))
        
        delete_button = ThemedButton(
            controls_frame,
            text="🗑️",
            command=self.delete_preset,
            variant='outline',
            size='small',
            width=40
        )
        delete_button.pack(side='left')
        
        # Description du preset sélectionné
        self.preset_info = ThemedLabel(
            self,
            text="",
            style='small',
            text_color=AppTheme.COLORS['text_secondary']
        )
        self.preset_info.pack(anchor='w', padx=20, pady=(0, 15))
        
        # Mettre à jour l'info
        self.update_preset_info()
    
    def load_presets(self) -> Dict[str, Any]:
        """Charge les presets depuis le fichier."""
        try:
            if self.presets_file.exists():
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erreur chargement presets: {e}")
        
        # Presets par défaut
        return {
            "Précision Standard (2mm)": {
                "description": "Configuration standard pour précision 2mm",
                "parameters": {
                    "precision_target": 2.0,
                    "weight_method": "Distance inverse",
                    "convergence_tolerance": 0.1,
                    "max_iterations": 50,
                    "atmospheric_corrections": True,
                    "temperature": 20.0,
                    "pressure": 1013.25,
                    "humidity": 50.0
                }
            },
            "Haute Précision (1mm)": {
                "description": "Configuration pour travaux haute précision",
                "parameters": {
                    "precision_target": 1.0,
                    "weight_method": "Distance inverse au carré",
                    "convergence_tolerance": 0.05,
                    "max_iterations": 100,
                    "atmospheric_corrections": True,
                    "temperature": 20.0,
                    "pressure": 1013.25,
                    "humidity": 50.0
                }
            },
            "Géodésie IGN": {
                "description": "Standards IGN pour géodésie française",
                "parameters": {
                    "precision_target": 1.5,
                    "weight_method": "Distance inverse",
                    "convergence_tolerance": 0.08,
                    "max_iterations": 75,
                    "atmospheric_corrections": True,
                    "temperature": 15.0,
                    "pressure": 1013.25,
                    "humidity": 60.0
                }
            }
        }
    
    def save_presets(self):
        """Sauvegarde les presets."""
        try:
            self.presets_file.parent.mkdir(exist_ok=True)
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(self.presets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde presets: {e}")
    
    def on_preset_selected(self, preset_name: str):
        """Gère la sélection d'un preset."""
        if preset_name == "Configuration personnalisée":
            return
        
        if preset_name in self.presets and self.callback:
            self.callback('load_preset', self.presets[preset_name]['parameters'])
        
        self.update_preset_info()
    
    def update_preset_info(self):
        """Met à jour les informations du preset."""
        preset_name = self.preset_var.get()
        if preset_name in self.presets:
            description = self.presets[preset_name].get('description', 'Pas de description')
            self.preset_info.configure(text=f"📝 {description}")
        else:
            self.preset_info.configure(text="")
    
    def save_current_preset(self):
        """Sauvegarde la configuration actuelle comme preset."""
        if not self.callback:
            return
        
        # Demander le nom du preset
        dialog = ctk.CTkInputDialog(
            text="Nom du nouveau preset:",
            title="Sauvegarder Configuration"
        )
        name = dialog.get_input()
        
        if name:
            # Récupérer la configuration actuelle
            current_config = self.callback('get_current_config')
            if current_config:
                self.presets[name] = {
                    "description": f"Configuration personnalisée créée le {datetime.now().strftime('%d/%m/%Y')}",
                    "parameters": current_config
                }
                
                # Sauvegarder et mettre à jour l'interface
                self.save_presets()
                self.update_preset_selector()
                self.preset_var.set(name)
                self.update_preset_info()
                
                messagebox.showinfo("Succès", f"Preset '{name}' sauvegardé avec succès!")
    
    def delete_preset(self):
        """Supprime le preset sélectionné."""
        preset_name = self.preset_var.get()
        
        if preset_name in self.presets:
            result = messagebox.askyesno(
                "Confirmer suppression",
                f"Voulez-vous vraiment supprimer le preset '{preset_name}' ?"
            )
            
            if result:
                del self.presets[preset_name]
                self.save_presets()
                self.update_preset_selector()
                
                # Sélectionner le premier preset disponible
                remaining_presets = list(self.presets.keys())
                if remaining_presets:
                    self.preset_var.set(remaining_presets[0])
                else:
                    self.preset_var.set("Configuration personnalisée")
                
                self.update_preset_info()
                messagebox.showinfo("Suppression", f"Preset '{preset_name}' supprimé.")
    
    def update_preset_selector(self):
        """Met à jour le sélecteur de presets."""
        preset_names = list(self.presets.keys()) + ["Configuration personnalisée"]
        self.preset_selector.configure(values=preset_names)


class AdvancedSettingsPanel(ctk.CTkScrollableFrame):
    """Panel principal de configuration avancée."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configuration scrollbar
        self.configure(
            scrollbar_button_color=AppTheme.COLORS['primary'],
            scrollbar_button_hover_color=AppTheme.COLORS['primary_dark']
        )
        
        # Groupes de paramètres
        self.parameter_groups = {}
        self.current_config = {}
        
        # Créer l'interface
        self.create_settings_interface()
    
    def create_settings_interface(self):
        """Crée l'interface de configuration avancée."""
        
        # En-tête principal
        self.create_main_header()
        
        # Gestionnaire de presets
        self.create_preset_manager()
        
        # Groupes de paramètres
        self.create_parameter_groups()
        
        # Actions et validation
        self.create_actions_panel()
    
    def create_main_header(self):
        """Crée l'en-tête principal."""
        
        header_frame = ctk.CTkFrame(self, fg_color='transparent')
        header_frame.pack(fill='x', pady=(20, 30))
        
        # Titre principal
        main_title = ThemedLabel(
            header_frame,
            text="⚙️ Configuration Avancée",
            style='title',
            text_color=AppTheme.COLORS['primary']
        )
        main_title.pack()
        
        # Sous-titre
        subtitle = ThemedLabel(
            header_frame,
            text="Paramètres géodésiques experts et optimisations LSQ",
            style='body',
            text_color=AppTheme.COLORS['text_secondary']
        )
        subtitle.pack(pady=(5, 0))
    
    def create_preset_manager(self):
        """Crée le gestionnaire de presets."""
        
        self.preset_manager = PresetManager(
            self,
            callback=self.handle_preset_action
        )
        self.preset_manager.pack(fill='x', pady=(0, 20))
    
    def create_parameter_groups(self):
        """Crée les groupes de paramètres."""
        
        # 1. Paramètres de précision
        precision_group = ParameterGroup(
            self,
            title="Paramètres de Précision",
            description="Configuration des objectifs de précision et tolérances",
            icon="🎯"
        )
        precision_group.pack(fill='x', pady=(0, 15))
        
        precision_group.add_parameter(
            'precision_target', 'Précision cible', 'entry', '2.0', unit='mm',
            tooltip="Précision visée pour la compensation (recommandé: 1-3mm)"
        )
        precision_group.add_parameter(
            'convergence_tolerance', 'Tolérance convergence', 'entry', '0.1', unit='mm',
            tooltip="Seuil d'arrêt pour la convergence LSQ"
        )
        precision_group.add_parameter(
            'max_iterations', 'Itérations maximales', 'entry', '50',
            tooltip="Nombre maximum d'itérations pour la résolution LSQ"
        )
        
        self.parameter_groups['precision'] = precision_group
        
        # 2. Méthodes de compensation
        methods_group = ParameterGroup(
            self,
            title="Méthodes de Compensation",
            description="Algorithmes et pondérations pour la compensation LSQ",
            icon="⚖️"
        )
        methods_group.pack(fill='x', pady=(0, 15))
        
        methods_group.add_parameter(
            'weight_method', 'Méthode de pondération', 'dropdown', 'Distance inverse',
            options=['Distance inverse', 'Distance inverse au carré', 'Uniforme', 'Personnalisée'],
            tooltip="Méthode de calcul des poids pour la compensation"
        )
        methods_group.add_parameter(
            'constraint_type', 'Type de contraintes', 'dropdown', 'Point fixe',
            options=['Point fixe', 'Points fixes multiples', 'Contraintes relatives'],
            tooltip="Type de contraintes appliquées au réseau"
        )
        methods_group.add_parameter(
            'adjustment_method', 'Méthode d\'ajustement', 'dropdown', 'Moindres carrés',
            options=['Moindres carrés', 'Moindres carrés pondérés', 'Estimation robuste'],
            tooltip="Algorithme d'ajustement utilisé"
        )
        
        self.parameter_groups['methods'] = methods_group
        
        # 3. Corrections atmosphériques
        atm_group = ParameterGroup(
            self,
            title="Corrections Atmosphériques",
            description="Paramètres de correction des effets atmosphériques",
            icon="🌡️"
        )
        atm_group.pack(fill='x', pady=(0, 15))
        
        atm_group.add_parameter(
            'atmospheric_corrections', 'Activer corrections', 'checkbox', True,
            tooltip="Active/désactive les corrections atmosphériques"
        )
        atm_group.add_parameter(
            'temperature', 'Température', 'entry', '20.0', unit='°C',
            tooltip="Température ambiante pour les corrections"
        )
        atm_group.add_parameter(
            'pressure', 'Pression', 'entry', '1013.25', unit='hPa',
            tooltip="Pression atmosphérique"
        )
        atm_group.add_parameter(
            'humidity', 'Humidité relative', 'entry', '50.0', unit='%',
            tooltip="Humidité relative de l'air"
        )
        atm_group.add_parameter(
            'refraction_coefficient', 'Coefficient de réfraction', 'entry', '0.13',
            tooltip="Coefficient de réfraction atmosphérique"
        )
        
        self.parameter_groups['atmospheric'] = atm_group
        
        # 4. Paramètres géodésiques
        geodetic_group = ParameterGroup(
            self,
            title="Paramètres Géodésiques",
            description="Systèmes de référence et transformations",
            icon="🌍"
        )
        geodetic_group.pack(fill='x', pady=(0, 15))
        
        geodetic_group.add_parameter(
            'reference_system', 'Système de référence', 'dropdown', 'RGF93',
            options=['RGF93', 'NTF', 'WGS84', 'ETRS89'],
            tooltip="Système de référence géodésique utilisé"
        )
        geodetic_group.add_parameter(
            'ellipsoid', 'Ellipsoïde', 'dropdown', 'GRS80',
            options=['GRS80', 'Clarke 1880', 'WGS84', 'Bessel 1841'],
            tooltip="Ellipsoïde de référence"
        )
        geodetic_group.add_parameter(
            'geoid_model', 'Modèle de géoïde', 'dropdown', 'RAF20',
            options=['RAF20', 'RAF18', 'RAF09', 'Aucun'],
            tooltip="Modèle de géoïde pour les corrections altimétriques"
        )
        geodetic_group.add_parameter(
            'projection', 'Projection', 'dropdown', 'Lambert 93',
            options=['Lambert 93', 'Lambert CC', 'UTM', 'Aucune'],
            tooltip="Système de projection cartographique"
        )
        
        self.parameter_groups['geodetic'] = geodetic_group
        
        # 5. Options avancées
        advanced_group = ParameterGroup(
            self,
            title="Options Avancées",
            description="Paramètres experts et optimisations",
            icon="🔧"
        )
        advanced_group.pack(fill='x', pady=(0, 15))
        
        advanced_group.add_parameter(
            'outlier_detection', 'Détection d\'aberrants', 'checkbox', True,
            tooltip="Active la détection automatique des mesures aberrantes"
        )
        advanced_group.add_parameter(
            'outlier_threshold', 'Seuil aberrants', 'entry', '3.0', unit='σ',
            tooltip="Seuil statistique pour la détection d'aberrants"
        )
        advanced_group.add_parameter(
            'variance_estimation', 'Estimation variance', 'dropdown', 'Automatique',
            options=['Automatique', 'Manuelle', 'À partir des résidus'],
            tooltip="Méthode d'estimation de la variance a priori"
        )
        advanced_group.add_parameter(
            'correlation_model', 'Modèle corrélation', 'dropdown', 'Aucune',
            options=['Aucune', 'Exponentielle', 'Gaussienne', 'Personnalisée'],
            tooltip="Modèle de corrélation spatiale des erreurs"
        )
        
        self.parameter_groups['advanced'] = advanced_group
    
    def create_actions_panel(self):
        """Crée le panneau d'actions."""
        
        actions_frame = ThemedFrame(self, elevated=True)
        actions_frame.pack(fill='x', pady=(20, 0))
        
        # Titre
        actions_title = ThemedLabel(
            actions_frame,
            text="🔧 Actions",
            style='subheading',
            text_color=AppTheme.COLORS['text']
        )
        actions_title.pack(padx=20, pady=(20, 10), anchor='w')
        
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(actions_frame, fg_color='transparent')
        buttons_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # Validation
        validate_button = ThemedButton(
            buttons_frame,
            text="✅ Valider Configuration",
            command=self.validate_configuration,
            variant='primary'
        )
        validate_button.pack(side='left')
        
        # Reset
        reset_button = ThemedButton(
            buttons_frame,
            text="🔄 Réinitialiser",
            command=self.reset_to_defaults,
            variant='outline'
        )
        reset_button.pack(side='left', padx=(10, 0))
        
        # Import/Export
        import_button = ThemedButton(
            buttons_frame,
            text="📁 Importer",
            command=self.import_configuration,
            variant='ghost'
        )
        import_button.pack(side='right')
        
        export_button = ThemedButton(
            buttons_frame,
            text="💾 Exporter",
            command=self.export_configuration,
            variant='ghost'
        )
        export_button.pack(side='right', padx=(0, 10))
    
    def handle_preset_action(self, action: str, data: Any = None):
        """Gère les actions des presets."""
        
        if action == 'load_preset':
            self.load_preset_values(data)
        elif action == 'get_current_config':
            return self.get_current_configuration()
    
    def load_preset_values(self, preset_data: Dict[str, Any]):
        """Charge les valeurs d'un preset."""
        
        for group_name, group in self.parameter_groups.items():
            for param_id, param_info in group.parameters.items():
                if param_id in preset_data:
                    group.set_value(param_id, preset_data[param_id])
    
    def get_current_configuration(self) -> Dict[str, Any]:
        """Récupère la configuration actuelle."""
        
        config = {}
        for group_name, group in self.parameter_groups.items():
            config.update(group.get_all_values())
        
        return config
    
    def validate_configuration(self):
        """Valide la configuration actuelle."""
        
        config = self.get_current_configuration()
        errors = []
        warnings = []
        
        # Validation des valeurs numériques
        try:
            precision = float(config.get('precision_target', 2.0))
            if precision <= 0 or precision > 10:
                errors.append("La précision cible doit être entre 0.1 et 10mm")
                
            tolerance = float(config.get('convergence_tolerance', 0.1))
            if tolerance <= 0 or tolerance > 1:
                errors.append("La tolérance de convergence doit être entre 0.01 et 1mm")
                
            max_iter = int(config.get('max_iterations', 50))
            if max_iter < 10 or max_iter > 1000:
                errors.append("Le nombre d'itérations doit être entre 10 et 1000")
                
        except ValueError:
            errors.append("Certaines valeurs numériques ne sont pas valides")
        
        # Validations spécifiques
        if config.get('atmospheric_corrections'):
            try:
                temp = float(config.get('temperature', 20))
                if temp < -50 or temp > 60:
                    warnings.append("Température hors plage normale (-50°C à 60°C)")
            except:
                errors.append("Température invalide")
        
        # Afficher les résultats
        if errors:
            error_text = "Erreurs de validation :\n\n" + "\n".join(f"• {err}" for err in errors)
            messagebox.showerror("Validation échouée", error_text)
        elif warnings:
            warning_text = "Avertissements :\n\n" + "\n".join(f"• {warn}" for warn in warnings)
            warning_text += "\n\nContinuer avec cette configuration ?"
            if messagebox.askyesno("Validation avec avertissements", warning_text):
                messagebox.showinfo("Configuration validée", "Configuration acceptée avec avertissements")
        else:
            messagebox.showinfo("Validation réussie", "✅ Configuration valide et optimale !")
        
        return len(errors) == 0
    
    def reset_to_defaults(self):
        """Remet les paramètres par défaut."""
        
        result = messagebox.askyesno(
            "Réinitialiser",
            "Voulez-vous vraiment remettre tous les paramètres par défaut ?"
        )
        
        if result:
            for group_name, group in self.parameter_groups.items():
                for param_id, param_info in group.parameters.items():
                    group.set_value(param_id, param_info['default'])
            
            messagebox.showinfo("Réinitialisation", "Paramètres remis par défaut")
    
    def export_configuration(self):
        """Exporte la configuration vers un fichier."""
        
        config = self.get_current_configuration()
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Exporter la configuration"
        )
        
        if filepath:
            try:
                export_data = {
                    "metadata": {
                        "export_date": datetime.now().isoformat(),
                        "version": "2.0",
                        "description": "Configuration système de compensation altimétrique"
                    },
                    "configuration": config
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Export réussi", f"Configuration exportée vers :\n{filepath}")
            except Exception as e:
                messagebox.showerror("Erreur d'export", f"Impossible d'exporter :\n{str(e)}")
    
    def import_configuration(self):
        """Importe une configuration depuis un fichier."""
        
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Importer une configuration"
        )
        
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extraire la configuration
                if "configuration" in data:
                    config = data["configuration"]
                else:
                    config = data  # Format ancien
                
                # Charger les valeurs
                self.load_preset_values(config)
                
                messagebox.showinfo("Import réussi", f"Configuration importée depuis :\n{filepath}")
            except Exception as e:
                messagebox.showerror("Erreur d'import", f"Impossible d'importer :\n{str(e)}")


class AdvancedSettingsWindow(ctk.CTkToplevel):
    """Fenêtre de configuration avancée."""
    
    def __init__(self, parent, current_config: Dict = None):
        super().__init__(parent)
        
        self.current_config = current_config or {}
        
        # Configuration fenêtre
        self.title("⚙️ Configuration Avancée - Système de Compensation Altimétrique")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        
        self.configure(fg_color=AppTheme.COLORS['background'])
        self.center_window()
        
        # Créer l'interface
        self.create_interface()
    
    def center_window(self):
        """Centre la fenêtre."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width - 1200) // 2
        y = (screen_height - 800) // 2
        
        self.geometry(f"1200x800+{x}+{y}")
    
    def create_interface(self):
        """Crée l'interface de la fenêtre."""
        
        # Panel de configuration
        self.settings_panel = AdvancedSettingsPanel(self)
        self.settings_panel.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Charger la configuration actuelle si fournie
        if self.current_config:
            self.settings_panel.load_preset_values(self.current_config)