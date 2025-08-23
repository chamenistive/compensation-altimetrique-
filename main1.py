import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Reading the xlsx file
df = pd.read_excel('RG.xlsx', header=[0])
print (df)

def identify_initial_and_final_points(df):
    df = df.dropna(subset=["Matricule"])
    if df.empty:
        raise ValueError("No valid 'Matricule' entries found.")
    return df.iloc[0]["Matricule"], df.iloc[-1]["Matricule"]

# Call the function and print results
initial, final = identify_initial_and_final_points(df)
print(f"\nInitial Point: {initial}")
print(f"Final Point: {final}")

def get_known_altitudes(initial_point, final_point, alt_initial=None, alt_final=None):
    """
    Get the known altitudes for the initial and final points.
    Prompts the user until valid numbers are entered.
    """
    while alt_initial is None:
        try:
            alt_initial = float(input(f"Enter the altitude for the initial point ({initial_point}): "))
        except ValueError:
            print("❌ Invalid input. Please enter a numeric value.")

    if initial_point != final_point:
        while alt_final is None:
            try:
                alt_final = float(input(f"Enter the altitude for the final point ({final_point}): "))
            except ValueError:
                print("❌ Invalid input. Please enter a numeric value.")
    else:
        alt_final = None  # closed loop, no need for final altitude

    return alt_initial, alt_final

df.columns = df.columns.str.strip()

# Identify AR/AV pairs (e.g., "AR 1" ↔ "AV 1", "AR 2" ↔ "AV 2")
ar_columns = [col for col in df.columns if col.upper().startswith("AR")]
av_columns = [col.replace("AR", "AV") for col in ar_columns]

# Validate pairs
if len(ar_columns) != len(av_columns):
    raise ValueError("Mismatched AR/AV pairs")

# Calculate delta_h for each instrument pair
delta_h_columns = []
for idx, (ar_col, av_col) in enumerate(zip(ar_columns, av_columns), start=1):
    delta_col = f"delta_h_{idx}"
    df[delta_col] = np.nan  # Initialize with NaN
    
    # Calculate delta_h = previous AR - current AV
    for i in range(1, len(df)):
        prev_ar = df.loc[i-1, ar_col]
        curr_av = df.loc[i, av_col]
        if pd.notna(prev_ar) and pd.notna(curr_av):
            df.loc[i, delta_col] = prev_ar - curr_av
    
    delta_h_columns.append(delta_col)

# Calculate mean of all delta_h columns
df["delta_h"] = df[delta_h_columns].mean(axis=1, skipna=False)

# Display relevant columns
output_cols = ["Matricule"] + ar_columns +  av_columns + delta_h_columns + ["delta_h"]
print(df[output_cols].astype(object))

# Add controle column where delta_h_1 and delta_h_2 exist
if 'delta_h_1' in df.columns and 'delta_h_2' in df.columns:
    df['controle'] = df['delta_h_1'] - df['delta_h_2']
else:
    print("Cannot calculate controle - missing delta_h columns")
# [...] Previous code remains unchanged until the output section

# Define output columns in the requested order
output_cols = (
    ["Matricule"] 
    + ar_columns 
    + av_columns 
    + delta_h_columns 
    + ["delta_h"] 
    + [col for col in df.columns if col.upper().startswith("DIST")]  # DIST_columns
    + ["controle"]  # controle_columns
)

# Display formatted output (preserving NaN values)
print(df[output_cols].astype(object))


# --- Assume df is already loaded and delta_h is computed ---

# Step 1: Ask the user to input the known altitude of the first point
while True:
    try:
        initial_altitude = float(input("Enter the known altitude of the first point (reference): "))
        break
    except ValueError:
        print("❌ Invalid input. Please enter a numeric value.")

# Step 2: Initialize the 'altitude' column with NaNs
df["altitude"] = pd.NA

# Step 3: Set the altitude of the first point (index 0)
df.loc[0, "altitude"] = initial_altitude

# Step 4: Loop through rows to compute altitudes
for i in range(1, len(df)):
    prev_alt = df.loc[i - 1, "altitude"]
    delta = df.loc[i, "delta_h"]
    
    if pd.notna(prev_alt) and pd.notna(delta):
        df.loc[i, "altitude"] = prev_alt + delta

