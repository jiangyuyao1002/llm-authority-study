"""Retrospective extraction rule, fixed before its replay results were computed."""
import json

def first_object(text, strict_parse):
    """Keep whole-response success; otherwise select first decodable object, then validate once."""
    if not isinstance(text,str):
        return None
    whole=strict_parse(text)
    if whole is not None:
        return whole
    decoder=json.JSONDecoder()
    for i,char in enumerate(text):
        if char!='{':
            continue
        try:
            obj,end=decoder.raw_decode(text,i)
        except ValueError:
            continue
        if type(obj) is dict:
            # Do not skip a decoded but schema-invalid first object to find a preferred later object.
            return strict_parse(text[i:end])
    return None
