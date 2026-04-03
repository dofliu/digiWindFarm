// src/services/opcService.js - OPC DA 通訊服務
const { WindTurbine, RealtimeData } = require('../models');
const logger = require('../utils/logger');
const { saveHistoricalData } = require('./dataService');

// 使用 node-opcda 套件進行 OPC DA 連線
const opcda = require('node-opcda');

class OPCService {
  constructor() {
    this.connections = new Map(); // 儲存每個風機的 OPC 連線
    this.isRunning = false;
    this.reconnectInterval = 5000; // 5秒重連間隔
    this.dataUpdateInterval = 1000; // 1秒資料更新間隔
  }

  // 初始化所有風機的 OPC 連線
  async initializeConnections() {
    try {
      const turbines = await WindTurbine.findAll({
        where: { isActive: true }
      });

      logger.info(`開始初始化 ${turbines.length} 台風機的 OPC 連線`);

      for (const turbine of turbines) {
        await this.createConnection(turbine);
      }

      this.isRunning = true;
      this.startDataCollection();
      
      logger.info('所有 OPC 連線初始化完成');
    } catch (error) {
      logger.error('OPC 連線初始化失敗:', error);
      throw error;
    }
  }

  // 建立單一風機的 OPC 連線
  async createConnection(turbine) {
    try {
      const opcConfig = turbine.opcConfig || this.getDefaultOPCConfig(turbine.id);
      
      const client = new opcda.OPCClient();
      
      // OPC Server 連線設定
      const connectionParams = {
        clsid: opcConfig.clsid || '{F8582CF2-88FB-11D0-B850-00C0F0104305}', // 預設 KepServer CLSID
        host: opcConfig.host || 'localhost',
        progId: opcConfig.progId || 'KEPware.KEPServerEx.V6',
        updateRate: opcConfig.updateRate || 1000
      };

      // 建立連線
      await client.connect(connectionParams);
      
      // 建立群組
      const group = await client.addGroup(`Turbine_${turbine.id}_Group`, {
        updateRate: connectionParams.updateRate,
        active: true
      });

      // 添加資料項目
      const items = this.getTurbineDataItems(turbine.id, opcConfig);
      await group.addItems(items);

      // 設定資料變更事件
      group.onDataChange = (items) => {
        this.handleDataChange(turbine.id, items);
      };

      // 儲存連線資訊
      this.connections.set(turbine.id, {
        client,
        group,
        turbine,
        lastUpdate: new Date(),
        isConnected: true,
        reconnectAttempts: 0
      });

      logger.info(`風機 ${turbine.name} OPC 連線建立成功`);
      
    } catch (error) {
      logger.error(`風機 ${turbine.name} OPC 連線失敗:`, error);
      
      // 設定重新連線
      setTimeout(() => {
        this.reconnectTurbine(turbine.id);
      }, this.reconnectInterval);
    }
  }

  // 取得風機資料項目配置
  getTurbineDataItems(turbineId, opcConfig) {
    const baseTag = opcConfig.baseTag || `Turbine_${turbineId}`;
    
    return [
      // 風況參數
      { name: 'WindSpeed', address: `${baseTag}.WindSpeed` },
      { name: 'WindDirection', address: `${baseTag}.WindDirection` },
      
      // 發電參數
      { name: 'PowerOutput', address: `${baseTag}.PowerOutput` },
      { name: 'Voltage', address: `${baseTag}.Voltage` },
      { name: 'Current', address: `${baseTag}.Current` },
      { name: 'Frequency', address: `${baseTag}.Frequency` },
      
      // 機械參數
      { name: 'RotorRpm', address: `${baseTag}.RotorRpm` },
      { name: 'GeneratorRpm', address: `${baseTag}.GeneratorRpm` },
      { name: 'PitchAngle', address: `${baseTag}.PitchAngle` },
      { name: 'YawAngle', address: `${baseTag}.YawAngle` },
      
      // 溫度參數
      { name: 'NacelleTemperature', address: `${baseTag}.NacelleTemperature` },
      { name: 'GearboxTemperature', address: `${baseTag}.GearboxTemperature` },
      { name: 'GeneratorTemperature', address: `${baseTag}.GeneratorTemperature` },
      { name: 'BearingTemperature', address: `${baseTag}.BearingTemperature` },
      
      // 振動參數
      { name: 'VibrationX', address: `${baseTag}.VibrationX` },
      { name: 'VibrationY', address: `${baseTag}.VibrationY` },
      { name: 'VibrationZ', address: `${baseTag}.VibrationZ` },
      
      // 狀態參數
      { name: 'OperatingStatus', address: `${baseTag}.OperatingStatus` },
      { name: 'FaultCode', address: `${baseTag}.FaultCode` },
      { name: 'MaintenanceStatus', address: `${baseTag}.MaintenanceStatus` }
    ];
  }

