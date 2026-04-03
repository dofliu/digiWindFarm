// src/routes/index.js - 主路由檔案
const express = require('express');
const router = express.Router();

// 導入各個路由模組
const authRoutes = require('./auth');
const turbineRoutes = require('./turbines');
const dataRoutes = require('./data');
const alertRoutes = require('./alerts');
const reportRoutes = require('./reports');

// 路由設定
router.use('/auth', authRoutes);
router.use('/turbines', turbineRoutes);
router.use('/data', dataRoutes);
router.use('/alerts', alertRoutes);
router.use('/reports', reportRoutes);

// 健康檢查端點
router.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

module.exports = router;

// src/routes/turbines.js - 風機相關路由
const express = require('express');
const router = express.Router();
const turbineController = require('../controllers/turbineController');
const { authenticateToken } = require('../middleware/auth');

// 所有路由都需要認證
router.use(authenticateToken);

// 風機基本資料
router.get('/', turbineController.getAllTurbines);
router.get('/:id', turbineController.getTurbineById);
router.post('/', turbineController.createTurbine);
router.put('/:id', turbineController.updateTurbine);
router.delete('/:id', turbineController.deleteTurbine);

// 風機即時資料
router.get('/:id/realtime', turbineController.getRealtimeData);
router.get('/:id/status', turbineController.getTurbineStatus);

// 風機控制
router.post('/:id/start', turbineController.startTurbine);
router.post('/:id/stop', turbineController.stopTurbine);
router.post('/:id/maintenance', turbineController.setMaintenanceMode);

module.exports = router;

// src/controllers/turbineController.js - 風機控制器
const { WindTurbine, RealtimeData } = require('../models');
const { opcService } = require('../services/opcService');
const logger = require('../utils/logger');

class TurbineController {
  // 取得所有風機
  async getAllTurbines(req, res) {
    try {
      const turbines = await WindTurbine.findAll({
        include: [{
          model: RealtimeData,
          limit: 1,
          order: [['timestamp', 'DESC']]
        }],
        order: [['name', 'ASC']]
      });

      res.json({
        success: true,
        data: turbines,
        total: turbines.length
      });
    } catch (error) {
      logger.error('取得風機清單失敗:', error);
      res.status(500).json({
        success: false,
        message: '取得風機清單失敗',
        error: error.message
      });
    }
  }

  // 取得單一風機詳細資訊
  async getTurbineById(req, res) {
    try {
      const { id } = req.params;
      
      const turbine = await WindTurbine.findByPk(id, {
        include: [{
          model: RealtimeData,
          limit: 1,
          order: [['timestamp', 'DESC']]
        }]
      });

      if (!turbine) {
        return res.status(404).json({
          success: false,
          message: '找不到指定的風機'
        });
      }

      res.json({
        success: true,
        data: turbine
      });
    } catch (error) {
      logger.error('取得風機詳細資訊失敗:', error);
      res.status(500).json({
        success: false,
        message: '取得風機詳細資訊失敗',
        error: error.message
      });
    }
  }

  // 建立新風機
  async createTurbine(req, res) {
    try {
      const turbineData = req.body;
      
      const turbine = await WindTurbine.create(turbineData);
      
      // 如果風機設為啟用，建立 OPC 連線
      if (turbine.isActive) {
        await opcService.createConnection(turbine);
      }

      res.status(201).json({
        success: true,
        data: turbine,
        message: '風機建立成功'
      });
    } catch (error) {
      logger.error('建立風機失敗:', error);
      res.status(500).json({
        success: false,
        message: '建立風機失敗',
        error: error.message
      });
    }
  }

  // 更新風機資訊
  async updateTurbine(req, res) {
    try {
      const { id } = req.params;
      const updateData = req.body;

      const turbine = await WindTurbine.findByPk(id);
      if (!turbine) {
        return res.status(404).json({
          success: false,
          message: '找不到指定的風機'
        });
      }

      await turbine.update(updateData);

      res.json({
        success: true,
        data: turbine,
        message: '風機資訊更新成功'
      });
    } catch (error) {
      logger.error('更新風機資訊失敗:', error);
      res.status(500).json({
        success: false,
        message: '更新風機資訊失敗',
        error: error.message
      });
    }
  }

  // 取得即時資料
  async getRealtimeData(req, res) {
    try {
      const { id } = req.params;

      const realtimeData = await RealtimeData.findOne({
        where: { turbineId: id },
        order: [['timestamp', 'DESC']]
      });

      if (!realtimeData) {
        return res.status(404).json({
          success: false,
          message: '沒有即時資料'
        });
      }

      res.json({
        success: true,
        data: realtimeData
      });
    } catch (error) {
      logger.error('取得即時資料失敗:', error);
      res.status(500).json({
        success: false,
        message: '取得即時資料失敗',
        error: error.message
      });
    }
  }

