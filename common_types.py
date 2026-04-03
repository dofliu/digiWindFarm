from dataclasses import dataclass

@dataclass
class TurbineParameters:
    """風機基本參數"""
    rated_power: float = 5000000  # 額定功率 (W) - 5MW
    rotor_diameter: float = 126    # 葉輪直徑 (m)
    hub_height: float = 90         # 輪轂高度 (m)
    cut_in_speed: float = 3.0      # 切入風速 (m/s)
    rated_speed: float = 12.0      # 額定風速 (m/s)
    cut_out_speed: float = 25.0    # 切出風速 (m/s)
    air_density: float = 1.225     # 空氣密度 (kg/m³)
