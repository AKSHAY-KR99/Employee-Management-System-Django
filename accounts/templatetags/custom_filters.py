from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if dictionary and key in dictionary:
        return dictionary.get(key)
    return ""

@register.filter
def get_field_value(field_values, field_id):
    value = field_values.filter(field_id=field_id).first()
    return value.value if value else ""

@register.filter
def is_equal(val1, val2):
    return str(val1) == str(val2)