  // 取得風機狀態
  async getTurbineStatus(req, res) {
    try {
      const { id } = req.params;

      // 取得 OPC 連線狀態
      const connectionStatus = opcService.getConnectionStatus();
      const opcStatus = connectionStatus[id] || { isConnected: false };

      // 取得最新資料
      const realtimeData = await RealtimeData.findOne({
        where: { turbineId: id },
        order: [['timestamp', 'DESC']]
      });

      res.json({
        success: true,
        data: {
          opcConnection: opcStatus,
          lastDataUpdate: realtimeData?.timestamp,
          hasRecentData: realtimeData && 
            (new Date() - new Date(realtimeData.timestamp)) < 300000 // 5分鐘內
        }
      });
    } catch (error) {
      logger.error('取得風機狀態失敗:', error);
      res.status(500).json({
        success: false,
        message: '取得風機狀態失敗',
        error: error.message
      });
    }
  }

  // 啟動風機
  async startTurbine(req, res) {
    try {
      const { id } = req.params;

      const turbine = await WindTurbine.findByPk(id);
      if (!turbine) {
        return res.status(404).json({
          success: false,
          message: '找不到指定的風機'
        });
      }

      await turbine.update({ status: 'active' });

      res.json({
        success: true,
        message: '風機啟動命令已發送'
      });
    } catch (error) {
      logger.error('啟動風機失敗:', error);
      res.status(500).json({
        success: false,
        message: '啟動風機失敗',
        error: error.message
      });
    }
  }

  // 停止風機
  async stopTurbine(req, res) {
    try {
      const { id } = req.params;

      const turbine = await WindTurbine.findByPk(id);
      if (!turbine) {
        return res.status(404).json({
          success: false,
          message: '找不到指定的風機'
        });
      }

      await turbine.update({ status: 'offline' });

      res.json({
        success: true,
        message: '風機停止命令已發送'
      });
    } catch (error) {
      logger.error('停止風機失敗:', error);
      res.status(500).json({
        success: false,
        message: '停止風機失敗',
        error: error.message
      });
    }
  }

  // 設定維護模式
  async setMaintenanceMode(req, res) {
    try {
      const { id } = req.params;
      const { maintenance } = req.body;

      const turbine = await WindTurbine.findByPk(id);
      if (!turbine) {
        return res.status(404).json({
          success: false,
          message: '找不到指定的風機'
        });
      }

      await turbine.update({ 
        status: maintenance ? 'maintenance' : 'active' 
      });

      res.json({
        success: true,
        message: `風機${maintenance ? '進入' : '退出'}維護模式`
      });
    } catch (error) {
      logger.error('設定維護模式失敗:', error);
      res.status(500).json({
        success: false,
        message: '設定維護模式失敗',
        error: error.message
      });
    }
  }
}

module.exports = new TurbineController();

// src/routes/data.js - 資料查詢路由
const express = require('express');
const router = express.Router();
const dataController = require('../controllers/dataController');
const { authenticateToken } = require('../middleware/auth');

router.use(authenticateToken);

// 歷史資料查詢
router.get('/history', dataController.getHistoricalData);
router.get('/history/:turbineId', dataController.getTurbineHistoricalData);

// 統計資料
router.get('/statistics', dataController.getStatistics);
router.get('/statistics/:turbineId', dataController.getTurbineStatistics);

// 資料匯出
router.get('/export/csv', dataController.exportCSV);
router.get('/export/excel', dataController.exportExcel);

module.exports = router;

// src/controllers/dataController.js - 資料控制器
const { HistoricalData, WindTurbine } = require('../models');
const { Op } = require('sequelize');
const createCsvWriter = require('csv-writer').createObjectCsvWriter;
const path = require('path');
const fs = require('fs');
const logger = require('../utils/logger');

