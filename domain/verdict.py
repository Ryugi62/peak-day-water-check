"""판정 보류 규칙(v9) — 순수 계산. 근거가 모자라면 숫자 대신 「보류 + 필요한 실측 목록」을 낸다.
등급 기준은 domain.supply.grade와 같다(2배 이상 적합 · 1~2배 조건부 · 1배 미만 부적합)."""
from domain.hydrothermal import passthrough_flow_m3_per_day
from domain.supply import grade

HOLD = "보류"
OPTIONS = ("evaporative", "liquid", "hydrothermal", "direct_air")

# 근거 키 → (이름, 측정 방법). 모르면 값이 None이거나 키가 없다.
MEASUREMENTS = {
    "weather_station": ("후보지 시간별 기상 지점(건구·습도·기압)", "가장 가까운 기상청 ASOS 지점 지정, 부지 5년 시간자료"),
    "net_supply_m3": ("공급원 순공급량(m³/일)", "처리장·정수장 방류량·기존 재이용 실측(수질TMS 일 자료)과 갈수기 최솟값"),
    "peak_day_m3": ("최대일 냉각 보충수(m³/일)", "후보지 5개년 시간별 기상으로 엔진 계산(IT 규모·냉각 사양 입력)"),
    "cycles": ("농축배수비 N(원수 전도도)", "원수 전도도·경도 시험성적서와 냉각수 관리기준"),
    "dry_basis": ("건식 전환 근거(제조사 건식 전환 온도·건식 비중)", "냉각기 제조사 성능표 또는 운영 계량값"),
    "heat_mw": ("방열량(MW)", "IT 부하 × 열배출 비율, 설계서"),
    "delta_t_k": ("허용 온도 상승(방류 온도 규제, K)", "하천·댐 관리기관의 방류 온도 허용 기준 문서"),
    "permit_flow_m3d": ("취수 허가 가능 유량(m³/일)", "수자원 관리기관 취수 협의 회신"),
    "source_distance_km": ("하천·댐 접근 거리(km)", "부지 좌표와 수원 취수 지점의 도로 거리 실측"),
}
REQUIRED = {
    "evaporative": ("weather_station", "net_supply_m3", "peak_day_m3", "cycles"),
    "liquid": ("weather_station", "net_supply_m3", "peak_day_m3", "cycles", "dry_basis"),
    "hydrothermal": ("heat_mw", "delta_t_k", "permit_flow_m3d", "source_distance_km"),
    "direct_air": (),
}


def _have(facts, key):
    return facts.get(key) is not None


def _missing(option, facts):
    return [{"key": k, "name": MEASUREMENTS[k][0], "how": MEASUREMENTS[k][1]} for k in REQUIRED[option] if not _have(facts, k)]


BOUNDARIES = (1.0, 2.0)     # grade()의 경계 배수


def band_status(ratio, band):
    """v11: 수요 오차 ±band이면 배수는 [ratio/(1+band), ratio/(1−band)] 안 어딘가다. 그 구간이 경계(1배·2배)를 품으면 보류, 아니면 등급."""
    if not 0 <= band < 1:
        raise ValueError("오차대는 0 이상 1 미만")
    lo, hi = ratio / (1 + band), ratio / (1 - band)
    if band > 0 and any(lo <= b <= hi for b in BOUNDARIES):
        return HOLD
    return grade(ratio)


def judge_option(option, facts, error_band=None):
    if option not in OPTIONS:
        raise ValueError(f"알 수 없는 냉각 방식: {option}")
    if option == "direct_air":
        return {"option": option, "status": HOLD, "ratio": None, "missing": [], "out_of_scope": True,
                "reason": "직접 증발식 외기 냉각은 엔진에 물 소비 물리식이 없다 — 판정하지 않는다"}
    miss = _missing(option, facts)
    if miss:
        return {"option": option, "status": HOLD, "ratio": None, "missing": miss, "out_of_scope": False,
                "reason": "근거 부족 — 필요한 실측 " + ", ".join(m["name"] for m in miss)}
    if option == "hydrothermal":
        if facts["heat_mw"] <= 0 or facts["permit_flow_m3d"] <= 0 or facts["source_distance_km"] < 0:
            raise ValueError("열량·허가 유량은 양수, 거리는 0 이상")
        ratio = facts["permit_flow_m3d"] / passthrough_flow_m3_per_day(facts["heat_mw"], facts["delta_t_k"])
    else:
        if facts["peak_day_m3"] <= 0 or facts["net_supply_m3"] < 0 or facts["cycles"] <= 1:
            raise ValueError("최대일은 양수, 공급은 0 이상, 농축배수비는 1 초과")
        ratio = facts["net_supply_m3"] / facts["peak_day_m3"]
    status = grade(ratio) if not error_band else band_status(ratio, error_band)
    reason = ""
    if status == HOLD:
        reason = f"오차대 ±{error_band:.0%}가 경계(1배·2배)에 걸림 — 배수 {ratio:.2f}배 판정 보류"
    return {"option": option, "status": status, "ratio": ratio, "missing": [], "out_of_scope": False, "reason": reason}


def judge_site(facts, options, overrides=None):
    """overrides: {방식: {키: 값}} — 방식마다 값이 다른 근거(예: 방식별 최대일)를 덮어쓴다."""
    overrides = overrides or {}
    verdicts = {o: judge_option(o, {**facts, **overrides.get(o, {})}) for o in options}
    seen, union = set(), []
    for v in verdicts.values():
        for m in v["missing"]:
            if m["key"] not in seen:
                seen.add(m["key"])
                union.append(m)
    return {"verdicts": verdicts, "split": len({v["status"] for v in verdicts.values()}) > 1, "missing": union}
