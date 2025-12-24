K-Alert 股票监控系统文档

1. 项目概述
   K-Alert 是一款实时股票监控系统，用于追踪股票价格、计算技术指标（特指相对强弱指数 RSI），并在触发用户自定义策略时，通过电子邮件或电报发送自动通知。该系统由 Python FastAPI 后端和 Vue 3 前端构成。
2. 已实现功能
   核心功能
   实时监控：按可配置的时间间隔（默认 60 秒）获取股市数据。
   技术分析：自动计算被监控股票的相对强弱指数（RSI）。
   自定义策略：用户可为单只股票设置特定的 RSI 阈值（低值 / 高值）。
   警报系统：当市场条件满足设定策略时，触发通知发送。
   警报冷却机制：防止同一事件重复发送通知，避免消息轰炸。
   后端服务（backend/app/services）
   市场数据服务（market_data.py）：处理实时股票数据获取，集成 AkShare 数据接口。
   指标服务（indicator.py）：计算 RSI 等技术指标。
   扫描程序（scanner.py）：后台进程，遍历被监控股票并检查触发条件。
   信号引擎（signal.py）：判断当前数据是否符合用户策略标准。
   通知服务（notification.py）：通过已配置渠道（电报）管理警报发送。
   任务处理器（worker.py）：处理后台任务和队列项。
   交易时段控制（trading_hours.py）：确保仅在市场交易时段运行监控。
   前端界面（frontend/src/views）
   股票列表（StockList.vue）：仪表盘视图，用于查看被监控股票、添加新股票代码及删除现有股票。
   策略设置（StrategySettings.vue）：配置界面，用于设置各股票的 RSI 阈值（低值 / 高值）。
3. 项目结构
   k-alert/
   ├── backend/ # Python FastAPI 后端
   │ ├── app/
   │ │ ├── api/ # REST API 端点
   │ │ │ ├── stocks.py # 股票管理相关 API
   │ │ │ ├── strategies.py # 策略配置相关 API
   │ │ │ └── notifications.py # 通知设置相关 API
   │ │ ├── core/ # 核心基础设施
   │ │ │ ├── config.py # 应用配置
   │ │ │ ├── database.py # 数据库连接
   │ │ │ ├── queue.py # Redis/内存队列封装
   │ │ │ └── scheduler.py # 任务调度器
   │ │ └── services/ # 业务逻辑层（市场数据、指标计算等）
   │ ├── main.py # 应用入口文件
   │ └── requirements.txt # Python 依赖包列表
   │
   ├── frontend/ # Vue 3 前端
   │ ├── src/
   │ │ ├── api/ # API 客户端模块
   │ │ ├── views/ # 页面组件
   │ │ │ ├── StockList.vue
   │ │ │ ├── StrategySettings.vue
   │ │ │ └── NotificationSettings.vue
   │ │ └── router/ # Vue 路由配置
   │ └── package.json # Node.js 依赖包列表
   │
   ├── 开发计划.md # 原始开发计划
   └── README.md # 快速开始指南
4. API 端点汇总
   请求方法 端点路径 描述
   股票相关
   GET /api/stock/list 获取所有被监控股票的列表
   POST /api/stock/add 添加新股票至监控列表
   POST /api/stock/delete 从监控列表中移除股票
   策略相关
   GET /api/strategy/{code} 获取某只股票的策略配置
   POST /api/strategy/update 更新 RSI 阈值及相关设置
   通知相关
   GET /api/user/notify 获取当前通知配置
   POST /api/user/notify/update 更新电子邮件 / 电报配置信息
5. 安装与配置
   后端配置
   进入 backend/ 目录。
   创建虚拟环境并安装依赖：pip install -r requirements.txt。
   在 .env 文件中配置环境变量（数据库、Redis、SMTP、电报相关信息）。
   启动服务器：python -m uvicorn app.main:app --reload。
   前端配置
   进入 frontend/ 目录。
   安装依赖：npm install。
   启动开发服务器：npm run dev。