  // 處理 OPC 資料變更
  async handleDataChange(turbineId, items) {
    try {
      const connection = this.connections.get(turbineId);
      if (!connection) return;

      // 轉換 OPC 資料格式
      const realtimeData = this.parseOPCData(turbineId, items);
      
      // 儲存到資料庫
      await this.saveRealtimeData(realtimeData);
      
      // 透過 WebSocket 發送即時資料
      this.broadcastRealtimeData(turbineId, realtimeData);
      
      // 更新連線狀態
      connection.lastUpdate = new Date();
      connection.reconnectAttempts = 0;
      
    } catch (error) {
      logger.error(`處理風機 ${turbineId} 資料失敗:`, error);
    }
  }

  // 解析 OPC 資料
  parseOPCData(turbineId, items) {
    const data = {
      turbineId,
      timestamp: new Date()
    };

    items.forEach(item => {
      switch (item.name) {
        case 'WindSpeed':
          data.windSpeed = item.value;
          break;
        case 'WindDirection':
          data.windDirection = item.value;
          break;
        case 'PowerOutput':
          data.powerOutput = item.value;
          break;
        case 'Voltage':
          data.voltage = item.value;
          break;
        case 'Current':
          data.current = item.value;
          break;
        case 'Frequency':
          data.frequency = item.value;
          break;
        case 'RotorRpm':
          data.rotorRpm = item.value;
          break;
        case 'GeneratorRpm':
          data.generatorRpm = item.value;
          break;
        case 'PitchAngle':
          data.pitchAngle = item.value;
          break;
        case 'YawAngle':
          data.yawAngle = item.value;
          break;
        case 'NacelleTemperature':
          data.nacelleTemperature = item.value;
          break;
        case 'GearboxTemperature':
          data.gearboxTemperature = item.value;
          break;
        case 'GeneratorTemperature':
          data.generatorTemperature = item.value;
          break;
        case 'BearingTemperature':
          data.bearingTemperature = item.value;
          break;
        case 'VibrationX':
          data.vibrationX = item.value;
          break;
        case 'VibrationY':
          data.vibrationY = item.value;
          break;
        case 'VibrationZ':
          data.vibrationZ = item.value;
          break;
        case 'OperatingStatus':
          data.operatingStatus = item.value;
          break;
        case 'FaultCode':
          data.faultCode = item.value;
          break;
        case 'MaintenanceStatus':
          data.maintenanceStatus = item.value;
          break;
      }
    });

    return data;
  }

  // 儲存即時資料
  async saveRealtimeData(data) {
    try {
      // 更新即時資料表 (保留最新資料)
      await RealtimeData.upsert(data, {
        where: { turbineId: data.turbineId }
      });

      // 每分鐘儲存歷史資料
      if (new Date().getSeconds() === 0) {
        await saveHistoricalData(data);
      }
      
    } catch (error) {
      logger.error('儲存即時資料失敗:', error);
    }
  }

  // 透過 WebSocket 廣播即時資料
  broadcastRealtimeData(turbineId, data) {
    if (global.io) {
      global.io.to(`turbine_${turbineId}`).emit('realtime_data', {
        turbineId,
        data,
        timestamp: new Date()
      });
    }
  }

