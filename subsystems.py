# wind_turbine_simulator/subsystems.py

import numpy as np
from typing import Dict
from common_types import TurbineParameters

class RotorSystem:
    """葉輪系統模型"""
    
    def __init__(self, params: TurbineParameters):
        self.params = params
        self.rotor_speed = 0  # RPM
        self.rotor_inertia = 5000000  # kg·m²
        
    def calculate(self, wind_speed: float, dt: float) -> Dict:
        """
        計算葉輪空氣動力學
        基於動量理論和葉素理論
        """
        # 計算掃風面積
        swept_area = np.pi * (self.params.rotor_diameter / 2) ** 2
        
        # 計算尖速比 (Tip Speed Ratio)
        if wind_speed > 0:
            tsr = (self.rotor_speed * np.pi * self.params.rotor_diameter / 60) / wind_speed
        else:
            tsr = 0
        
        # 計算功率係數 Cp (簡化模型)
        cp = self._calculate_cp(tsr)
        
        # 計算風能功率
        wind_power = 0.5 * self.params.air_density * swept_area * wind_speed ** 3
        
        # 計算葉輪功率和扭矩
        rotor_power = wind_power * cp
        if self.rotor_speed > 0:
            rotor_torque = rotor_power / (self.rotor_speed * 2 * np.pi / 60)
        else:
            rotor_torque = 0
        
        # 計算推力
        ct = self._calculate_ct(tsr)  # 推力係數
        thrust = 0.5 * self.params.air_density * swept_area * wind_speed ** 2 * ct
        
        # 更新轉速 (簡化的動力學模型)
        if wind_speed >= self.params.cut_in_speed:
            target_rpm = self._optimal_rotor_speed(wind_speed)
            self.rotor_speed += (target_rpm - self.rotor_speed) * 0.1 * dt
        else:
            self.rotor_speed *= 0.95  # 減速
        
        return {
            'rotor_speed': self.rotor_speed,
            'rotor_torque': rotor_torque,
            'rotor_power': rotor_power,
            'thrust': thrust,
            'cp': cp,
            'tsr': tsr
        }
    
    def _calculate_cp(self, tsr: float) -> float:
        """計算功率係數 (簡化的貝茲理論曲線)"""
        if tsr <= 0 or tsr > 12:
            return 0
        # 簡化的Cp曲線，峰值約在TSR=7-8
        optimal_tsr = 7.5
        cp_max = 0.48
        return cp_max * np.exp(-0.5 * ((tsr - optimal_tsr) / 2.5) ** 2)
    
    def _calculate_ct(self, tsr: float) -> float:
        """計算推力係數"""
        if tsr <= 0:
            return 0
        return min(0.9, 0.4 + 0.1 * tsr)
    
    def _optimal_rotor_speed(self, wind_speed: float) -> float:
        """計算最佳轉速 (RPM)"""
        optimal_tsr = 7.5
        return (optimal_tsr * wind_speed * 60) / (np.pi * self.params.rotor_diameter)

class GearboxSystem:
    """齒輪箱系統模型"""
    
    def __init__(self, gear_ratio: float = 100, efficiency: float = 0.97):
        self.gear_ratio = gear_ratio
        self.efficiency = efficiency
        self.temperature = 50  # °C
        self.vibration_level = 0  # mm/s
        self.oil_pressure = 2.5  # bar
        
    def calculate(self, input_speed: float, input_torque: float) -> Dict:
        """計算齒輪箱輸出"""
        output_speed = input_speed * self.gear_ratio
        output_torque = input_torque / self.gear_ratio * self.efficiency
        
        # 模擬溫度變化
        power_loss = input_torque * input_speed * (1 - self.efficiency) * 2 * np.pi / 60
        self.temperature = 50 + power_loss / 100000  # 簡化的熱模型
        
        # 模擬振動
        self.vibration_level = 0.5 + np.random.normal(0, 0.1) + output_speed / 10000
        
        return {
            'output_speed': output_speed,
            'output_torque': output_torque,
            'temperature': self.temperature,
            'vibration': self.vibration_level,
            'oil_pressure': self.oil_pressure,
            'efficiency': self.efficiency
        }

