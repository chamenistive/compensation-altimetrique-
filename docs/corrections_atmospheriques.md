# 🌡️ CORRECTIONS ATMOSPHÉRIQUES - DOCUMENTATION

## 📋 Vue d'ensemble

Les corrections atmosphériques compensent les effets de la courbure terrestre et de la réfraction atmosphérique sur les mesures de nivellement géométrique.

## 🧮 Formules théoriques

### Correction de courbure terrestre
```
C₁ = k × d² / (2R)
```
- k = 1.0 (coefficient de courbure)
- d = distance de visée (m)
- R = 6,371,000 m (rayon terrestre)

### Correction de réfraction atmosphérique
```
C₂ = -r × d² / (2R)
```
- r = coefficient de réfraction (variable selon conditions)
- Valeur standard : r = 0.13
- Varie selon température, pression, humidité

### Correction totale
```
C_total = C₁ + C₂ = (k - r) × d² / (2R)
C_total = (1 - r) × d² / (2R)
```

## 📊 Coefficient de réfraction variable

Le coefficient r varie selon les conditions atmosphériques :

### Effet de la température
```
Δr_temp = -(T - 15°C) × 0.004
```

### Effet de la pression
```
Δr_press = (P - 1013.25 hPa) × 0.0001
```

### Effet de l'humidité
```
Δr_humid = (H - 60%) × 0.0002
```

### Coefficient final
```
r = 0.13 + Δr_temp + Δr_press + Δr_humid + Δr_time
```

## 🌍 Valeurs typiques par région

### France métropolitaine
- Température : 15°C
- Pression : 1013 hPa  
- Humidité : 65%
- **r ≈ 0.13**

### Sahel africain  
- Température : 32°C
- Pression : 1008 hPa
- Humidité : 40%
- **r ≈ 0.06**

## 📈 Impact selon la distance

| Distance | Correction (conditions standard) |
|----------|----------------------------------|
| 50m      | +0.10 mm                        |
| 100m     | +0.38 mm                        |
| 150m     | +0.86 mm                        |
| 200m     | +1.53 mm                        |
| 300m     | +3.44 mm                        |

## 🔧 Utilisation dans le code

### Activation automatique
```python
calculator = LevelingCalculator(
    precision_mm=2.0,
    apply_atmospheric_corrections=True  # Par défaut
)
```

### Conditions personnalisées
```python
from atmospheric_corrections import AtmosphericConditions

conditions = AtmosphericConditions(
    temperature_celsius=32.0,
    pressure_hpa=1008.0,
    humidity_percent=40.0
)

calculator = LevelingCalculator(
    atmospheric_conditions=conditions
)
```

### Désactivation
```python
calculator = LevelingCalculator(
    apply_atmospheric_corrections=False
)
```

## 📋 Recommandations

### Quand appliquer les corrections
- **Toujours** pour distances > 100m
- **Recommandé** pour précision < 5mm
- **Obligatoire** pour travaux de haute précision

### Conditions critiques
- **Forte chaleur** (> 30°C) : r diminue
- **Haute pression** : r augmente légèrement  
- **Matin/soir** : gradients thermiques importants

### Validation
- Vérifier amélioration de la fermeture
- Contrôler cohérence des corrections
- Analyser résidus après compensation

## 🎯 Précision attendue

Avec corrections atmosphériques :
- Amélioration fermeture : 10-30%
- Réduction erreurs systématiques
- Meilleure cohérence statistique

Sans corrections (distances > 150m) :
- Biais systématique
- Fermeture dégradée
- Tests statistiques moins fiables
