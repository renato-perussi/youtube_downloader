from django.apps import AppConfig


class YtdownloaderConfig(AppConfig):
    name = 'ytdownloader'

    def ready(self):
        import ytdownloader.signals  # noqa
