# 在线聊天程序

基于Python的实时在线聊天程序，采用前后端分离架构，使用程序级API。

## 项目结构

```
chat-app/
├── backend/
│   └── server.py          # 后端服务器（Flask + WebSocket）
├── frontend/
│   ├── index.html         # 前端页面
│   ├── style.css          # 样式文件
│   └── app.js            # 前端逻辑
├── requirements.txt       # Python依赖
└── README.md             # 项目说明
```

## 技术栈

### 后端
- **Flask**: Web框架
- **Flask-SocketIO**: WebSocket支持
- **Flask-CORS**: 跨域支持
- **Python**: 编程语言

### 前端
- **HTML5**: 页面结构
- **CSS3**: 样式设计
- **JavaScript**: 交互逻辑
- **Socket.IO Client**: WebSocket客户端

## 功能特性

1. **实时消息传输**: 使用WebSocket实现双向实时通信
2. **多用户支持**: 支持多用户同时在线聊天
3. **房间系统**: 支持多聊天室（目前实现通用聊天室）
4. **在线状态**: 实时显示在线用户列表
5. **输入状态**: 显示用户正在输入的状态
6. **历史消息**: 自动加载历史聊天记录
7. **程序级API**: 提供完整的API接口供调用

## 程序级API

### 后端API类 `ChatAPI`

```python
class ChatAPI:
    @staticmethod
    def send_message(user_id, username, message, room='general')
    @staticmethod
    def get_online_users()
    @staticmethod
    def get_messages(limit=50)
    @staticmethod
    def get_room_info(room_name)
```

### RESTful API端点

- `GET /api/users/online` - 获取在线用户列表
- `GET /api/messages?limit=50` - 获取历史消息
- `GET /api/rooms/<room_name>` - 获取房间信息

### WebSocket事件

- `connect` - 客户端连接
- `disconnect` - 客户端断开
- `join` - 加入聊天室
- `send_message` - 发送消息
- `leave_room` - 离开房间
- `typing` - 输入状态

## 安装和运行

### 1. 安装依赖

```bash
cd chat-app
pip install -r requirements.txt
```

### 2. 启动后端服务器

```bash
cd backend
python server.py
```

服务器将在 `http://localhost:5000` 启动

### 3. 打开前端页面

在浏览器中打开 `frontend/index.html` 文件

或者使用简单的HTTP服务器：

```bash
cd frontend
python -m http.server 8080
```

然后在浏览器中访问 `http://localhost:8080`

## 使用说明

1. 在登录界面输入用户名
2. 点击"加入聊天"按钮
3. 在消息输入框中输入消息并发送
4. 可以看到其他用户的实时消息
5. 左侧边栏显示在线用户列表

## 开发说明

### 扩展功能

1. **添加更多聊天室**: 修改前端和后端代码支持多个房间
2. **私有消息**: 实现用户之间的私聊功能
3. **消息持久化**: 使用数据库存储消息历史
4. **用户认证**: 添加登录注册系统
5. **文件传输**: 支持发送图片和文件
6. **表情包**: 添加表情包支持

### 修改配置

- 修改 `backend/server.py` 中的 `app.config['SECRET_KEY']`
- 修改 `frontend/app.js` 中的 `io('http://localhost:5000')` 地址

## 注意事项

1. 确保后端服务器正在运行
2. 前端需要通过HTTP服务器访问（直接打开文件可能有CORS问题）
3. 默认使用内存存储，重启服务器后消息会丢失
4. 生产环境建议使用数据库存储消息

## 许可证

MIT License
