"""
在线聊天程序后端服务器
使用Flask + Flask-SocketIO实现实时通信
"""

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from datetime import datetime
import threading
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app)

# 允许跨域
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 存储在线用户和消息
online_users = {}
messages = []
rooms = {}  # 房间信息

class ChatAPI:
    """聊天程序级API"""

    @staticmethod
    def send_message(user_id, username, message, room='general'):
        """发送消息到指定房间"""
        message_data = {
            'user_id': user_id,
            'username': username,
            'message': message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'room': room
        }
        messages.append(message_data)
        socketio.emit('new_message', message_data, room=room)
        return message_data

    @staticmethod
    def get_online_users():
        """获取在线用户列表"""
        return [{'user_id': uid, 'username': online_users[uid]} for uid in online_users]

    @staticmethod
    def get_messages(limit=50):
        """获取历史消息"""
        return messages[-limit:]

    @staticmethod
    def get_room_info(room_name):
        """获取房间信息"""
        return rooms.get(room_name, {'name': room_name, 'users': []})

# RESTful API 路由
@app.route('/api/users/online', methods=['GET'])
def get_online_users():
    """获取在线用户API"""
    return jsonify({'success': True, 'users': ChatAPI.get_online_users()})

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """获取历史消息API"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify({'success': True, 'messages': ChatAPI.get_messages(limit)})

@app.route('/api/rooms/<room_name>', methods=['GET'])
def get_room_info(room_name):
    """获取房间信息API"""
    return jsonify({'success': True, 'room': ChatAPI.get_room_info(room_name)})

# WebSocket 事件处理
@socketio.on('connect')
def handle_connect():
    """处理客户端连接"""
    print(f'客户端已连接: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开连接"""
    user_id = request.sid
    if user_id in online_users:
        username = online_users[user_id]
        del online_users[user_id]
        emit('user_left', {
            'user_id': user_id,
            'username': username
        }, broadcast=True)
        print(f'用户 {username} 已断开连接')

@socketio.on('join')
def handle_join(data):
    """处理用户加入聊天室"""
    user_id = request.sid
    username = data.get('username', f'User_{user_id[:8]}')
    room = data.get('room', 'general')

    # 存储用户信息
    online_users[user_id] = username

    # 加入房间
    join_room(room)

    # 更新房间用户列表
    if room not in rooms:
        rooms[room] = {'name': room, 'users': []}
    if user_id not in rooms[room]['users']:
        rooms[room]['users'].append(user_id)

    # 通知其他用户
    emit('user_joined', {
        'user_id': user_id,
        'username': username,
        'room': room
    }, room=room)

    # 发送欢迎消息
    emit('system_message', {
        'message': f'{username} 加入了聊天室',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }, room=room)

    # 向新用户发送当前在线用户列表
    emit('online_users', {'users': ChatAPI.get_online_users()}, room=user_id)

    print(f'用户 {username} 加入了房间 {room}')

@socketio.on('send_message')
def handle_message(data):
    """处理发送消息"""
    user_id = request.sid
    username = online_users.get(user_id, 'Anonymous')
    message = data.get('message', '')
    room = data.get('room', 'general')

    if message.strip():
        message_data = ChatAPI.send_message(user_id, username, message, room)
        print(f'{username} 在 {room} 发送消息: {message}')

@socketio.on('leave_room')
def handle_leave_room(data):
    """处理用户离开房间"""
    user_id = request.sid
    room = data.get('room', 'general')

    if user_id in online_users:
        username = online_users[user_id]
        leave_room(room)

        # 更新房间用户列表
        if room in rooms and user_id in rooms[room]['users']:
            rooms[room]['users'].remove(user_id)

        emit('user_left', {
            'user_id': user_id,
            'username': username,
            'room': room
        }, room=room)

        emit('system_message', {
            'message': f'{username} 离开了聊天室',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }, room=room)

        print(f'用户 {username} 离开了房间 {room}')

@socketio.on('typing')
def handle_typing(data):
    """处理用户输入状态"""
    user_id = request.sid
    username = online_users.get(user_id, 'Anonymous')
    is_typing = data.get('is_typing', False)
    room = data.get('room', 'general')

    emit('user_typing', {
        'user_id': user_id,
        'username': username,
        'is_typing': is_typing
    }, room=room, include_self=False)

if __name__ == '__main__':
    print('聊天服务器启动中...')
    print('服务器运行在 http://localhost:5000')
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
