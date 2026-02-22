def is_serial_in_range(serial, start, end):
    """
    Check if a serial number falls within a range.
    Handles alphanumeric serials by comparing as strings.
    """
    try:
        # Normalize to uppercase for comparison
        serial = serial.upper().strip()
        start = start.upper().strip()
        end = end.upper().strip()
        
        # Simple string comparison (works for most alphanumeric manufacturers)
        return start <= serial <= end
    except:
        return False
