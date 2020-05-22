from django.template.defaulttags import register

from mep.accounts.management.commands.twitterbot_100years import tweet_content


@register.filter
def tweet_text(event):
    return tweet_content(event)

