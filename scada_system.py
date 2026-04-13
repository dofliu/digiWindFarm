# wind_turbine_simulator/scada_system.py

import sqlite3
from datetime import datetime
import pandas as pd
from opcua import Client
import threading
import time
from typing import Dict

class TimeSeriesDatabase:
    """時序資料庫"""
    
    def __init__(self, db_path: str = "wind_turbine_data.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化資料庫"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS turbine_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                turbine_id TEXT,
                wind_speed REAL,
                power REAL,
                rotor_speed REAL,
                pitch_angle REAL,
                generator_temp REAL,
                gearbox_temp REAL,
                gearbox_vibration REAL,
                operational_state TEXT,
                yaw_angle REAL,
                hydraulic_pressure REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alarms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                turbine_id TEXT,
                alarm_type TEXT,
                severity TEXT,
                description TEXT,
                acknowledged BOOLEAN DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def insert_data(self, data: Dict):
        """插入資料"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO turbine_data (
                timestamp, turbine_id, wind_speed, power, rotor_speed,
                pitch_angle, generator_temp, gearbox_temp, gearbox_vibration,
                operational_state, yaw_angle, hydraulic_pressure
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now(),
            data.get('turbine_id'),
            data.get('wind_speed'),
            data.get('total_power', 0) / 1000,  # kW
            data.get('rotor', {}).get('rotor_speed', 0),
            data.get('pitch_angle', 0),
            data.get('generator', {}).get('temperature', 0),
            data.get('gearbox', {}).get('temperature', 0),
            data.get('gearbox', {}).get('vibration', 0),
            data.get('operational_state'),
            data.get('yaw', {}).get('yaw_angle', 0),
            data.get('hydraulic', {}).get('pressure', 0)
        ))
        
        conn.commit()
        conn.close()
    
    def get_historical_data(self, turbine_id: str, start_time: datetime, 
                           end_time: datetime) -> pd.DataFrame:
        """獲取歷史資料"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT * FROM turbine_data 
            WHERE turbine_id = ? 
            AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp
        '''
        
        df = pd.read_sql_query(
            query, conn,
            params=(turbine_id, start_time, end_time),
            parse_dates=['timestamp']
        )
        
        conn.close()
        return df

class SCADASystem:
    """SCADA監控系統"""
    
    def __init__(self, opcua_url: str = "opc.tcp://localhost:4840"):
        self.opcua_url = opcua_url
        self.client = None
        self.database = TimeSeriesDatabase()
        self.monitoring_active = False
        self.monitor_thread = None
        
    def connect_to_opcua(self):
        """連接到OPC UA伺服器"""
        self.client = Client(self.opcua_url)
        self.client.connect()
        print(f"Connected to OPC UA server at {self.opcua_url}")
    
    def start_monitoring(self, turbine_ids: list, interval: float = 1.0):
        """開始監控"""
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(turbine_ids, interval)
        )
        self.monitor_thread.start()
    
    def _monitor_loop(self, turbine_ids: list, interval: float):
        """監控循環"""
        while self.monitoring_active:
            for turbine_id in turbine_ids:
                try:
                    data = self._read_turbine_data(turbine_id)
                    self.database.insert_data(data)
                    self._check_alarms(data)
                except Exception as e:
                    print(f"Error reading data for {turbine_id}: {e}")
            
            time.sleep(interval)
    
    def _read_turbine_data(self, turbine_id: str) -> Dict:
        """從OPC UA讀取風機資料"""
        base_path = f"2:WindTurbines/2:{turbine_id}/"
        
        data = {
            'turbine_id': turbine_id,
            'wind_speed': self._read_variable(base_path + "2:WindSpeed"),
            'total_power': self._read_variable(base_path + "2:Power") * 1000,
            'rotor': {
                'rotor_speed': self._read_variable(base_path + "2:RotorSpeed")
            },
            'pitch_angle': self._read_variable(base_path + "2:PitchAngle"),
            'generator': {
                'temperature': self._read_variable(base_path + "2:GeneratorTemp")
            },
            'gearbox': {
                'temperature': self._read_variable(base_path + "2:GearboxTemp"),
                'vibration': self._read_variable(base_path + "2:GearboxVibration")
            },
            'operational_state': self._read_variable(base_path + "2:OperationalState"),
            'yaw': {
                'yaw_angle': self._read_variable(base_path + "2:YawAngle")
            },
            'hydraulic': {
                'pressure': self._read_variable(base_path + "2:HydraulicPressure")
            }
        }
        
        return data
    
    def _read_variable(self, node_path: str):
        """讀取單個變數"""
        try:
            node = self.client.get_node(node_path)
            return node.get_value()
        except:
            return None
    
    def _check_alarms(self, data: Dict):
        """檢查警報條件"""
        alarms = []
        
        # 齒輪箱溫度過高
        if data['gearbox']['temperature'] > 80:
            alarms.append({
                'turbine_id': data['turbine_id'],
                'alarm_type': 'GEARBOX_TEMP_HIGH',
                'severity': 'WARNING',
                'description': f"Gearbox temperature {data['gearbox']['temperature']:.1f}°C exceeds limit"
            })
        
        # 振動過高
        if data['gearbox']['vibration'] > 10:
            alarms.append({
                'turbine_id': data['turbine_id'],
                'alarm_type': 'VIBRATION_HIGH',
                'severity': 'CRITICAL',
                'description': f"Vibration level {data['gearbox']['vibration']:.2f} mm/s is critical"
            })
        
        # 記錄警報
        for alarm in alarms:
            self._log_alarm(alarm)
    
    def _log_alarm(self, alarm: Dict):
        """記錄警報到資料庫"""
        conn = sqlite3.connect(self.database.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alarms (timestamp, turbine_id, alarm_type, severity, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now(),
            alarm['turbine_id'],
            alarm['alarm_type'],
            alarm['severity'],
            alarm['description']
        ))
        
        conn.commit()
        conn.close()
        
        print(f"ALARM: {alarm['severity']} - {alarm['description']}")
    
    def stop_monitoring(self):
        """停止監控"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join()
        if self.client:
            self.client.disconnect()
