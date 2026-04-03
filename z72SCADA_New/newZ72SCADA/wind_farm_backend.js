// package.json
{
  "name": "wind-farm-monitoring-backend",
  "version": "1.0.0",
  "description": "Wind Farm Monitoring System Backend",
  "main": "src/app.js",
  "scripts": {
    "start": "node src/app.js",
    "dev": "nodemon src/app.js",
    "test": "jest",
    "migrate": "npx sequelize-cli db:migrate",
    "seed": "npx sequelize-cli db:seed:all"
  },
  "dependencies": {
    "express": "^4.18.2",
    "express-rate-limit": "^6.7.0",
    "helmet": "^6.1.5",
    "cors": "^2.8.5",
    "morgan": "^1.10.0",
    "dotenv": "^16.0.3",
    "jsonwebtoken": "^9.0.0",
    "bcryptjs": "^2.4.3",
    "sequelize": "^6.31.1",
    "pg": "^8.11.0",
    "redis": "^4.6.6",
    "socket.io": "^4.6.2",
    "node-opcda": "^1.0.0",
    "winston": "^3.8.2",
    "compression": "^1.7.4",
    "express-validator": "^6.15.0",
    "multer": "^1.4.5",
    "csv-writer": "^1.6.0",
    "node-cron": "^3.0.2"
  },
  "devDependencies": {
    "nodemon": "^2.0.22",
    "jest": "^29.5.0",
    "supertest": "^6.3.3"
  }
}

// src/app.js - 主應用程式
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const { sequelize } = require('./models');
const routes = require('./routes');
const { errorHandler } = require('./middleware/errorHandler');
const { initializeOPCConnections } = require('./services/opcService');
const logger = require('./utils/logger');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: process.env.FRONTEND_URL || "http://localhost:3000",
    methods: ["GET", "POST"]
  }
});

// 中介軟體設定
app.use(helmet());
app.use(compression());
app.use(morgan('combined', { stream: { write: message => logger.info(message.trim()) } }));
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 速率限制
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分鐘
  max: 1000 // 限制每個IP 1000次請求
});
app.use('/api/', limiter);

// 路由設定
app.use('/api', routes);

// 錯誤處理
app.use(errorHandler);

// Socket.IO 設定
global.io = io;
io.on('connection', (socket) => {
  logger.info(`客戶端連線: ${socket.id}`);
  
  socket.on('subscribe_turbine', (turbineId) => {
    socket.join(`turbine_${turbineId}`);
    logger.info(`客戶端 ${socket.id} 訂閱風機 ${turbineId}`);
  });

  socket.on('disconnect', () => {
    logger.info(`客戶端斷線: ${socket.id}`);
  });
});

// 資料庫連線和伺服器啟動
const PORT = process.env.PORT || 3001;

async function startServer() {
  try {
    // 資料庫連線測試
    await sequelize.authenticate();
    logger.info('資料庫連線成功');

    // 同步資料庫模型
    await sequelize.sync({ alter: true });
    logger.info('資料庫同步完成');

    // 初始化 OPC 連線
    await initializeOPCConnections();
    logger.info('OPC 連線初始化完成');

    // 啟動伺服器
    server.listen(PORT, () => {
      logger.info(`伺服器運行於端口 ${PORT}`);
    });
  } catch (error) {
    logger.error('伺服器啟動失敗:', error);
    process.exit(1);
  }
}

startServer();

// 優雅關閉
process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

function gracefulShutdown() {
  logger.info('正在關閉伺服器...');
  server.close(() => {
    logger.info('伺服器已關閉');
    sequelize.close();
    process.exit(0);
  });
}

// src/config/database.js - 資料庫設定
module.exports = {
  development: {
    username: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'password',
    database: process.env.DB_NAME || 'wind_farm_monitoring',
    host: process.env.DB_HOST || 'localhost',
    port: process.env.DB_PORT || 5432,
    dialect: 'postgres',
    logging: false,
    pool: {
      max: 20,
      min: 5,
      acquire: 60000,
      idle: 10000
    }
  },
  production: {
    username: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
    host: process.env.DB_HOST,
    port: process.env.DB_PORT,
    dialect: 'postgres',
    logging: false,
    pool: {
      max: 20,
      min: 5,
      acquire: 60000,
      idle: 10000
    }
  }
};

// src/models/index.js - 資料庫模型索引
const { Sequelize } = require('sequelize');
const config = require('../config/database')[process.env.NODE_ENV || 'development'];

const sequelize = new Sequelize(config.database, config.username, config.password, config);

// 模型導入
const WindTurbine = require('./WindTurbine')(sequelize, Sequelize.DataTypes);
const RealtimeData = require('./RealtimeData')(sequelize, Sequelize.DataTypes);
const HistoricalData = require('./HistoricalData')(sequelize, Sequelize.DataTypes);
const Alert = require('./Alert')(sequelize, Sequelize.DataTypes);
const User = require('./User')(sequelize, Sequelize.DataTypes);

