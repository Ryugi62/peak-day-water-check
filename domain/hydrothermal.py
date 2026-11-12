"""수열(댐·하천 냉수) 통과 냉각 — 순수 계산. 증발로 사라지는 물은 0에 가깝지만, 열을 실어 나를 통과(취수→방류) 유량이 필요하다.
유량 = 방열량 ÷ (비열 × 온도 상승). 물 비열 4.186 kJ/kg·K, 밀도 1,000 kg/m³."""
CP_KJ = 4.186


def passthrough_flow_m3_per_day(heat_mw, delta_t_k):
    if delta_t_k <= 0:
        raise ValueError("온도 상승은 양수")
    kg_s = heat_mw * 1000.0 / (CP_KJ * delta_t_k)
    return kg_s * 86400 / 1000.0
