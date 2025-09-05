# project/utils.py

def safe_divide(a, b, default=0):
    """Divisão segura que evita ZeroDivisionError"""
    return a / b if b != 0 else default