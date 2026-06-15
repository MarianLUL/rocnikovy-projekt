from django import template

register = template.Library()


@register.filter(name='equip_category')
def equip_category(value):
    """Normalize or simplify the weapon category string.

    If the API returns strings like 'EEquippableCategory::Rifle', return
    the short label 'EQUIP_Category'. Otherwise return the original value.
    """
    if not value:
        return ''
    s = str(value)
    if 'EquippableCategory' in s or 'Equippable' in s:
        return 'EQUIP_Category'
    return s


@register.filter(name='prettyjson')
def prettyjson(value):
    """Pretty-print a Python dict/list or JSON string for display in templates."""
    import json
    try:
        if value is None:
            return ''
        # If it's a string, try to parse as JSON
        if isinstance(value, str):
            try:
                obj = json.loads(value)
            except Exception:
                return value
        else:
            obj = value
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        try:
            return str(value)
        except Exception:
            return ''