# Optional: Format to 3 decimal places
df["altitude"] = df["altitude"].astype(float).round(3)

# Step 1: Build the list of output columns
output_cols = (
    ["Matricule"]
    + ar_columns                                  # Backsight columns
    + av_columns                                  # Foresight columns
    + delta_h_columns                             # delta_h_1, delta_h_2, ...
    + ["delta_h"]                                 # Averaged delta_h
    + [col for col in df.columns if col.upper().startswith("DIST")]  # Distance columns
    + ["controle", "altitude"]                    # Final control check and computed altitude
)

# Step 2: Display the output
print(df[output_cols])

# Step 1: Get matricule of first and last point
first_point = df.loc[0, "Matricule"]
last_point = df.loc[len(df) - 1, "Matricule"]

# Step 2: Get computed altitude of the last point
calculated_final_alt = df.loc[len(df) - 1, "altitude"]

# Step 3: Determine closure type and compute closure error
if first_point == last_point:
    # Closed loop: use known initial altitude
    known_final_alt = df.loc[0, "altitude"]
    closure_error = calculated_final_alt - known_final_alt
    print("\nClosed loop detected.")
else:
    # Open traverse: ask for known final altitude
    known_final_alt = float(input("Enter the known altitude of the last point ({}): ".format(last_point)))
    closure_error = calculated_final_alt - known_final_alt
    print("\nOpen traverse detected.")

# Step 4: Display closure error
print(f"Calculated final altitude: {calculated_final_alt:.3f}")
print(f"Known final altitude:       {known_final_alt:.3f}")
print(f"Closure error:              {closure_error:.4f}")


# Step 1: Choose a DIST column (we’ll use the first one available)
dist_columns = [col for col in df.columns if col.upper().startswith("DIST")]
chosen_dist_col = dist_columns[0]  # You can change this if needed

# Step 2: Compute total distance K (in kilometers)
total_distance_m = df[chosen_dist_col].astype(float).sum(skipna=True)
K = total_distance_m / 1000  # Convert to kilometers

# Step 3: Compute tolerance in millimeters
tolerance_mm = 4 * np.sqrt(K)

# Step 4: Convert closure error to millimeters
closure_error_mm = abs(closure_error * 1000)  # Closure error is in meters

# Step 5: Print results
print(f"\n--- Tolerance Check ---")
print(f"Chosen DIST column:         {chosen_dist_col}")
print(f"Total leveling distance (K): {K:.3f} km")
print(f"Tolerance:                  ±{tolerance_mm:.2f} mm")
print(f"Actual closure error:        {closure_error_mm:.2f} mm")


# Step 6: Compare error to tolerance
print(f"Closure error = {closure_error_mm:.3f} mm (Tolerance = {tolerance_mm:.3f} mm)")

if closure_error_mm <= tolerance_mm:
    print("ℹ️ Closure error is within acceptable tolerance.")
else:
    print("⚠️ Closure error exceeds the tolerance. Results may be less reliable.")

# Step 7: Always continue to adjustment
print("➡️ Proceeding to adjustment...")

# --- call adjustment pipeline directly ---
# (design matrix, misclosure, weights, normal equations, etc.)

# --- Atmospheric Refraction Correction (CRA_i) ---
k = 0.13
R = 6_370_000  # Earth's radius in meters

# 🔎 Check available columns before computing D_mean
print("Available columns in df:", df.columns.tolist())

# Compute mean distance D_i
# Step: Compute mean distance safely
if {"Dist1", "Dist2"}.issubset(df.columns):
    # Case 1: Both Dist1 and Dist2 exist
    df["D_mean"] = df[["Dist1", "Dist2"]].mean(axis=1)
    print("ℹ️ Using Dist1 and Dist2 to compute D_mean.")

elif "Distance" in df.columns:
    # Case 2: Only one distance column
    df["D_mean"] = df["Distance"]
    print("ℹ️ Using Distance column as D_mean.")