class DataController {
  // 取得歷史資料
  async getHistoricalData(req, res) {
    try {
      const {
        startDate,
        endDate,
        turbineIds,
        interval = '1h',
        limit = 1000,
        offset = 0
      } = req.query;

      const whereClause = {};
      
      // 時間範圍篩選
      if (startDate || endDate) {
        whereClause.timestamp = {};
        if (startDate) whereClause.timestamp[Op.gte] = new Date(startDate);
        if (endDate) whereClause.timestamp[Op.lte] = new Date(endDate);
      }

      // 風機篩選
      if (turbineIds) {
        const ids = Array.isArray(turbineIds) ? turbineIds : [turbineIds];
        whereClause.turbineId = { [Op.in]: ids };
      }

      const data = await HistoricalData.findAndCountAll({
        where: whereClause,
        include: [{
          model: WindTurbine,
          attributes: ['name', 'model']
        }],
        order: [['timestamp', 'DESC']],
        limit: parseInt(limit),
        offset: parseInt(offset)
      });

      res.json({
        success: true,
        data: data.rows,
        total: data.count,
        pagination: {
          limit: parseInt(limit),
          offset: parseInt(offset),
          hasMore: data.count > (parseInt(offset) + parseInt(limit))
        }
      });
    } catch (error) {
      logger.error('取得歷史資料失敗:', error);
      res.status(500).json({
        success: false,
        message: '取得歷史資料失敗',
        error: error.message
      });
    }
  }

  // 取得統計資料
  async getStatistics(req, res) {
    try {
      const { startDate, endDate, turbineIds } = req.query;
      
      const whereClause = {};
      if (startDate || endDate) {
        whereClause.timestamp = {};
        if (startDate) whereClause.timestamp[Op.gte] = new Date(startDate);
        if (endDate) whereClause.timestamp[Op.lte] = new Date(endDate);
      }

      if (turbineIds) {
        const ids = Array.isArray(turbineIds) ? turbineIds : [turbineIds];
        whereClause.turbineId = { [Op.in]: ids };
      }

      const [statistics] = await HistoricalData.findAll({
        attributes: [
          [HistoricalData.sequelize.fn('AVG', HistoricalData.sequelize.col('powerOutput')), 'avgPower'],
          [HistoricalData.sequelize.fn('MAX', HistoricalData.sequelize.col('powerOutput')), 'maxPower'],
          [HistoricalData.sequelize.fn('MIN', HistoricalData.sequelize.col('powerOutput')), 'minPower'],
          [HistoricalData.sequelize.fn('AVG', HistoricalData.sequelize.col('windSpeed')), 'avgWindSpeed'],
          [HistoricalData.sequelize.fn('MAX', HistoricalData.sequelize.col('windSpeed')), 'maxWindSpeed'],
          [HistoricalData.sequelize.fn('COUNT', HistoricalData.sequelize.col('id')), 'totalRecords']
        ],
        where: whereClause,
        raw: true
      });

      res.json({
        success: true,
        data: statistics
      });
    } catch (error) {
      logger.error('取得統計資料失敗:', error);
      res.status(500).json({
        success: false,
        message: '取得統計資料失敗',
        error: error.message
      });
    }
  }

  // 匯出 CSV
  async exportCSV(req, res) {
    try {
      const { startDate, endDate, turbineIds } = req.query;
      
      const whereClause = {};
      if (startDate || endDate) {
        whereClause.timestamp = {};
        if (startDate) whereClause.timestamp[Op.gte] = new Date(startDate);
        if (endDate) whereClause.timestamp[Op.lte] = new Date(endDate);
      }

      if (turbineIds) {
        const ids = Array.isArray(turbineIds) ? turbineIds : [turbineIds];
        whereClause.turbineId = { [Op.in]: ids };
      }

      const data = await HistoricalData.findAll({
        where: whereClause,
        include: [{
          model: WindTurbine,
          attributes: ['name']
        }],
        order: [['timestamp', 'ASC']],
        limit: 10000 // 限制匯出筆數
      });

      // 產生 CSV 檔案
      const fileName = `wind_farm_data_${Date.now()}.csv`;
      const filePath = path.join(__dirname, '../../exports', fileName);

      // 確保目錄存在
      const exportDir = path.dirname(filePath);
      if (!fs.existsSync(exportDir)) {
        fs.mkdirSync(exportDir, { recursive: true });
      }

      const csvWriter = createCsvWriter({
        path: filePath,
        header: [
          { id: 'timestamp', title: '時間戳記' },
          { id: 'turbineName', title: '風機名稱' },
          { id: 'windSpeed', title: '風速 (m/s)' },
          { id: 'windDirection', title: '風向 (度)' },
          { id: 'powerOutput', title: '發電量 (kW)' },
          { id: 'rotorRpm', title: '轉子轉速 (RPM)' },
          { id: 'nacelleTemperature', title: '機艙溫度 (°C)' },
          { id: 'operatingStatus', title: '運行狀態' }
        ]
      });

      const csvData = data.map(record => ({
        timestamp: record.timestamp,
        turbineName: record.WindTurbine?.name || '',
        windSpeed: record.windSpeed,
        windDirection: record.windDirection,
        powerOutput: record.powerOutput,
        rotorRpm: record.rotorRpm,