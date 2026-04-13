# wind_turbine_simulator/opcua_interface.py

from opcua import Server, ua
from threading import Thread
from typing import Dict

class OPCUAServer:
    """OPC UA 伺服器"""
    
    def __init__(self, endpoint: str = "opc.tcp://localhost:49000"):
        self.server = Server()
        self.server.set_endpoint(endpoint)
        self.server.set_server_name("Wind Turbine Simulator OPC UA Server")
        
        # 設置命名空間
        self.uri = "http://windturbine.simulator"
        self.idx = self.server.register_namespace(self.uri)
        
        # 創建對象結構
        self.objects = self.server.get_objects_node()
        self.turbine_folder = None
        self.variables = {}
        self.server_thread = None
        
        self._setup_address_space()
        
    def _setup_address_space(self):
        """設置OPC UA地址空間"""
        # 創建風機文件夾
        self.turbine_folder = self.objects.add_folder(self.idx, "WindTurbines")
        
    def add_turbine_variables(self, turbine_id: str):
        """為風機添加變數"""
        turbine_node = self.turbine_folder.add_folder(self.idx, turbine_id)
        
        variables = {
            'WindSpeed': 0.0,
            'Power': 0.0,
            'RotorSpeed': 0.0,
            'PitchAngle': 0.0,
            'GeneratorTemp': 0.0,
            'GearboxTemp': 0.0,
            'GearboxVibration': 0.0,
            'OperationalState': 'IDLE',
            'YawAngle': 0.0,
            'HydraulicPressure': 0.0
        }
        
        self.variables[turbine_id] = {}
        
        for var_name, initial_value in variables.items():
            if isinstance(initial_value, str):
                var = turbine_node.add_variable(
                    self.idx, var_name, initial_value,
                    varianttype=ua.VariantType.String
                )
            else:
                var = turbine_node.add_variable(
                    self.idx, var_name, initial_value,
                    varianttype=ua.VariantType.Double
                )
            var.set_writable()
            self.variables[turbine_id][var_name] = var
    
    def update_values(self, turbine_id: str, data: Dict):
        """更新OPC UA變數值"""
        if turbine_id in self.variables:
            mapping = {
                'WindSpeed': data.get('wind_speed', 0),
                'Power': data.get('total_power', 0) / 1000,  # 轉換為kW
                'RotorSpeed': data.get('rotor', {}).get('rotor_speed', 0),
                'PitchAngle': data.get('pitch_angle', 0),
                'GeneratorTemp': data.get('generator', {}).get('temperature', 0),
                'GearboxTemp': data.get('gearbox', {}).get('temperature', 0),
                'GearboxVibration': data.get('gearbox', {}).get('vibration', 0),
                'OperationalState': data.get('operational_state', 'UNKNOWN'),
                'YawAngle': data.get('yaw', {}).get('yaw_angle', 0),
                'HydraulicPressure': data.get('hydraulic', {}).get('pressure', 0)
            }
            
            for var_name, value in mapping.items():
                if var_name in self.variables[turbine_id]:
                    self.variables[turbine_id][var_name].set_value(value)
    
    def start(self):
        """啟動OPC UA伺服器"""
        self.server_thread = Thread(target=self.server.start)
        self.server_thread.start()
        print(f"OPC UA Server started at {self.server.endpoint}")
    
    def stop(self):
        """停止OPC UA伺服器"""
        if self.server_thread:
            self.server.stop()
            self.server_thread.join()
            self.server_thread = None
