import json
from django.template.defaulttags import register, mark_safe

@register.filter
def dict_item(dictionary, key):
    ''''Template filter to allow accessing dictionary value by variable key.
    Example use::

        {{ mydict|dict_item:keyvar }}
    '''
    return dictionary.get(key, None)


@register.filter(name='json')
def json_dumps(data):
    return mark_safe(json.dumps(data))
