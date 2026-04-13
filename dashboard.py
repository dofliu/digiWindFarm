# wind_turbine_simulator/dashboard.py

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
from datetime import datetime, timedelta

from scada_system import TimeSeriesDatabase

class WindTurbineDashboard:
    """風機監控儀表板"""
    
    def __init__(self, database_path: str = "wind_turbine_data.db"):
        self.database = TimeSeriesDatabase(database_path)
        self.app = dash.Dash(__name__)
        self._setup_layout()
        self._setup_callbacks()
    
    def _setup_layout(self):
        """設置儀表板布局"""
        self.app.layout = html.Div([
            html.H1('Wind Turbine Monitoring Dashboard', 
                   style={'textAlign': 'center'}),
            
            # 風機選擇
            html.Div([
                html.Label('Select Turbine:'),
                dcc.Dropdown(
                    id='turbine-selector',
                    options=[
                        {'label': 'WT001', 'value': 'WT001'},
                        {'label': 'WT002', 'value': 'WT002'}
                    ],
                    value='WT001'
                )
            ], style={'width': '30%'}),
            
            # 即時資料卡片
            html.Div(id='realtime-cards', className='row'),
            
            # 圖表
            html.Div([
                # 功率曲線
                dcc.Graph(id='power-chart'),
                
                # 風速vs功率散點圖
                dcc.Graph(id='power-curve-chart'),
                
                # 溫度趨勢
                dcc.Graph(id='temperature-chart'),
                
                # 振動趨勢
                dcc.Graph(id='vibration-chart')
            ]),
            
            # 自動更新
            dcc.Interval(
                id='interval-component',
                interval=5*1000,  # 5秒更新一次
                n_intervals=0
            )
        ])
    
    def _setup_callbacks(self):
        """設置回調函數"""
        
        @self.app.callback(
            [Output('power-chart', 'figure'),
             Output('temperature-chart', 'figure'),
             Output('vibration-chart', 'figure'),
             Output('power-curve-chart', 'figure')],
            [Input('interval-component', 'n_intervals'),
             Input('turbine-selector', 'value')]
        )
        def update_charts(n, turbine_id):
            # 獲取最近24小時的資料
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            df = self.database.get_historical_data(
                turbine_id, start_time, end_time
            )
            
            if df.empty:
                empty_fig = go.Figure()
                return empty_fig, empty_fig, empty_fig, empty_fig
            
            # 功率趨勢圖
            power_fig = go.Figure()
            power_fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['power'],
                mode='lines',
                name='Power Output'
            ))
            power_fig.update_layout(
                title='Power Output Trend',
                xaxis_title='Time',
                yaxis_title='Power (kW)'
            )
            
            # 溫度趨勢圖
            temp_fig = go.Figure()
            temp_fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['generator_temp'],
                mode='lines',
                name='Generator'
            ))
            temp_fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['gearbox_temp'],
                mode='lines',
                name='Gearbox'
            ))
            temp_fig.update_layout(
                title='Temperature Trends',
                xaxis_title='Time',
                yaxis_title='Temperature (°C)'
            )
            
            # 振動趨勢圖
            vib_fig = go.Figure()
            vib_fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['gearbox_vibration'],
                mode='lines',
                name='Vibration'
            ))
            vib_fig.update_layout(
                title='Gearbox Vibration',
                xaxis_title='Time',
                yaxis_title='Vibration (mm/s)'
            )
            
            # 功率曲線散點圖
            pc_fig = go.Figure()
            pc_fig.add_trace(go.Scatter(
                x=df['wind_speed'],
                y=df['power'],
                mode='markers',
                name='Actual',
                marker=dict(size=5)
            ))
            pc_fig.update_layout(
                title='Power Curve',
                xaxis_title='Wind Speed (m/s)',
                yaxis_title='Power (kW)'
            )
            
            return power_fig, temp_fig, vib_fig, pc_fig
    
    def run(self, debug=True, port=8050):
        """運行儀表板"""
        self.app.run_server(debug=debug, port=port)
