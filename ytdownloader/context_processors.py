def tenant(request):
    tenant = getattr(request, 'tenant', None)
    return {'request_tenant': tenant}
