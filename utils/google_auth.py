import requests
from django.conf import settings


def verify_google_token(id_token):
    response = requests.get(
        'https://oauth2.googleapis.com/tokeninfo',
        params={'id_token': id_token}
    )

    if response.status_code != 200:
        raise ValueError('Invalid Google token')

    data = response.json()

    if 'error' in data:
        raise ValueError(f'Google token error: {data["error"]}')

    if data.get('aud') != settings.GOOGLE_CLIENT_ID:
        raise ValueError('Token audience does not match client ID')

    return {
        'google_id': data.get('sub'),
        'email': data.get('email'),
        'first_name': data.get('given_name', ''),
        'last_name': data.get('family_name', ''),
        'photo_url': data.get('picture', ''),
    }
