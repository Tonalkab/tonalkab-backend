# app/core/limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

# Instancia global del limitador de velocidad basada en la dirección IP del cliente
limiter = Limiter(key_func=get_remote_address)
