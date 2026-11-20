"""Shared settings: paths, seed, and the classes of text."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"              # downloaded sources (fetch/)
PREPARED = ROOT / "data" / "prepared"    # cleaned two-register texts and Rigdon's revelations (prepare/)
PROC = ROOT / "data" / "processed"       # documents, units and chunks (steps 1-4)
RESULTS = ROOT / "results"               # scores, series and reports (steps 5-10)

SEED = 20261113
CHUNK_WORDS = 1000
MIN_RANKED_UNITS = 20    # development units a class needs before held-out units can set its compatibility line
TAU = 0.10               # a chunk is compatible with author k if its rank against k's held-out writing is above this

SMITH = "Joseph Smith"
SMITH_REVELATIONS = "Joseph Smith (revelations)"
RIGDON = "Sidney Rigdon"
RIGDON_REVELATIONS = "Sidney Rigdon (revelations, 1856-76)"
RIGDON_LATE_LETTERS = "Sidney Rigdon (letters, 1863-76)"

# The classes the model learns
CANDIDATES = [SMITH, RIGDON, "Solomon Spalding", "Oliver Cowdery", "Parley P. Pratt"]
DISTRACTORS = ["Campbell-edited periodicals", "KJV", "Lucy Mack Smith", "Ethan Smith", "David Whitmer",
               "Hamilton", "Madison"]
CLASSES = CANDIDATES + DISTRACTORS

# Biblical-style texts by other authors: never learned, scored as controls
PSEUDO_BIBLICAL = ["Richard Snowden", "'Eliakim the Scribe' (pseud.)", "John Ballou Newbrough",
                   "Philemon Stewart (Shaker)"]
PSEUDO_BIBLICAL_AUDIT = ["Gilbert J. Hunt", "Levi H. Dowling"]     # held back in the audit layer: counted, never scored

# Authors with both scripture-style text and plain prose (the two-register study)
TWO_REGISTER = ["James J. Strang", "Richard Grant White", "Charles B. Thompson", "Jacob Ilive",
                "Christopher G. Memminger"]
