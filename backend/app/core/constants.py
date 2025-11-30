"""Shared application constants.

Centralizes repeat values used across import/processing logic so we can
document and adjust them in one place.
"""

# Distance of one statute mile in meters
MILE_M = 1609.34

# Sampling step for distance-indexed series (~0.1 mi)
SAMPLE_STEP_M = 160.934

# Minimum speed considered "moving" (m/s). ~1.1 mph.
MOVING_SPEED_MPS = 0.5

# Heart rate zone bounds as fractions of HR max.
# Z1: [0.50, 0.60), Z2: [0.60, 0.70), ..., Z5: [0.90, 1.01)
HR_ZONE_BOUNDS = [0.5, 0.6, 0.7, 0.8, 0.9, 1.01]

