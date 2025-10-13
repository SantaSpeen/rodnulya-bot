# File: src/modules/phraseEngine/utils.py
# Module: phraseEngine
# Written by: SantaSpeen
# Licence: MIT
# (c) SantaSpeen 2025

def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
