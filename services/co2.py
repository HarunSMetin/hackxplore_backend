def estimate_co2_emission(current_fill, capacity, last_updated, location_lat, location_lng, delayed_hours=0):
    """
    Estimate extra CO₂ emission due to delayed unloading.
    Simple formula: extra_kg = delayed_hours * (current_fill / capacity) * CO2_COEFFICIENT
    """
    CO2_COEFFICIENT = 0.5  # kg CO2 per hour per full container (example value)
    fill_ratio = current_fill / capacity if capacity else 0
    extra_kg = delayed_hours * fill_ratio * CO2_COEFFICIENT
    return extra_kg 