from django import template
from urllib.parse import urlencode
import re

register = template.Library()


@register.simple_tag
def urlparams(*_, **kwargs):
    safe_args = {k: v for k, v in kwargs.items() if v is not None}
    if safe_args:
        return '?{}'.format(urlencode(safe_args))
    return ''


### Add a tag to split camel case strings into words
@register.filter
def split_camel_case(value):
    return ' '.join([word for word in re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', value)])

### Add a tag to convert string into title
@register.filter
def title_case(value):
    return value.title()