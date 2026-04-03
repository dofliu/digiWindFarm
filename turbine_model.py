# wind_turbine_simulator/turbine_model.py

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime
import math

from common_types import TurbineParameters

from subsystems import RotorSystem, GearboxSystem, GeneratorSystem, PitchControlSystem, YawSystem, HydraulicSystem, ControlSystem


class WindTurbine:
    """風力發電機主模型"""
    
    def __init__(self, turbine_id: str = "WT001", params: Optional[TurbineParameters] = None):
        self.turbine_id = turbine_id
        self.params = params or TurbineParameters()
        
        # 子系統
        self.rotor = RotorSystem(self.params)
        self.gearbox = GearboxSystem()
        self.generator = GeneratorSystem(self.params)
        self.pitch_system = PitchControlSystem()
        self.yaw_system = YawSystem()
        self.hydraulic_system = HydraulicSystem()
        self.control_system = ControlSystem()
        
        # 狀態變數
        self.operational_state = "IDLE"  # IDLE, STARTING, RUNNING, STOPPING, FAULT
        self.current_output = {}
        
    def simulate_step(self, wind_speed: float, wind_direction: float, 
                     timestamp: datetime, dt: float = 1.0) -> Dict:
        """
        模擬一個時間步長
        
        Args:
            wind_speed: 風速 (m/s)
            wind_direction: 風向 (度)
            timestamp: 當前時間戳
            dt: 時間步長 (秒)
        
        Returns:
            包含所有輸出參數的字典
        """
        
        # 1. 檢查運行狀態
        self._update_operational_state(wind_speed)
        
        if self.operational_state == "RUNNING":
            # 2. 計算葉輪空氣動力學
            rotor_output = self.rotor.calculate(wind_speed, dt)
            
            # 3. 計算葉片俯仰角控制
            pitch_angle = self.pitch_system.calculate_pitch(
                wind_speed, 
                rotor_output['rotor_speed']
            )
            
            # 4. 齒輪箱轉換
            gearbox_output = self.gearbox.calculate(
                rotor_output['rotor_speed'],
                rotor_output['rotor_torque']
            )
            
            # 5. 發電機輸出
            generator_output = self.generator.calculate(
                gearbox_output['output_speed'],
                gearbox_output['output_torque']
            )
            
            # 6. 偏航系統
            yaw_output = self.yaw_system.calculate(wind_direction)
            
            # 7. 液壓系統
            hydraulic_output = self.hydraulic_system.calculate()
            
        else:
            # 停機或故障狀態
            rotor_output = {'rotor_speed': 0, 'rotor_torque': 0, 'thrust': 0}
            generator_output = {'power': 0, 'voltage': 0, 'current': 0}
            pitch_angle = 90  # 順槳位置
            yaw_output = {'yaw_angle': 0, 'yaw_error': 0}
            hydraulic_output = {'pressure': 0}
        
        # 整合所有輸出
        self.current_output = {
            'timestamp': timestamp.isoformat(),
            'turbine_id': self.turbine_id,
            'operational_state': self.operational_state,
            'wind_speed': wind_speed,
            'wind_direction': wind_direction,
            'rotor': rotor_output,
            'pitch_angle': pitch_angle,
            'gearbox': gearbox_output if self.operational_state == "RUNNING" else {},
            'generator': generator_output,
            'yaw': yaw_output,
            'hydraulic': hydraulic_output,
            'total_power': generator_output.get('power', 0),
        }
        
        return self.current_output
    
    def _update_operational_state(self, wind_speed: float):
        """更新運行狀態"""
        if wind_speed < self.params.cut_in_speed:
            self.operational_state = "IDLE"
        elif wind_speed > self.params.cut_out_speed:
            self.operational_state = "STOPPING"
        elif self.params.cut_in_speed <= wind_speed <= self.params.cut_out_speed:
            if self.operational_state in ["IDLE", "STOPPING"]:
                self.operational_state = "STARTING"
            elif self.operational_state == "STARTING":
                self.operational_state = "RUNNING"
