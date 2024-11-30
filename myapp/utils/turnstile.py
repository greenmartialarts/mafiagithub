import requests
from django.conf import settings
from django.core.exceptions import ValidationError

def verify_turnstile(token):
    """Verify Cloudflare Turnstile token"""
    try:
        response = requests.post('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
            'secret': settings.TURNSTILE_SECRET_KEY,
            'response': token,
        })
        
        result = response.json()
        
        if not result.get('success'):
            raise ValidationError('Turnstile verification failed')
            
        return True
        
    except requests.RequestException as e:
        raise ValidationError(f'Turnstile verification request failed: {str(e)}')
    except (KeyError, ValueError) as e:
        raise ValidationError(f'Invalid Turnstile response: {str(e)}') 