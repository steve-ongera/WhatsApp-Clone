from django import template

register = template.Library()

# Get value from dictionary by key
@register.filter
def get(dict_obj, key):
    try:
        return dict_obj.get(key)
    except:
        return None

# Get attribute of an object dynamically
@register.filter
def get_attr(obj, attr):
    return getattr(obj, attr, None)

# Convert queryset or list to count
@register.filter
def count(value):
    try:
        return value.count()
    except:
        return len(value)

# Format datetime nicely
@register.filter
def format_time(value, fmt="%Y-%m-%d %H:%M"):
    return value.strftime(fmt) if value else ""

# Limit text to n characters
@register.filter
def truncate_chars(value, num):
    return value[:num] + "..." if len(value) > num else value

# Check if string contains text
@register.filter
def contains(text, word):
    return word in text
