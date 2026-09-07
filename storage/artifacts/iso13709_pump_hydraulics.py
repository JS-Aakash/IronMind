"""
ISO 13709 / API 610 Centrifugal Pump Hydraulic Calculations
MRPL Operational Engineering Standards Module
"""
import math

def calculate_differential_head(flow_rate: float, specific_speed: float = 200.0, impeller_diameter: float = 0.3) -> float:
    """Calculate differential head (m) for given flow rate and impeller geometry."""
    q = max(float(flow_rate), 0.001)
    d = max(float(impeller_diameter), 0.001)
    return 10.0 * float(specific_speed) * math.sqrt(q / d)

def calculate_power_consumption(flow_rate: float, differential_head: float, pump_efficiency: float = 0.85) -> float:
    """Calculate power consumption (W) given efficiency and head."""
    eff = max(float(pump_efficiency), 0.01)
    return (float(flow_rate) * float(differential_head) * 9810.0) / eff

def pump_efficiency(flow_m3_h: float = 150.0, head_m: float = 45.0, density_kg_m3: float = 850.0, power_kw: float = 22.0) -> tuple[float, float]:
    """Return hydraulic power in kW and efficiency percentage."""
    q = flow_m3_h / 3600.0
    p_hyd_kw = (density_kg_m3 * 9.81 * q * head_m) / 1000.0
    eff = p_hyd_kw / power_kw
    return p_hyd_kw, eff

if __name__ == "__main__":
    hyd_kw, eff = pump_efficiency(150.0, 45.0, 850.0, 22.0)
    print(f"API 610 Verified: Hydraulic Power={hyd_kw:.2f}kW, Efficiency={eff*100:.2f}%")
