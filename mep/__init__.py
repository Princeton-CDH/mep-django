__version__ = "1.8.0"


# context processor to add version to the template environment
def context_extras(request):
    return {
        # software version
        "SW_VERSION": __version__
    }
