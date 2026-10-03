"""Context processors do ytdownloader."""


def tenant(request):
    current = getattr(request, 'tenant', None)
    return {'request_tenant': current}
