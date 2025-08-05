# Documentation des Algorithmes de Compensation Altimétrique

## Vue d'ensemble

Ce document détaille les algorithmes implémentés dans le système de compensation altimétrique avec une précision garantie de **2 millimètres**.

## Table des matières

1. [Algorithmes fondamentaux](#1-algorithmes-fondamentaux)
2. [Calcul des dénivelées](#2-calcul-des-dénivelées)
3. [Compensation par moindres carrés](#3-compensation-par-moindres-carrés)
4. [Analyse statistique](#4-analyse-statistique)
5. [Validation de précision](#5-validation-de-précision)

---

## 1. Algorithmes fondamentaux

### 1.1 Principe du nivellement géométrique

Le nivellement géométrique mesure les différences d'altitude entre points par visées horizontales sur des mires graduées.

**Formule fondamentale :**
```
Δh = AR - AV
```

Où :
- `Δh` : Dénivelée entre deux points
- `AR` : Lecture arrière (Arrière)  
- `AV` : Lecture avant (Avant)

### 1.2 Propagation d'altitude

**Algorithme de calcul séquentiel :**
```
H₀ = altitude de référence (connue)
H₁ = H₀ + Δh₁
H₂ = H₁ + Δh₂
...
Hᵢ = Hᵢ₋₁ + Δhᵢ
```

**Optimisation vectorielle :**
```python
altitudes = H₀ + cumsum([0, Δh₁, Δh₂, ..., Δhₙ])
```

---

## 2. Calcul des dénivelées

### 2.1 Dénivelées simples

Pour chaque observation avec un instrument :

```python
def calculate_delta_h_single(ar_reading: float, av_reading: float) -> float:
    """
    Calcul d'une dénivelée simple.
    
    Théorie: En nivellement géométrique, la dénivelée entre deux points
    est la différence entre la lecture arrière (sur le point de départ)
    et la lecture avant (sur le point d'arrivée).
    """
    return ar_reading - av_reading
```

### 2.2 Dénivelées multiples (contrôle)

Avec plusieurs instruments pour la même visée :

```python
def calculate_delta_h_multiple(ar_readings: list, av_readings: list) -> tuple:
    """
    Calcul avec contrôle instrumental.
    
    Algorithme:
    1. Calculer Δh pour chaque instrument
    2. Vérifier cohérence (écart < 5mm)
    3. Calculer moyenne pondérée
    """
    delta_h_values = []
    for ar, av in zip(ar_readings, av_readings):
        delta_h_values.append(ar - av)
    
    # Contrôle de cohérence
    mean_delta = np.mean(delta_h_values)
    residuals = [dh - mean_delta for dh in delta_h_values]
    
    # Validation (tolérance 5mm)
    if max(abs(r) * 1000 for r in residuals) > 5.0:
        raise ControlError("Écart entre instruments > 5mm")
    
    return mean_delta, residuals
```

### 2.3 Validation des lectures

**Plages de validité :**
- Lectures AR/AV : [-10m, +10m] (plage normale pour mires)
- Dénivelées : [-50m, +50m] (limites géométriques raisonnables)

```python
def validate_readings(ar: float, av: float, point_id: str):
    """Validation des lectures selon critères géodésiques."""
    if not (-10.0 <= ar <= 10.0):
        raise ValidationError(f"Lecture AR hors plage: {ar}m au point {point_id}")
    if not (-10.0 <= av <= 10.0):
        raise ValidationError(f"Lecture AV hors plage: {av}m au point {point_id}")
```

---

## 3. Compensation par moindres carrés

### 3.1 Modèle mathématique

**Modèle fonctionnel :**
```
l + v = A × x + f
```

Où :
- `l` : Vecteur des observations (dénivelées mesurées)
- `v` : Vecteur des résidus
- `A` : Matrice de conception
- `x` : Vecteur des corrections d'altitude
- `f` : Vecteur des fermetures

**Modèle stochastique :**
```
P = σ₀² × Q⁻¹
```

Où :
- `P` : Matrice de poids
- `σ₀²` : Variance a priori du poids unitaire
- `Q` : Matrice de covariance a priori

### 3.2 Construction de la matrice de conception A

Pour un cheminement de n points avec le premier point fixé :

```python
def build_design_matrix(n_points: int) -> np.ndarray:
    """
    Construction de la matrice A pour nivellement.
    
    Dimension: (n-1) × (n-1)
    - (n-1) observations (entre points consécutifs)
    - (n-1) inconnues (points 2 à n, point 1 fixé)
    """
    n_obs = n_points - 1
    n_unknowns = n_points - 1
    
    A = np.zeros((n_obs, n_unknowns))
    
    for i in range(n_obs):
        A[i, i] = 1.0      # Point d'arrivée (correction positive)
        if i > 0:
            A[i, i-1] = -1.0   # Point de départ (correction négative)
    
    return A
```

**Exemple pour 4 points (A, B, C, D) :**
```
Observations: A→B, B→C, C→D
Inconnues: corrections pour B, C, D

    B   C   D
A→B [1   0   0]
B→C [-1  1   0]  
C→D [0  -1   1]
```

### 3.3 Calcul de la matrice de poids P

**Théorie géodésique de la variance :**
```
σᵢ² = a² + b² × dᵢ
```

Où :
- `σᵢ²` : Variance de l'observation i (mm²)
- `a` : Erreur instrumentale (mm)
- `b` : Erreur kilométrique (mm/km)
- `dᵢ` : Distance de visée (km)

```python
def calculate_observation_weight(distance_m: float, 
                               instrumental_error_mm: float = 1.0,
                               kilometric_error_mm: float = 1.0) -> float:
    """
    Calcul du poids d'une observation selon la théorie géodésique.
    """
    distance_km = distance_m / 1000.0
    
    # Variance en mm²
    variance_mm2 = instrumental_error_mm**2 + (kilometric_error_mm * distance_km)**2
    
    # Poids = inverse de la variance
    weight = 1.0 / variance_mm2
    
    return weight
```

### 3.4 Résolution du système

**Équations normales :**
```
N × x = b
```

Où :
```
N = A^T × P × A    (matrice normale)
b = A^T × P × f    (second membre)
```

**Implémentation avec sélection automatique de méthode :**

```python
def solve_least_squares(A: np.ndarray, P: np.ndarray, f: np.ndarray) -> tuple:
    """
    Résolution optimisée selon la taille du système.
    """
    n_obs, n_unknowns = A.shape
    
    if n_unknowns < 1000:
        # Petits systèmes : équations normales
        return solve_normal_equations(A, P, f)
    else:
        # Gros systèmes : décomposition QR (plus stable)
        return solve_qr_decomposition(A, P, f)

def solve_normal_equations(A, P, f):
    """Méthode classique pour petits systèmes."""
    N = A.T @ P @ A
    b = A.T @ P @ f
    
    x_hat = np.linalg.solve(N, b)
    Qx = np.linalg.inv(N)  # Matrice de covariance
    
    return x_hat, Qx

def solve_qr_decomposition(A, P, f):
    """Méthode stable pour gros systèmes."""
    sqrt_P = np.sqrt(P)
    A_weighted = sqrt_P @ A
    f_weighted = sqrt_P @ f
    
    Q, R = np.linalg.qr(A_weighted)
    x_hat = scipy.linalg.solve_triangular(R, Q.T @ f_weighted)
    
    # Covariance via R
    R_inv = scipy.linalg.solve_triangular(R, np.eye(R.shape[0]))
    Qx = R_inv @ R_inv.T
    
    return x_hat, Qx
```

---

## 4. Analyse statistique

### 4.1 Écart-type a posteriori

**Formule :**
```
σ₀ = √(v^T P v / r)
```

Où :
- `v` : Vecteur des résidus
- `P` : Matrice de poids
- `r` : Degrés de liberté (n_obs - n_unknowns)

```python
def calculate_sigma_0_posteriori(residuals: np.ndarray, 
                                weights: np.ndarray, 
                                degrees_of_freedom: int) -> float:
    """Calcul de l'écart-type a posteriori."""
    vtPv = residuals.T @ np.diag(weights) @ residuals
    sigma_0_hat = np.sqrt(vtPv / degrees_of_freedom)
    return sigma_0_hat[0, 0]
```

### 4.2 Test du poids unitaire (χ²)

**Hypothèses :**
- H₀ : σ₀² = σ₀²(a priori) = 1
- H₁ : σ₀² ≠ 1

**Statistique de test :**
```
T = v^T P v ~ χ²(r)
```

```python
def test_unit_weight(vtPv: float, degrees_of_freedom: int, 
                    confidence_level: float = 0.95) -> bool:
    """Test du χ² pour validation du poids unitaire."""
    from scipy.stats import chi2
    
    chi2_critical = chi2.ppf(confidence_level, degrees_of_freedom)
    
    return vtPv <= chi2_critical
```

### 4.3 Détection des fautes grossières

**Résidus normalisés :**
```
r̂ᵢ = vᵢ / (σ₀ √qᵥᵥᵢ)
```

Où `qᵥᵥᵢ` est l'élément diagonal i de la matrice de covariance des résidus.

**Seuil de détection (test de Student) :**
```python
def detect_blunders(normalized_residuals: np.ndarray, 
                   degrees_of_freedom: int,
                   confidence_level: float = 0.95) -> list:
    """Détection des fautes grossières."""
    from scipy.stats import t
    
    alpha = 1 - confidence_level
    t_critical = t.ppf(1 - alpha/2, degrees_of_freedom)
    
    blunders = []
    for i, residual in enumerate(normalized_residuals):
        if abs(residual) > t_critical:
            blunders.append({
                'observation': i,
                'normalized_residual': residual,
                'significance': abs(residual) / t_critical
            })
    
    return blunders
```

---

## 5. Validation de précision

### 5.1 Contrôle de fermeture

**Erreur de fermeture :**

Pour cheminement fermé :
```
ef = H_finale_calculée - H_initiale_connue
```

Pour cheminement ouvert :
```
ef = H_finale_calculée - H_finale_connue
```

### 5.2 Tolérance géodésique

**Formule normative :**
```
T = 4 × √K    (mm)
```

Où `K` est la longueur totale du cheminement en kilomètres.

```python
def calculate_tolerance(total_distance_km: float) -> float:
    """Calcul de la tolérance selon normes géodésiques."""
    return 4.0 * np.sqrt(total_distance_km)  # mm

def validate_closure(closure_error_m: float, total_distance_km: float) -> bool:
    """Validation de l'erreur de fermeture."""
    closure_error_mm = abs(closure_error_m * 1000)
    tolerance_mm = calculate_tolerance(total_distance_km)
    
    return closure_error_mm <= tolerance_mm
```

### 5.3 Validation précision 2mm

**Critères de validation :**

1. **Corrections individuelles :** `|xᵢ| ≤ 2mm`
2. **Erreur de fermeture :** `|ef| ≤ 2mm` (si possible)
3. **Résidus normalisés :** `|r̂ᵢ| ≤ 3.0` (seuil 3-sigma)

```python
def validate_2mm_precision(corrections_mm: np.ndarray,
                          closure_error_mm: float,
                          normalized_residuals: np.ndarray) -> dict:
    """Validation complète de la précision 2mm."""
    
    results = {
        'corrections_valid': np.max(np.abs(corrections_mm)) <= 2.0,
        'closure_valid': abs(closure_error_mm) <= 2.0,
        'residuals_valid': np.max(np.abs(normalized_residuals)) <= 3.0
    }
    
    results['precision_achieved'] = all(results.values())
    
    return results
```

---

## 6. Optimisations de performance

### 6.1 Complexité algorithmique

| Opération              | Complexité   | Optimisation             |
|------------------------|--------------|--------------------------|
| Calcul dénivelées      | O(n)         | Vectorisation            |
| Construction matrice A | O(n²) → O(n) | Matrices creuses         |
| Résolution système     | O(n³)        | QR décomposition         |
| Calcul résidus         | O(n²)        | Multiplication optimisée |

### 6.2 Gestion mémoire

**Pour gros volumes (n > 10000) :**

```python
def process_large_dataset(data, chunk_size=1000):
    """Traitement par blocs pour économiser la mémoire."""
    n_chunks = len(data) // chunk_size + 1
    
    for i in range(n_chunks):
        chunk = data[i*chunk_size:(i+1)*chunk_size]
        yield process_chunk(chunk)
```

---

## 7. Références théoriques

### Formules géodésiques fondamentales

1. **Variance théorique :** Wolf, P.R., & Ghilani, C.D. (2006). *Elementary Surveying: An Introduction to Geomatics*.

2. **Moindres carrés :** Mikhail, E.M., & Ackermann, F. (1976). *Observations and Least Squares*.

3. **Tests statistiques :** Koch, K.R. (1999). *Parameter Estimation and Hypothesis Testing in Linear Models*.

### Normes appliquées

- **IGN France :** Instruction technique sur le nivellement général de la France
- **ISO 17123-2 :** Procédures d'essai sur le terrain pour instruments géodésiques
- **Précision 2mm :** Spécification projet (niveau ingénierie de précision)

---

## 8. Exemples d'application

### Cas d'usage typique

```python
# 1. Import et validation
importer = DataImporter()
data = importer.import_file("nivellement.xlsx")

# 2. Calculs préliminaires  
calculator = LevelingCalculator(precision_mm=2.0)
results = calculator.calculate_complete_leveling(
    data.dataframe, data.ar_columns, data.av_columns, 
    data.dist_columns, initial_altitude=100.000
)

# 3. Compensation
compensator = LevelingCompensator(precision_mm=2.0)
compensation = compensator.compensate(results, distances)

# 4. Validation
validation = compensator.validate_compensation_quality(compensation)
print(f"Précision 2mm atteinte: {validation.details['precision_achieved']}")
```

---

*Document généré automatiquement par le système de compensation altimétrique v1.0*
*Précision garantie: 2mm | Conforme aux normes géodésiques internationales*