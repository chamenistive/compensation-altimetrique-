# 🎨 Guide de Développement UI/UX - Compensation Altimétrique

## 🎯 **Utilisation du Nouveau Thème Géodésique**

### 📦 Import des Composants

```python
from gui.utils.theme import AppTheme
from gui.components.base_components import (
    ThemedButton, ThemedLabel, ThemedFrame, 
    ThemedEntry, ThemedProgressBar,
    StepIndicator, StatusBar, ModernCard, 
    MetricCard, NotificationBanner
)
```

---

## 🎨 **Système de Couleurs**

### 🏗️ Couleurs Principales
```python
# Couleurs géodésiques
AppTheme.COLORS['primary']          # #2E86AB - Bleu géodésique
AppTheme.COLORS['secondary']        # #A23B72 - Magenta technique
AppTheme.COLORS['accent']           # #F18F01 - Orange précision

# Surfaces modernes
AppTheme.COLORS['background']       # #F8FAFC - Arrière-plan
AppTheme.COLORS['surface']          # #FFFFFF - Cartes
AppTheme.COLORS['surface_elevated'] # #FDFDFD - Éléments surélevés
```

### ✅ États de Validation
```python
AppTheme.COLORS['success']          # #10B981 - Vert
AppTheme.COLORS['warning']          # #F59E0B - Jaune  
AppTheme.COLORS['error']            # #EF4444 - Rouge
AppTheme.COLORS['info']             # #3B82F6 - Bleu info
```

---

## 🔘 **Composants Modernes**

### 🎛️ Boutons Thématisés
```python
# Bouton principal (bleu géodésique)
primary_btn = ThemedButton(
    parent, 
    text="Calculer", 
    variant='primary',
    size='large',
    command=self.calculate
)

# Bouton secondaire (magenta technique)
secondary_btn = ThemedButton(
    parent, 
    text="Paramètres", 
    variant='secondary',
    size='medium'
)

# Bouton accent (orange précision)
accent_btn = ThemedButton(
    parent, 
    text="Export", 
    variant='accent'
)

# Boutons utilitaires
outline_btn = ThemedButton(parent, text="Annuler", variant='outline')
ghost_btn = ThemedButton(parent, text="Aide", variant='ghost')
glass_btn = ThemedButton(parent, text="Options", variant='glass')
```

### 🏷️ Labels Hiérarchiques
```python
# Titre principal (32px, bleu géodésique)
title = ThemedLabel(parent, text="Compensation Altimétrique", style='display')

# Titre de page (24px)
page_title = ThemedLabel(parent, text="Import des Données", style='title')

# Titre de section (18px, magenta)  
section = ThemedLabel(parent, text="Paramètres", style='heading')

# Sous-titre (14px, magenta)
subtitle = ThemedLabel(parent, text="Configuration", style='subheading')

# Texte principal (12px)
body = ThemedLabel(parent, text="Description...", style='body')

# Petit texte (10px, gris)
small = ThemedLabel(parent, text="Détails", style='small')
```

### 🏗️ Conteneurs Modernes
```python
# Carte standard
card = ThemedFrame(parent)

# Carte élevée avec ombre
elevated_card = ThemedFrame(parent, elevated=True)

# Carte avec effet glassmorphism
glass_card = ThemedFrame(parent, glass=True)

# Carte moderne avec titre et icône
modern_card = ModernCard(parent, title="Résultats", icon="📊")
modern_card.add_content(content_widget)
```

---

## 📊 **Cartes de Métriques**

### 🎯 Affichage de Données
```python
# Métrique de précision (orange)
precision_card = MetricCard(
    parent,
    title="Précision Atteinte", 
    value="1.8 mm",
    description="Objectif : 2.0 mm",
    icon="🎯",
    variant='accent'
)

# Métrique de validation (vert)
success_card = MetricCard(
    parent,
    title="Points Validés",
    value="156/156", 
    description="100% de réussite",
    icon="✅",
    variant='success'
)

# Métrique d'erreur (rouge)  
error_card = MetricCard(
    parent,
    title="Erreur de Fermeture",
    value="3.2 mm",
    description="Seuil : 10 mm",
    icon="📐",
    variant='error'
)
```

---

## 🔔 **Notifications**

### 📢 Bannières d'Information
```python
# Succès
success_banner = NotificationBanner(
    parent,
    message="Calculs terminés avec succès !",
    notification_type='success',
    dismissible=True
)

# Avertissement
warning_banner = NotificationBanner(
    parent,
    message="Précision limite atteinte, vérifiez les données.",
    notification_type='warning'
)

# Erreur
error_banner = NotificationBanner(
    parent,
    message="Impossible d'importer le fichier.",
    notification_type='error'
)

# Information
info_banner = NotificationBanner(
    parent,
    message="Les corrections atmosphériques sont appliquées.",
    notification_type='info'
)
```

