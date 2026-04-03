# Project Overview

This project, `digiWindTurbine`, appears to be a simulation and monitoring system for a wind farm. It simulates the behavior of wind turbines, collects data, stores it in a time-series database, and provides a dashboard for visualization. It also includes an OPC UA server for industrial communication and a SCADA system for monitoring and control.

## Key Components:

*   **`main.py`**: The main entry point for the wind farm simulator, orchestrating the wind model, turbines, OPC UA server, and SCADA system.
*   **`wind_model.py`**: Simulates wind speed and direction based on daily patterns and turbulence.
*   **`turbine_model.py`**: Defines the `WindTurbine` class, which models the physical and operational aspects of a wind turbine. It integrates various subsystems to simulate the turbine's behavior under different wind conditions.
*   **`subsystems.py`**: Contains detailed implementations of the individual wind turbine subsystems, including:
    *   `RotorSystem`: Calculates rotor speed, torque, and thrust based on wind speed and power coefficient.
    *   `GearboxSystem`: Simulates the gearbox, converting rotor output to generator input, and models temperature and vibration.
    *   `GeneratorSystem`: Calculates electrical power output, voltage, current, and temperature.
    *   `PitchControlSystem`: Adjusts blade pitch angle to optimize power capture and limit power in high winds.
    *   `YawSystem`: Controls the turbine's orientation to face the wind.
    *   `HydraulicSystem`: Simulates hydraulic pressure.
    *   `ControlSystem`: A placeholder for higher-level control logic.
*   **`opcua_interface.py`**: Implements an OPC UA server to expose turbine data for industrial communication, allowing external systems to read and potentially write turbine parameters.
*   **`scada_system.py`**: Acts as a SCADA (Supervisory Control and Data Acquisition) system. It connects to the OPC UA server, periodically collects real-time data from the simulated turbines, stores this data in a `TimeSeriesDatabase` (SQLite), and includes logic for checking and logging alarms based on predefined thresholds.
*   **`dashboard.py`**: Provides a web-based dashboard using Dash and Plotly for real-time visualization of turbine data and trends. It allows users to select turbines and view power output, temperature, vibration trends, and power curves.
*   **`main_architecture.py`**: Seems to define the overall system architecture, though its current role might be more for conceptual organization or future expansion.

## Technologies Used:

*   **Python**: The primary programming language for the entire simulation and monitoring system.
*   **Dash/Plotly**: Used in `dashboard.py` for creating interactive and dynamic web-based data visualizations.
*   **OPC UA (python-opcua library)**: Facilitates industrial communication, enabling the simulated wind turbines to expose their data in a standardized way.
*   **SQLite**: Employed in `scada_system.py` as a lightweight time-series database for storing historical turbine data and alarms.
*   **Pandas**: Utilized in `scada_system.py` and `dashboard.py` for efficient data manipulation, analysis, and retrieval from the SQLite database.
*   **Numpy**: Used for numerical operations, particularly in the `wind_model.py` and `subsystems.py` for simulating physical phenomena and adding randomness (e.g., turbulence).
*   **Threading**: Used in `main.py` and `scada_system.py` to manage concurrent tasks, such as the main simulation loop and background data monitoring.

## Setup and Running:

To set up and run this project, follow these steps:

1.  **Create a `requirements.txt` file**:
    ```bash
    echo "dash" > requirements.txt
    echo "plotly" >> requirements.txt
    echo "pandas" >> requirements.txt
    echo "numpy" >> requirements.txt
    echo "python-opcua" >> requirements.txt
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the main simulation**:
    Open your terminal or command prompt and navigate to the project directory. Then, execute:
    ```bash
    python main.py
    ```
    This will start the OPC UA server and the wind farm simulation, which will begin generating and exposing turbine data.

4.  **Run the dashboard (in a separate terminal)**:
    Open a *new* terminal or command prompt, navigate to the project directory, and execute:
    ```bash
    python dashboard.py
    ```
    This will start the Dash web server. You can then access the wind turbine monitoring dashboard in your web browser, typically at `http://127.0.0.1:8050/`.

## Development Conventions:

*   **Modularity**: The project is well-structured into several Python files, each responsible for a specific part of the simulation or monitoring system, promoting code organization and reusability.
*   **Object-Oriented Programming**: Classes are used extensively to model different components (e.g., `WindTurbine`, `OPCUAServer`, `SCADASystem`, and various `Subsystems`), encapsulating their behavior and data.
*   **Comments**: Code includes comments, often in Chinese, explaining the purpose of classes, methods, and complex sections, which aids in understanding the codebase.
*   **Data Handling**: SQLite is used for persistent data storage, and Pandas DataFrames are used for efficient historical data retrieval and analysis, especially within the SCADA and dashboard components.
*   **Real-time Aspects**: The project leverages `threading` for concurrent operations (e.g., simulation loop, SCADA monitoring) and `dcc.Interval` in Dash for periodic updates on the dashboard, enabling real-time data display.

## Future Enhancements/Considerations:

*   **Error Handling**: Enhance error handling and logging across the system for better robustness and debugging.
*   **Configuration**: Externalize configuration parameters (e.g., OPC UA endpoint, database path, turbine parameters, alarm thresholds) into a separate configuration file (e.g., YAML, JSON) to make the system more flexible and easier to manage.
*   **Testing**: Add comprehensive unit and integration tests for different components to ensure correctness and prevent regressions.
*   **Advanced Subsystem Models**: Further refine the physical models within `subsystems.py` to incorporate more complex aerodynamics, mechanical dynamics, and electrical characteristics for a more realistic simulation.
*   **Alarm Management**: Implement more sophisticated alarm management features, including alarm acknowledgment, historical alarm viewing, and different alarm priorities/escalation.
*   **Security**: For a real-world OPC UA deployment, robust security considerations (e.g., authentication, authorization, encryption) would be paramount and should be implemented.
*   **Scalability**: Consider how the system would scale to a larger number of turbines and higher data rates, potentially exploring more advanced database solutions or distributed architectures.
