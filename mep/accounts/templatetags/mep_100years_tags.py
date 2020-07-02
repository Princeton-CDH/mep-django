from django.template.defaulttags import register

from mep.accounts.management.commands.twitterbot_100years import tweet_content


@register.simple_tag
def tweet_text(event, day):
    return tweet_content(event, day)
