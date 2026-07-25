import os

# Keep matplotlib headless for CLI tests.
os.environ.setdefault("MPLBACKEND", "Agg")
