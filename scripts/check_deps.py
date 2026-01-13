# DEPRECATED: Este script utilitário está marcado como suspeito de não ser mais utilizado. Favor revisar antes de remover.

import sys
try:
    from transformers import T5Tokenizer
    print("T5Tokenizer imported successfully")
except Exception as e:
    print(f"Failed to import T5Tokenizer: {e}")
    sys.exit(1)

try:
    from transformers import T5TokenizerFast
    print("T5TokenizerFast imported successfully")
except Exception as e:
    print(f"Failed to import T5TokenizerFast: {e}")

try:
    import sentencepiece
    print(f"SentencePiece version: {sentencepiece.__version__}")
except ImportError:
    print("SentencePiece not found")

