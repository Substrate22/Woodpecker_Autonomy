"""Centralized configuration for the lane detection script."""

import math

# ── Vision Pipeline ─────────────────────────────────────────────────
GAUSSIAN_KERNEL = (9, 9)
CANNY_LOW = 50
CANNY_HIGH = 200
HOUGH_RHO = 1
HOUGH_THETA = math.pi / 180
HOUGH_THRESHOLD = 25
HOUGH_MIN_LINE_LEN = 30
HOUGH_MAX_LINE_GAP = 40
ROI_TOP_RATIO = 0.45
SLOPE_MIN = 0.3
SMOOTHING_ALPHA = 0.4       #exponential moving average in find_center_offset

# ── PID Controller ──────────────────────────────────────────────────
KP = 1.2
KI = 0.008
KD = 0.5
PID_INTEGRAL_LIMIT = 50.0

# ── Adaptive Speed Controller ───────────────────────────────────────
SPEED_MIN = 35.0               # minimum speed (px/s)
SPEED_CURVATURE_GAIN = 0.35    # lower = slower in curves
SPEED_LOOK_AHEAD_DIST = 300.0  # how far ahead to check curvature
SPEED_SMOOTHING = 0.08         # how fast speed adjusts (per frame blend)

# ── Fonts ───────────────────────────────────────────────────────────
FONT_MONO = "consolas"
FONT_SANS = "helvetica"

# ── For use in find_center_offset ───────────────────────────────────
# Frame is 512x512: base of trapezoid spans (width * 0.2, width * 0.8)
ROAD_WIDTH = 307