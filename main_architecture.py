# wind_turbine_simulator/main_architecture.py

class WindTurbineSimulatorSystem:
    """
    離岸風力發電場模擬系統主架構
    """
    def __init__(self):
        self.wind_model = WindEnvironmentModel()
        self.turbine = WindTurbine()
        self.opcua_server = OPCUAServer()
        self.scada_system = SCADASystem()
        self.database = TimeSeriesDatabase()
