# wind_turbine_simulator/main.py

import time
from datetime import datetime
import threading
from typing import Dict

from wind_model import WindEnvironmentModel
from opcua_interface import OPCUAServer
from scada_system import SCADASystem
from turbine_model import WindTurbine


class WindFarmSimulator:
    """風場模擬器主程式"""

    def __init__(self):
        opcua_url = "opc.tcp://localhost:49000"
        self.wind_model = WindEnvironmentModel()
        self.turbines: Dict[str, WindTurbine] = {}
        self.opcua_server = OPCUAServer(opcua_url)
        self.scada = SCADASystem(opcua_url)

        self.simulation_running = False
        self.simulation_thread: threading.Thread | None = None

    def add_turbine(self, turbine_id: str):
        """添加風機"""
        self.turbines[turbine_id] = WindTurbine(turbine_id)
        self.opcua_server.add_turbine_variables(turbine_id)

    def start_simulation(self, time_step: float = 1.0):
        """開始模擬 (啟動OPC UA + SCADA + 背景模擬執行緒)"""
        # 1. 啟動 OPC UA 伺服器
        #    假設 self.opcua_server.start() 是非阻塞，會立刻回傳
        self.opcua_server.start()

        # 2. 等伺服器起來，避免SCADA太早連
        time.sleep(2)

        # 3. 連接 SCADA
        self.scada.connect_to_opcua()

        # 4. 開始 SCADA 監控
        self.scada.start_monitoring(list(self.turbines.keys()))

        # 5. 啟動模擬主迴圈 (放到背景執行緒)
        self.simulation_running = True
        self.simulation_thread = threading.Thread(
            target=self._simulation_loop,
            args=(time_step,),
            daemon=False  # 我們打算手動join，所以不用daemon
        )
        self.simulation_thread.start()

    def _simulation_loop(self, time_step: float):
        """模擬主循環: 持續更新每台風機的狀態，並同步到OPC UA"""
        try:
            while self.simulation_running:
                current_time = datetime.now()

                # 取得環境條件
                wind_speed = self.wind_model.get_wind_speed(current_time)
                wind_direction = self.wind_model.get_wind_direction(current_time)

                # 更新每一台風機
                for turbine_id, turbine in self.turbines.items():
                    output = turbine.simulate_step(
                        wind_speed,
                        wind_direction,
                        current_time,
                        time_step
                    )

                    # 更新OPC UA
                    self.opcua_server.update_values(turbine_id, output)

                    # 即時輸出
                    self._display_realtime_data(turbine_id, output)

                time.sleep(time_step)

        except Exception as e:
            # 如果模擬執行緒內部發生未預期錯誤，至少印出來，不要靜默卡死
            print(f"[SimulationLoop] Error: {e}")

    def _display_realtime_data(self, turbine_id: str, data: Dict):
        """顯示即時資料 (注意: 這會大量輸出到console，長時間跑可能導致卡頓)"""
        print(f"\n{'='*60}")
        print(f"Turbine: {turbine_id} | Time: {data['timestamp']}")
        print(f"State: {data['operational_state']}")
        print(f"Wind Speed: {data['wind_speed']:.1f} m/s")
        print(f"Power Output: {data['total_power']/1000:.1f} kW")
        print(f"Rotor Speed: {data['rotor'].get('rotor_speed', 0):.1f} RPM")
        print(f"Pitch Angle: {data['pitch_angle']:.1f}°")
        print(f"Generator Temp: {data['generator'].get('temperature', 0):.1f}°C")
        print(f"Gearbox Temp: {data['gearbox'].get('temperature', 0):.1f}°C")

    def stop_simulation(self):
        """停止模擬 (乾淨收攤)"""
        print("[Main] Stopping simulation...")

        # 停止模擬迴圈
        self.simulation_running = False

        # 等模擬執行緒結束
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=5)

        # 停止 SCADA 偵測
        self.scada.stop_monitoring()

        # 關閉 OPC UA 伺服器
        self.opcua_server.stop()

        print("[Main] Simulation stopped cleanly.")


if __name__ == "__main__":
    simulator = WindFarmSimulator()

    # 添加兩台風機
    simulator.add_turbine("WT001")
    simulator.add_turbine("WT002")

    print("[Main] Starting Wind Farm Simulation...")
    try:
        simulator.start_simulation(time_step=1.0)

        # ====== 示範跑30秒後自動關閉 ======
        runtime_sec = 30
        start_t = time.time()
        while time.time() - start_t < runtime_sec:
            time.sleep(1)

    except KeyboardInterrupt:
        print("[Main] KeyboardInterrupt received.")

    except Exception as e:
        print(f"[Main] Error during simulation: {e}")

    finally:
        simulator.stop_simulation()
