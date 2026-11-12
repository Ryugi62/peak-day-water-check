/* Port of domain/verdict.py (Peak-Day Water Check). tests/test_parity.py runs both on the same cases. */
(function (root) {
  "use strict";
  var CP_KJ = 4.186;
  var OPTIONS = ["evaporative", "liquid", "hydrothermal", "direct_air"];
  var REQUIRED = {
    evaporative: ["weather_station", "net_supply_m3", "peak_day_m3", "cycles"],
    liquid: ["weather_station", "net_supply_m3", "peak_day_m3", "cycles", "dry_basis"],
    hydrothermal: ["heat_mw", "delta_t_k", "permit_flow_m3d", "source_distance_km"],
    direct_air: []
  };
  var MEASURE = {
    weather_station: ["Hourly weather station for the site (dry-bulb, humidity, pressure)", "Pick the nearest KMA ASOS station and pull 5 years of hourly data for the site."],
    net_supply_m3: ["Net supply from the water source (m3/day)", "Plant discharge and existing reuse from measured daily data (SOOSIRO TMS), plus the dry-season minimum."],
    peak_day_m3: ["Peak-day cooling make-up water (m3/day)", "Run the engine on 5 years of hourly weather for the site, with IT load and cooling spec."],
    cycles: ["Cycles of concentration N", "Source-water conductivity and hardness test report, and the cooling-water management limit."],
    dry_basis: ["Basis for switching to dry cooling", "Chiller maker's performance sheet or metered operating data."],
    heat_mw: ["Heat to reject (MW)", "IT load times heat-rejection ratio, from the design document."],
    delta_t_k: ["Allowed water temperature rise (K)", "The river or dam authority's discharge-temperature limit, in writing."],
    permit_flow_m3d: ["Permitted intake flow (m3/day)", "Reply from the water-resource authority on the intake consultation."],
    source_distance_km: ["Distance to the river or dam (km)", "Road distance from the site coordinates to the intake point."]
  };
  var RANGE_ERROR = "range";

  function grade(x) { return x >= 2.0 ? "Fit" : (x >= 1.0 ? "Conditional" : "Not fit"); }
  function have(facts, k) { return facts[k] !== undefined && facts[k] !== null && facts[k] !== ""; }
  function passthrough(heatMw, dT) {
    if (dT <= 0) throw new Error(RANGE_ERROR);
    return (heatMw * 1000.0 / (CP_KJ * dT)) * 86400 / 1000.0;
  }

  /* returns {option,status,ratio,missing:[{key,name,how}],outOfScope,numerator,denominator}; throws Error("range") */
  function judgeOption(option, facts) {
    if (OPTIONS.indexOf(option) < 0) throw new Error("unknown option");
    if (option === "direct_air") return { option: option, status: "Hold", ratio: null, missing: [], outOfScope: true };
    var miss = REQUIRED[option].filter(function (k) { return !have(facts, k); })
      .map(function (k) { return { key: k, name: MEASURE[k][0], how: MEASURE[k][1] }; });
    if (miss.length) return { option: option, status: "Hold", ratio: null, missing: miss, outOfScope: false };
    var num, den;
    if (option === "hydrothermal") {
      if (facts.heat_mw <= 0 || facts.permit_flow_m3d <= 0 || facts.source_distance_km < 0) throw new Error(RANGE_ERROR);
      num = facts.permit_flow_m3d; den = passthrough(facts.heat_mw, facts.delta_t_k);
    } else {
      if (facts.peak_day_m3 <= 0 || facts.net_supply_m3 < 0 || facts.cycles <= 1) throw new Error(RANGE_ERROR);
      num = facts.net_supply_m3; den = facts.peak_day_m3;
    }
    var ratio = num / den;
    return { option: option, status: grade(ratio), ratio: ratio, missing: [], outOfScope: false, numerator: num, denominator: den };
  }

  var api = { OPTIONS: OPTIONS, REQUIRED: REQUIRED, MEASURE: MEASURE, judgeOption: judgeOption, grade: grade };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.PeakDay = api;
})(typeof window !== "undefined" ? window : globalThis);
