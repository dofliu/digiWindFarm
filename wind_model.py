# wind_turbine_simulator/wind_model.py
import numpy as np
from datetime import datetime


class WindEnvironmentModel:
    """風場環境模型"""
    
    def __init__(self):
        self.base_pattern = self._create_daily_pattern()
        self.turbulence_intensity = 0.1
        
    def _create_daily_pattern(self):
        """創建日常風速模式"""
        hours = np.arange(0, 24, 0.1)
        pattern = np.zeros_like(hours)
        
        for i, hour in enumerate(hours):
            if 0 <= hour < 6:  # 凌晨
                pattern[i] = 4 + np.sin(hour * np.pi / 6)
            elif 6 <= hour < 12:  # 上午
                pattern[i] = 3 + 4 * (hour - 6) / 6
            elif 12 <= hour < 18:  # 下午
                pattern[i] = 7 + 3 * np.sin((hour - 12) * np.pi / 6)
            else:  # 晚上
                pattern[i] = 4 + 2 * np.cos((hour - 18) * np.pi / 6)
        
        return pattern
    
    def get_wind_speed(self, timestamp: datetime) -> float:
        """
        獲取指定時間的風速
        包含基本模式和湍流
        """
        hour_of_day = timestamp.hour + timestamp.minute / 60
        index = int(hour_of_day * 10)
        base_speed = self.base_pattern[index % len(self.base_pattern)]
        
        # 添加湍流
        turbulence = np.random.normal(0, base_speed * self.turbulence_intensity)
        
        return max(0, base_speed + turbulence)
    
    def get_wind_direction(self, timestamp: datetime) -> float:
        """獲取風向"""
        # 簡化模型：風向緩慢變化
        base_direction = 270  # 西風
        variation = 30 * np.sin(timestamp.hour * np.pi / 12)
        return (base_direction + variation) % 360