  // 重新連線特定風機
  async reconnectTurbine(turbineId) {
    const connection = this.connections.get(turbineId);
    if (!connection) return;

    try {
      connection.reconnectAttempts++;
      logger.info(`嘗試重新連線風機 ${turbineId} (第 ${connection.reconnectAttempts} 次)`);

      // 關閉舊連線
      if (connection.client) {
        try {
          await connection.client.disconnect();
        } catch (error) {
          // 忽略斷線錯誤
        }
      }

      // 建立新連線
      await this.createConnection(connection.turbine);
      
    } catch (error) {
      logger.error(`風機 ${turbineId} 重新連線失敗:`, error);
      
      // 如果重試次數未超過限制，繼續嘗試
      if (connection.reconnectAttempts < 10) {
        setTimeout(() => {
          this.reconnectTurbine(turbineId);
        }, this.reconnectInterval * connection.reconnectAttempts);
      } else {
        logger.error(`風機 ${turbineId} 重新連線失敗次數過多，暫停重試`);
        connection.isConnected = false;
      }
    }
  }

  // 開始資料收集
  startDataCollection() {
    if (this.dataCollectionTimer) {
      clearInterval(this.dataCollectionTimer);
    }

    this.dataCollectionTimer = setInterval(() => {
      this.checkConnections();
    }, 30000); // 每30秒檢查連線狀態
  }

  // 檢查連線狀態
  checkConnections() {
    const now = new Date();
    
    this.connections.forEach((connection, turbineId) => {
      const timeSinceLastUpdate = now - connection.lastUpdate;
      
      // 如果超過5分鐘沒有資料更新，嘗試重新連線
      if (timeSinceLastUpdate > 300000 && connection.isConnected) {
        logger.warn(`風機 ${turbineId} 資料更新逾時，嘗試重新連線`);
        connection.isConnected = false;
        this.reconnectTurbine(turbineId);
      }
    });
  }

  // 停止所有連線
  async stopAllConnections() {
    this.isRunning = false;
    
    if (this.dataCollectionTimer) {
      clearInterval(this.dataCollectionTimer);
    }

    for (const [turbineId, connection] of this.connections) {
      try {
        if (connection.client) {
          await connection.client.disconnect();
        }
        logger.info(`風機 ${turbineId} OPC 連線已關閉`);
      } catch (error) {
        logger.error(`關閉風機 ${turbineId} OPC 連線失敗:`, error);
      }
    }

    this.connections.clear();
    logger.info('所有 OPC 連線已關閉');
  }

  // 取得預設 OPC 設定
  getDefaultOPCConfig(turbineId) {
    return {
      clsid: '{F8582CF2-88FB-11D0-B850-00C0F0104305}',
      host: 'localhost',
      progId: 'KEPware.KEPServerEx.V6',
      updateRate: 1000,
      baseTag: `Turbine_${turbineId}`
    };
  }

  // 取得連線狀態
  getConnectionStatus() {
    const status = {};
    
    this.connections.forEach((connection, turbineId) => {
      status[turbineId] = {
        isConnected: connection.isConnected,
        lastUpdate: connection.lastUpdate,
        reconnectAttempts: connection.reconnectAttempts
      };
    });

    return status;
  }

  // 手動讀取特定風機資料
  async readTurbineData(turbineId) {
    const connection = this.connections.get(turbineId);
    if (!connection || !connection.isConnected) {
      throw new Error(`風機 ${turbineId} 未連線`);
    }

    try {
      const items = await connection.group.read();
      return this.parseOPCData(turbineId, items);
    } catch (error) {
      logger.error(`讀取風機 ${turbineId} 資料失敗:`, error);
      throw error;
    }
  }
}

// 建立單例實例
const opcService = new OPCService();

// 匯出初始化函數
async function initializeOPCConnections() {
  await opcService.initializeConnections();
}

