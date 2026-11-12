"""재이용 공급원 매칭 — 순수 계산. 공공하수처리시설 방류량(m³/일, 연평균)을 데이터센터 최대일 수요와 견준다.
v2(2026-10-06): 순공급 = (방류량 × 갈수기 계수 − 기존 재이용량) × (1 − 하천 유지 몫) × 재처리 회수율 — 장내 용수는 갈수기에도 줄지 않으므로 계수를 먼저 곱하고 뺀다(보수적).
v1은 (방류량 − 기존 재이용) × 갈수기 계수 … 로 건기 순공급을 과대평가했다."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Plant:
    name: str
    capacity_m3: float      # 시설용량(m³/일)
    effluent_m3: float      # 방류량(m³/일, 연평균)
    existing_reuse_m3: float = 0.0   # 이미 쓰이는 재이용량(장내+장외, m³/일)


def reuse_options(plants, peak_day_m3, min_capacity_m3=5000):
    big = sorted((p for p in plants if p.capacity_m3 >= min_capacity_m3), key=lambda p: -p.effluent_m3)
    rows = [{"name": p.name, "capacity_m3": p.capacity_m3, "effluent_m3": p.effluent_m3, "existing_reuse_m3": p.existing_reuse_m3,
             "coverage_x": p.effluent_m3 / peak_day_m3 if peak_day_m3 else 0.0,
             "share_needed_pct": peak_day_m3 / p.effluent_m3 * 100 if p.effluent_m3 else float("inf")} for p in big]
    return {"plants": rows, "total_effluent_m3": sum(p.effluent_m3 for p in big),
            "best_coverage_x": rows[0]["coverage_x"] if rows else 0.0}


def net_supply_m3(plant, low_flow, stream_reserve, recovery):
    free = max(0.0, plant.effluent_m3 * low_flow - plant.existing_reuse_m3)
    return free * (1.0 - stream_reserve) * recovery


def outfall_reuse_deduction(in_plant_m3, offsite_m3, inflow_m3, outflow_m3):
    """v6: 수질TMS 방류량은 「최종 방류구」 계측(SOOSIRO 용어사전)이라, 방류구 앞에서 쓰는 재이용은 이미 빠져 있다.
    장내용수는 처리장 안에서 쓰고 되돌아가므로 차감 0. 장외용수 중 방류구 앞 취수분은 유입−방류 이하 →
    기준 = 장외 − (유입−방류), 보수 = 장외 전량(모두 방류구 뒤에서 취수한다고 가정). 단위 m³/일."""
    if min(in_plant_m3, offsite_m3, inflow_m3, outflow_m3) < 0:
        raise ValueError("음수 입력")
    pre = max(0.0, inflow_m3 - outflow_m3)
    return {"base": max(0.0, offsite_m3 - pre), "conservative": float(offsite_m3)}


def low_flow_ratio(monthly_m3):
    """갈수기 계수(실측) = 월평균 방류량의 최솟값 ÷ 전체 평균(v5). monthly_m3: {"YYYY-MM": m³/일}."""
    vals = list(monthly_m3.values())
    if not vals:
        raise ValueError("월별 값 없음")
    mean = sum(vals) / len(vals)
    if mean <= 0:
        raise ValueError("평균 방류량은 양수")
    return min(vals) / mean


def monthly_ratio_profile(monthly_m3):
    """달력 월별(01~12) 평균 ÷ 전체 평균 — 계절별 공급량에 곱할 비율(v5)."""
    if not monthly_m3:
        raise ValueError("월별 값 없음")
    mean = sum(monthly_m3.values()) / len(monthly_m3)
    if mean <= 0:
        raise ValueError("평균 방류량은 양수")
    by = {}
    for k, v in monthly_m3.items():
        by.setdefault(k[5:7], []).append(v)
    return {m: (sum(v) / len(v)) / mean for m, v in sorted(by.items())}


def monthly_binding(supply_by_month, demand_peak_by_month):
    """달력 월별 순공급 ÷ 그 달 최대일 수요 → 가장 작은 달이 판정 달(v5). 수요 0인 달(외기냉방)은 제외."""
    if set(supply_by_month) != set(demand_peak_by_month):
        raise ValueError("공급·수요의 달 목록이 다르다")
    by = {m: supply_by_month[m] / demand_peak_by_month[m] for m in sorted(supply_by_month) if demand_peak_by_month[m] > 0}
    if not by:
        raise ValueError("수요가 있는 달이 없다")
    bm = min(by, key=by.get)
    return {"by_month": by, "binding_month": bm, "binding_x": by[bm]}


def grade(x):
    """순공급 ÷ 최대일 배수 → 등급(1쪽 리포트와 같은 규칙): 2배 이상 적합 · 1~2배 조건부 · 1배 미만 부적합."""
    return "적합" if x >= 2.0 else ("조건부" if x >= 1.0 else "부적합")


def required_effluent_m3(peak_m3, existing_reuse_m3, low_flow, stream_reserve, recovery, target_x):
    """net_supply_m3 의 역: 순공급이 최대일 × target_x가 되는 데 필요한 연평균 방류량(m³/일)."""
    if min(peak_m3, low_flow, recovery, target_x) <= 0 or not 0 <= stream_reserve < 1:
        raise ValueError("입력 범위 오류")
    return (target_x * peak_m3 / ((1.0 - stream_reserve) * recovery) + existing_reuse_m3) / low_flow