// 建立關聯
WindTurbine.hasMany(RealtimeData, { foreignKey: 'turbineId' });
WindTurbine.hasMany(HistoricalData, { foreignKey: 'turbineId' });
WindTurbine.hasMany(Alert, { foreignKey: 'turbineId' });

RealtimeData.belongsTo(WindTurbine, { foreignKey: 'turbineId' });
HistoricalData.belongsTo(WindTurbine, { foreignKey: 'turbineId' });
Alert.belongsTo(WindTurbine, { foreignKey: 'turbineId' });

module.exports = {
  sequelize,
  WindTurbine,
  RealtimeData,
  HistoricalData,
  Alert,
  User
};

// src/models/WindTurbine.js - 風力機模型
module.exports = (sequelize, DataTypes) => {
  const WindTurbine = sequelize.define('WindTurbine', {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true
    },
    name: {
      type: DataTypes.STRING(100),
      allowNull: false,
      unique: true
    },
    model: {
      type: DataTypes.STRING(100),
      allowNull: true
    },
    capacity: {
      type: DataTypes.DECIMAL(8, 2), // kW
      allowNull: true
    },
    latitude: {
      type: DataTypes.DECIMAL(10, 8),
      allowNull: true
    },
    longitude: {
      type: DataTypes.DECIMAL(11, 8),
      allowNull: true
    },
    installationDate: {
      type: DataTypes.DATE,
      allowNull: true
    },
    opcConfig: {
      type: DataTypes.JSONB, // OPC 設定參數
      allowNull: true
    },
    status: {
      type: DataTypes.ENUM('active', 'maintenance', 'fault', 'offline'),
      defaultValue: 'active'
    },
    isActive: {
      type: DataTypes.BOOLEAN,
      defaultValue: true
    }
  }, {
    tableName: 'wind_turbines',
    timestamps: true
  });

  return WindTurbine;
};

// src/models/RealtimeData.js - 即時資料模型
module.exports = (sequelize, DataTypes) => {
  const RealtimeData = sequelize.define('RealtimeData', {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true
    },
    turbineId: {
      type: DataTypes.INTEGER,
      allowNull: false,
      references: {
        model: 'wind_turbines',
        key: 'id'
      }
    },
    timestamp: {
      type: DataTypes.DATE,
      defaultValue: DataTypes.NOW
    },
    // 風況參數
    windSpeed: {
      type: DataTypes.DECIMAL(5, 2), // m/s
      allowNull: true
    },
    windDirection: {
      type: DataTypes.INTEGER, // 度
      allowNull: true
    },
    // 發電參數
    powerOutput: {
      type: DataTypes.DECIMAL(8, 2), // kW
      allowNull: true
    },
    voltage: {
      type: DataTypes.DECIMAL(8, 2), // V
      allowNull: true
    },
    current: {
      type: DataTypes.DECIMAL(8, 2), // A
      allowNull: true
    },
    frequency: {
      type: DataTypes.DECIMAL(5, 2), // Hz
      allowNull: true
    },
    // 機械參數
    rotorRpm: {
      type: DataTypes.DECIMAL(6, 2), // RPM
      allowNull: true
    },
    generatorRpm: {
      type: DataTypes.DECIMAL(8, 2), // RPM
      allowNull: true
    },
    pitchAngle: {
      type: DataTypes.DECIMAL(5, 2), // 度
      allowNull: true
    },
    yawAngle: {
      type: DataTypes.DECIMAL(5, 2), // 度
      allowNull: true
    },
    // 溫度參數
    nacelleTemperature: {
      type: DataTypes.DECIMAL(4, 1), // °C
      allowNull: true
    },
    gearboxTemperature: {
      type: DataTypes.DECIMAL(4, 1), // °C
      allowNull: true
    },
    generatorTemperature: {
      type: DataTypes.DECIMAL(4, 1), // °C
      allowNull: true
    },
    bearingTemperature: {
      type: DataTypes.DECIMAL(4, 1), // °C
      allowNull: true
    },
    // 振動參數
    vibrationX: {
      type: DataTypes.DECIMAL(6, 3), // mm/s
      allowNull: true
    },
    vibrationY: {
      type: DataTypes.DECIMAL(6, 3), // mm/s
      allowNull: true
    },
    vibrationZ: {
      type: DataTypes.DECIMAL(6, 3), // mm/s
      allowNull: true
    },
    // 狀態參數
    operatingStatus: {
      type: DataTypes.INTEGER, // 運行狀態碼
      allowNull: true
    },
    faultCode: {
      type: DataTypes.STRING(50), // 故障碼
      allowNull: true
    },
    maintenanceStatus: {
      type: DataTypes.BOOLEAN,
      defaultValue: false
    }
  }, {
    tableName: 'realtime_data',
    timestamps: false,
    indexes: [
      {
        fields: ['turbineId', 'timestamp']
      },
      {
        fields: ['timestamp']
      }
    ]
  });

  return RealtimeData;
};