// 優雅關閉處理
process.on('SIGTERM', async () => {
  await opcService.stopAllConnections();
});

process.on('SIGINT', async () => {
  await opcService.stopAllConnections();
});

module.exports = {
  opcService,
  initializeOPCConnections
};

// src/services/dataService.js - 資料處理服務
const { HistoricalData, Alert } = require('../models');
const logger = require('../utils/logger');

// 儲存歷史資料
async function saveHistoricalData(realtimeData) {
  try {
    await HistoricalData.create({
      ...realtimeData,
      timestamp: new Date()
    });
  } catch (error) {
    logger.error('儲存歷史資料失敗:', error);
  }
}

// 檢查告警條件
async function checkAlertConditions(realtimeData) {
  const alerts = [];

  // 風速過高告警
  if (realtimeData.windSpeed > 25) {
    alerts.push({
      turbineId: realtimeData.turbineId,
      alertType: 'high_wind_speed',
      severity: 'high',
      message: `風速過高: ${realtimeData.windSpeed} m/s`,
      value: realtimeData.windSpeed
    });
  }

  // 溫度過高告警
  if (realtimeData.nacelleTemperature > 80) {
    alerts.push({
      turbineId: realtimeData.turbineId,
      alertType: 'high_temperature',
      severity: 'medium',
      message: `機艙溫度過高: ${realtimeData.nacelleTemperature}°C`,
      value: realtimeData.nacelleTemperature
    });
  }

  // 振動異常告警
  if (realtimeData.vibrationX > 10 || realtimeData.vibrationY > 10 || realtimeData.vibrationZ > 10) {
    alerts.push({
      turbineId: realtimeData.turbineId,
      alertType: 'high_vibration',
      severity: 'high',
      message: `振動異常: X=${realtimeData.vibrationX}, Y=${realtimeData.vibrationY}, Z=${realtimeData.vibrationZ}`,
      value: Math.max(realtimeData.vibrationX, realtimeData.vibrationY, realtimeData.vibrationZ)
    });
  }

  // 發電異常告警
  if (realtimeData.powerOutput < 100 && realtimeData.windSpeed > 5) {
    alerts.push({
      turbineId: realtimeData.turbineId,
      alertType: 'low_power_output',
      severity: 'medium',
      message: `發電量異常偏低: ${realtimeData.powerOutput}kW (風速: ${realtimeData.windSpeed}m/s)`,
      value: realtimeData.powerOutput
    });
  }

  // 故障碼告警
  if (realtimeData.faultCode && realtimeData.faultCode !== '0' && realtimeData.faultCode !== '') {
    alerts.push({
      turbineId: realtimeData.turbineId,
      alertType: 'fault_code',
      severity: 'high',
      message: `設備故障: ${realtimeData.faultCode}`,
      value: realtimeData.faultCode
    });
  }

  // 儲存告警記錄
  for (const alert of alerts) {
    try {
      await Alert.create(alert);
      
      // 透過 WebSocket 發送告警通知
      if (global.io) {
        global.io.emit('new_alert', alert);
      }
      
      logger.warn(`風機 ${alert.turbineId} 產生告警: ${alert.message}`);
    } catch (error) {
      logger.error('儲存告警記錄失敗:', error);
    }
  }

  return alerts;
}

// 資料清理 - 清除舊的歷史資料
async function cleanupOldData() {
  try {
    const cutoffDate = new Date();
    cutoffDate.setMonth(cutoffDate.getMonth() - 6); // 保留6個月資料

    const deletedCount = await HistoricalData.destroy({
      where: {
        timestamp: {
          [require('sequelize').Op.lt]: cutoffDate
        }
      }
    });

    logger.info(`清理歷史資料: 刪除 ${deletedCount} 筆記錄`);
  } catch (error) {
    logger.error('清理歷史資料失敗:', error);
  }
}

module.exports = {
  saveHistoricalData,
  checkAlertConditions,
  cleanupOldData
};