---

## 📏 **Espacements et Dimensions**

### 📐 Système d'Espacement
```python
# Micro-espacements
AppTheme.SPACING['xs']      # 4px
AppTheme.SPACING['sm']      # 8px
AppTheme.SPACING['md']      # 16px
AppTheme.SPACING['lg']      # 24px
AppTheme.SPACING['xl']      # 32px
AppTheme.SPACING['xxl']     # 48px

# Espacements spéciaux
AppTheme.SPACING['section']    # 20px (entre sections)
AppTheme.SPACING['component']  # 12px (entre composants)
```

### 📏 Tailles Standards
```python
# Hauteurs des composants
AppTheme.SIZES['button_height']       # 44px
AppTheme.SIZES['button_height_small'] # 32px  
AppTheme.SIZES['input_height']        # 40px

# Coins arrondis
AppTheme.SIZES['border_radius']       # 8px
AppTheme.SIZES['border_radius_large'] # 12px
AppTheme.SIZES['card_radius']         # 16px
```

---

## 🎨 **Bonnes Pratiques**

### ✅ À Faire
1. **Toujours utiliser les composants thématisés**
```python
# ✅ Bon
button = ThemedButton(parent, text="OK", variant='primary')

# ❌ Éviter  
button = ctk.CTkButton(parent, text="OK", fg_color='#2E86AB')
```

2. **Respecter la hiérarchie des couleurs**
```python
# ✅ Actions principales = primary (bleu géodésique)
save_btn = ThemedButton(parent, text="Sauvegarder", variant='primary')

# ✅ Actions secondaires = secondary ou outline
cancel_btn = ThemedButton(parent, text="Annuler", variant='outline')

# ✅ Précision/Validation = accent (orange)
precision_label = ThemedLabel(parent, text="2.0 mm", 
                            text_color=AppTheme.COLORS['accent'])
```

3. **Utiliser les espacements cohérents**
```python
# ✅ Padding des cartes
card.pack(padx=AppTheme.SPACING['lg'], pady=AppTheme.SPACING['md'])

# ✅ Entre sections  
section.pack(pady=(0, AppTheme.SPACING['section']))
```

### ❌ À Éviter
- Couleurs hardcodées dans le code
- Tailles de police fixes  
- Espacements arbitraires
- Mélange des styles CustomTkinter natifs et thématisés

---

## 🔄 **Exemples d'Usage**

### 📋 Création d'une Étape Complète
```python
def create_modern_step(self):
    # Container principal
    container = ctk.CTkFrame(self.main_frame, fg_color='transparent')
    container.pack(fill='both', expand=True, padx=AppTheme.SPACING['xl'])
    
    # En-tête dans une carte élevée
    header_card = ThemedFrame(container, elevated=True)
    header_card.pack(fill='x', pady=(0, AppTheme.SPACING['section']))
    
    # Titre avec icône
    title_frame = ctk.CTkFrame(header_card, fg_color='transparent')
    title_frame.pack(fill='x', padx=AppTheme.SPACING['xl'], pady=AppTheme.SPACING['lg'])
    
    icon = ThemedLabel(title_frame, text="📊", style='title', 
                      text_color=AppTheme.COLORS['primary'])
    icon.pack(side='left')
    
    title = ThemedLabel(title_frame, text="Résultats", style='title')
    title.pack(side='left', padx=(AppTheme.SPACING['md'], 0))
    
    # Contenu dans une carte moderne
    content_card = ModernCard(container, title="Métriques", icon="📈")
    
    # Métriques avec cartes spécialisées
    metrics_frame = ctk.CTkFrame(content_card.content_frame, fg_color='transparent')
    metrics_frame.pack(fill='x')
    
    precision = MetricCard(metrics_frame, title="Précision", value="1.8 mm",
                          variant='accent', icon="🎯")
    precision.pack(side='left', padx=(0, AppTheme.SPACING['md']), fill='x', expand=True)
    
    points = MetricCard(metrics_frame, title="Points", value="156",
                       variant='success', icon="📍") 
    points.pack(side='left', fill='x', expand=True)
```

---

## 🚀 **Prochaines Améliorations Possibles**

### 🎨 Fonctionnalités Avancées
- **Mode sombre/clair** avec transition
- **Animations et micro-interactions** 
- **Thèmes personnalisés** par utilisateur
- **Système de notifications** avancé
- **Tooltips contextuels** modernes

### 📊 Composants Futurs
- **DataTable** thématisée pour les résultats
- **ChartCard** pour graphiques intégrés
- **ProgressCard** avec étapes multiples
- **SearchBox** avec filtres
- **TabContainer** moderne

---

**🎉 Le système de thème géodésique est maintenant prêt pour créer des interfaces professionnelles et modernes !**