# Step: Compute D_mean safely from DIST1 and DIST2
if {"DIST1", "DIST2"}.issubset(df.columns):
    df["D_mean"] = df[["DIST1", "DIST2"]].mean(axis=1)
    print("ℹ️ Using DIST1 and DIST2 to compute D_mean.")

# --- Calculate corrections ---
# Correction for Earth's curvature
df['S'] = (df["D_mean"] ** 2) / (2 * R)

# Correction for atmospheric refraction
df["CRA"] = -K * df['S']
df["CRA"] = df["CRA"].round(6)

# Correction of apparent level (n.a)
df['NA'] = df['S'] + df["CRA"]

# Apply correction to delta_h
df["delta_h_corr"] = df["delta_h"] + df['NA']
print("delta_h_corr")
# Display corrected columns (don't delete delta_h if you still use it)
output_cols = (
    ["Matricule"]
    + ar_columns
    + av_columns
    + delta_h_columns
    + ["delta_h_corr"]  # Use corrected delta
    + [col for col in df.columns if col.upper().startswith("DIST")]
    + ["D_mean", "NA"]
    + ["controle", "altitude"]
)
print(df[output_cols])
print("Corrected delta_h (delta_h_corr):")
print(df[['Matricule', 'delta_h', 'CRA', 'NA', 'delta_h_corr']])

import numpy as np
import pandas as pd

# -----------------------
# Parameters
# -----------------------
sigma0_mm = 0.2      # instrument error in mm
k_km_mm   = 0.3      # km-dependent error in mm/sqrt(km)

sigma0_sq = sigma0_mm**2    # variance of instrument error [mm²]
k_km_sq   = k_km_mm**2      # variance of km error [mm²/km]

# -----------------------
# Fixed point
# -----------------------
df["Matricule"] = df["Matricule"].astype(str)
fixed_point = "AM1"

# Build unknowns
all_points = df["Matricule"].tolist()
unknown_points = [pt for pt in all_points if pt != fixed_point]
point_to_index = {pt: idx for idx, pt in enumerate(unknown_points)}

# -----------------------
# Build design matrix A
# -----------------------
m = len(df) - 1           # number of obs = n_points - 1
n = len(unknown_points)   # number of unknowns

A = np.zeros((m, n))
f = np.zeros((m, 1))

for i in range(1, len(df)):
    p = df.loc[i-1, "Matricule"]
    q = df.loc[i, "Matricule"]

    # Fill A row
    if p in point_to_index:
        A[i-1, point_to_index[p]] = -1
    if q in point_to_index:
        A[i-1, point_to_index[q]] = +1

# -----------------------
# Misclosure vector f
# -----------------------
for i in range(1, len(df)):
    dh_corr = df.loc[i, "delta_h_corr"]
    alt_curr = df.loc[i, "altitude"]
    alt_prev = df.loc[i - 1, "altitude"]

    if pd.notna(dh_corr) and pd.notna(alt_curr) and pd.notna(alt_prev):
        f[i-1, 0] = dh_corr - (alt_curr - alt_prev)
    else:
        f[i-1, 0] = 0.0

df["misclosure_f"] = np.vstack(([0], f))  # attach with leading 0 for first point

# -----------------------
# Weight matrix W
# -----------------------
df['D_km'] = df['D_mean'] / 1000.0
df['sigma_squared_mm2'] = sigma0_sq + k_km_sq * df['D_km']
df['sigma_squared_m2']  = (df['sigma_squared_mm2'] / 1e6)   # convert mm² → m²
df['W_i'] = 1.0 / df['sigma_squared_m2']

weights = df['W_i'].iloc[1:].to_numpy()  # skip first row (no obs there)
W = np.diag(weights)

# -----------------------
# Print checks
# -----------------------
print("\n📌 Design matrix A:")
print(A)

print("\n📌 Misclosure vector f:")
print(f)

print("\n📌 Weight vector w:")
print(weights.reshape(-1,1))

print("\n📌 Weight matrix W:")
print(W)

# -----------------------
# Adjustment
# -----------------------
AT = A.T
N   = AT @ W @ A
rhs = AT @ W @ f

