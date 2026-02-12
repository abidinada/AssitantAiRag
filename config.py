"""Configuration du système RAG"""

# Chemins
PERSIST_DIR = "chroma_db"
COLLECTION_NAME = "ppt_slides"
FEEDBACK_DB = "feedback.db"

# Modèles
EMBED_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"

# Paramètres
RETRIEVAL_K = 6

# Domaine d'expertise (personnalisable)
EXPERTISE_DOMAIN = "cybersécurité, cloud computing et IA générative"

# Fichiers à ingérer
FILES = [
    "data/0-Graduation_AI.pptx",
    "data/1-Securite_Mines_2026.pptx",
    "data/2-Gen_AI_Mines_2026.pptx",
    "data/3-Cloud_Mines_2026_part_1.pptx",
    "data/4-Cloud_Mines_2026_part_2_exec.pptx",
    "data/5-Cloud_Mines_2025_part_3_operation.pptx",
    "data/6-Cloud_Mines_2025_part_4_trend.pptx",
]