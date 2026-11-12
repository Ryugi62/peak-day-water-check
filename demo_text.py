"""English display text for the demo. The engine (domain.verdict) keeps its Korean status keys; this module only translates them for the screen."""
STATUS_EN = {"적합": "Fit", "조건부": "Conditional", "부적합": "Not fit", "보류": "Hold"}
NAME_EN = {"evaporative": "Evaporative (chiller + cooling tower)", "liquid": "Liquid + air hybrid",
           "hydrothermal": "Hydrothermal (dam or river pass-through)", "direct_air": "Direct evaporative air cooling"}
MEASURE_EN = {  # key -> (what to measure, how)
    "weather_station": ("Hourly weather station for the site (dry-bulb, humidity, pressure)", "Pick the nearest Korea Meteorological Administration station and pull 5 years of hourly data for the site."),
    "net_supply_m3": ("Net supply from the water source (m³/day)", "Plant discharge and existing reuse from measured daily data (SOOSIRO discharge monitoring), plus the dry-season minimum."),
    "peak_day_m3": ("Peak-day cooling make-up water (m³/day)", "Run the engine on 5 years of hourly weather for the site, with IT load and cooling spec."),
    "cycles": ("Cycles of concentration N", "Source-water conductivity and hardness test report, and the cooling-water management limit."),
    "dry_basis": ("Basis for switching to dry cooling", "Chiller maker's performance sheet or metered operating data."),
    "heat_mw": ("Heat to reject (MW)", "IT load times heat-rejection ratio, from the design document."),
    "delta_t_k": ("Allowed water temperature rise (K)", "The river or dam authority's discharge-temperature limit, in writing."),
    "permit_flow_m3d": ("Permitted intake flow (m³/day)", "Reply from the water-resource authority on the intake consultation."),
    "source_distance_km": ("Distance to the river or dam (km)", "Road distance from the site coordinates to the intake point."),
}
OUT_OF_SCOPE_EN = "The engine has no water-use physics for direct evaporative air cooling, so it does not judge it."
