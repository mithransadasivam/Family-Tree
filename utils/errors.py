from rest_framework.response import Response


class ServiceError(Exception):
    """A write was refused. The view turns it into the HTTP answer: `payload` is the JSON body."""

    def __init__(self, payload, status_code=400):
        super().__init__(payload)
        self.payload = payload
        self.status_code = status_code


def error_response(exc):
    return Response(exc.payload, status=exc.status_code)
