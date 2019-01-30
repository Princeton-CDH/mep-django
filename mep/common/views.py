from django.views.generic.base import TemplateView

class Homepage(TemplateView):

    template_name = 'home.html'

class About(TemplateView):

    template_name = 'about.html'