class GeneratorSystem:
    """發電機系統模型"""
    
    def __init__(self, params: TurbineParameters):
        self.params = params
        self.efficiency = 0.95
        self.power_factor = 0.95
        self.temperature = 60  # °C
        
    def calculate(self, speed: float, torque: float) -> Dict:
        """計算發電機輸出"""
        mechanical_power = torque * speed * 2 * np.pi / 60
        electrical_power = min(mechanical_power * self.efficiency, self.params.rated_power)
        
        # 簡化的電氣參數計算
        if electrical_power > 0:
            voltage = 690  # V (典型的風機發電機電壓)
            current = electrical_power / (voltage * np.sqrt(3) * self.power_factor)
            frequency = speed * 2 / 60  # 假設4極發電機
        else:
            voltage = 0
            current = 0
            frequency = 0
        
        # 溫度模型
        power_loss = mechanical_power * (1 - self.efficiency)
        self.temperature = 60 + power_loss / 50000
        
        return {
            'power': electrical_power,
            'voltage': voltage,
            'current': current,
            'frequency': frequency,
            'power_factor': self.power_factor,
            'temperature': self.temperature,
            'efficiency': self.efficiency
        }

class PitchControlSystem:
    """葉片俯仰角控制系統"""
    
    def __init__(self):
        self.max_pitch_rate = 8  # 度/秒
        self.current_pitch = 0
        
    def calculate_pitch(self, wind_speed: float, rotor_speed: float) -> float:
        """
        計算最佳俯仰角
        低風速時為0度，高風速時增加俯仰角以限制功率
        """
        if wind_speed < 3:
            target_pitch = 90  # 順槳
        elif wind_speed < 12:
            target_pitch = 0  # 最佳角度
        else:
            # 高風速時的俯仰角控制
            target_pitch = min(30, (wind_speed - 12) * 3)
        
        # 限制變化率
        pitch_change = np.clip(
            target_pitch - self.current_pitch,
            -self.max_pitch_rate,
            self.max_pitch_rate
        )
        self.current_pitch += pitch_change
        
        return self.current_pitch

class YawSystem:
    """偏航系統"""
    def __init__(self):
        self.yaw_angle = 0.0 # 初始偏航角 (度)
        self.yaw_error = 0.0 # 偏航誤差 (度)
        
    def calculate(self, wind_direction: float) -> Dict:
        """
        計算偏航角
        
        Args:
            wind_direction: 當前風向 (度)
            
        Returns:
            包含偏航角和偏航誤差的字典
        """
        # 簡化偏航控制邏輯
        # 目標是使風機正對風向
        
        # 計算風向與當前偏航角的誤差
        error = wind_direction - self.yaw_angle
        
        # 調整誤差到 -180 到 180 之間
        if error > 180:
            error -= 360
        elif error < -180:
            error += 360
            
        self.yaw_error = error
        
        # 模擬偏航動作 (緩慢調整)
        if abs(self.yaw_error) > 5: # 如果誤差超過5度，則調整
            self.yaw_angle += np.sign(self.yaw_error) * 0.5 # 每次調整0.5度
            self.yaw_angle = self.yaw_angle % 360 # 保持在0-360度
            
        return {
            'yaw_angle': self.yaw_angle,
            'yaw_error': self.yaw_error
        }

class HydraulicSystem:
    """液壓系統"""
    def __init__(self):
        self.pressure = 150.0 # 初始壓力 (bar)
        
    def calculate(self) -> Dict:
        """
        計算液壓系統狀態
        
        Returns:
            包含壓力的字典
        """
        # 模擬壓力波動 (簡化)
        self.pressure += np.random.normal(0, 0.5)
        self.pressure = max(100, min(self.pressure, 200)) # 限制在合理範圍
        
        return {
            'pressure': self.pressure
        }

class ControlSystem:
    """主控制系統 (簡化)"""
    def __init__(self):
        pass
        
    def calculate_control_actions(self, turbine_data: Dict) -> Dict:
        """
        根據風機資料計算控制動作
        
        Args:
            turbine_data: 當前風機資料
            
        Returns:
            控制動作的字典 (例如：變槳指令、偏航指令)
        """
        # 這裡可以實現更複雜的PID控制、故障檢測等
        return {}
