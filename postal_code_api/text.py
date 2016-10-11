from normalizr import Normalizr
import re

def normalize_text(text):
    normalizr = Normalizr(language='es')
    normalizations = [
        'remove_accent_marks',
        'replace_hyphens',
        ('replace_punctuation', {'replacement': ' '}),
        'remove_extra_whitespaces',
        'replace_symbols'
    ]
    return normalizr.normalize(text.lower().strip(), normalizations)