# Check condition number
eigvals = np.linalg.eigvals(N)
eigvals = np.real(eigvals[eigvals > 1e-12])
if eigvals.size == 0:
    raise ValueError("❌ Normal matrix N is singular (check fixed points).")
cond = np.max(np.abs(eigvals)) / np.min(np.abs(eigvals))
print(f"\nCondition number ≈ {cond:.2e}")

# Solve with fallback
try:
    if cond > 1e10:
        print("⚠️ Ill-conditioned system, using pseudo-inverse.")
        x_solution = np.linalg.pinv(N) @ rhs
    else:
        x_solution = np.linalg.solve(N, rhs)
    x = x_solution.reshape(-1, 1)
except np.linalg.LinAlgError as e:
    print(f"❌ Adjustment failed: {str(e)}")
    x = np.zeros((n, 1))

print("\n✅ Adjustment vector x (corrections):")
print(x)


import numpy as np
import pandas as pd

# --- Apply x to compute adjusted altitudes ---
df["altitude_adjusted"] = df["altitude"]  # initialize

for pt, idx in point_to_index.items():
    mask = df["Matricule"] == pt
    df.loc[mask, "altitude_adjusted"] = df.loc[mask, "altitude"] + x[idx][0]

# Round adjusted altitudes
df["altitude_adjusted"] = df["altitude_adjusted"].round(3)

print("\n✅ Adjusted altitudes:")
print(df[["Matricule", "altitude", "altitude_adjusted"]])

# -----------------------
# Residual computation
# -----------------------
# 1️⃣ Residual vector from least squares: v = A·x - f
v = (A @ x) - f  # shape (m,1)

# 2️⃣ Explicit residuals from Δh_corr and adjusted altitudes
residuals_explicit = []
for i, row in df.iterrows():
    if i == 0:
        residuals_explicit.append(np.nan)  # skip first point
        continue

    dh_corr = row["delta_h_corr"]
    pt_from = df.loc[i - 1, "Matricule"]
    pt_to   = row["Matricule"]

    H_from = df.loc[i - 1, "altitude_adjusted"]
    H_to   = row["altitude_adjusted"]

    if pd.notna(dh_corr) and pd.notna(H_from) and pd.notna(H_to):
        v_i = dh_corr - (H_to - H_from)
    else:
        v_i = np.nan
    residuals_explicit.append(v_i)

df["residual_explicit"] = residuals_explicit

# -----------------------
# Degrees of freedom
# -----------------------
m, n = A.shape
dof = m - n
print(f"\nObservations m={m}, unknowns n={n}, dof={dof}")

if dof <= 0:
    print(f"⚠️ Not enough redundancy (dof={dof}). Cannot compute σ₀ and uncertainties.")
    sigma_0 = np.nan
    std_uncertainty = np.full((n, 1), np.nan)
else:
    # Posteriori variance factor
    sigma_0_squared = (v.T @ W @ v) / dof
    sigma_0 = np.sqrt(sigma_0_squared.item())

    # Covariance matrix of unknowns
    Q_xx = np.linalg.inv(N)
    cov_x = sigma_0_squared * Q_xx

    # Standard uncertainties
    std_uncertainty = np.sqrt(np.diag(cov_x)).reshape(-1, 1)

# -----------------------
# Results
# -----------------------
print("\n✅ Residual vector v (from least squares):")
print(v)

print("\n✅ Residuals (explicit, by Δh_corr vs adjusted altitudes):")
print(df[["Matricule", "delta_h_corr", "altitude_adjusted", "residual_explicit"]])

print(f"\n✅ Posteriori standard deviation (σ₀): {sigma_0:.6f}"
      if not np.isnan(sigma_0) else "σ₀ not computed.")

if not np.isnan(sigma_0):
    print("\n✅ Standard uncertainties:")
    for pt, idx in point_to_index.items():
        print(f"Point {pt}: ±{std_uncertainty[idx][0]:.6f} m")

# -----------------------
# Save to Excel
# -----------------------
df.to_excel("adjusted_results_with_residuals.xlsx", index=False)
print("\n📁 Results saved to 'adjusted_results_with_residuals.xlsx'")



