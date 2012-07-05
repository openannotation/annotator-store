def atoi(v, default=0):
    try:
        return int(v or default)
    except ValueError:
        return default
