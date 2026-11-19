"""One place that turns "the client sent something that is not an id" into a 400 instead of a 500."""
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None and isinstance(exc, (ValueError, TypeError)) and 'expected a number' in str(exc):
        # Django refuses a non-numeric value for an id column, e.g. {"tree": "abc"}.
        return Response({'error': 'An id must be a number'}, status=400)
    return response
