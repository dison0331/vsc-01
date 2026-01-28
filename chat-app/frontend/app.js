/**
 * 在线聊天室前端应用
 * 使用Socket.IO实现实时通信
 */

class ChatApp {
    constructor() {
        this.socket = null;
        this.username = '';
        this.currentRoom = 'general';
        this.typingTimeout = null;

        this.initElements();
        this.bindEvents();
    }

    initElements() {
        // 登录界面元素
        this.loginScreen = document.getElementById('login-screen');
        this.chatScreen = document.getElementById('chat-screen');
        this.usernameInput = document.getElementById('username');
        this.joinBtn = document.getElementById('join-btn');

        // 聊天界面元素
        this.currentUsername = document.getElementById('current-username');
        this.currentRoomName = document.getElementById('current-room-name');
        this.messagesContainer = document.getElementById('messages-container');
        this.messageInput = document.getElementById('message-input');
        this.messageForm = document.getElementById('message-form');
        this.leaveBtn = document.getElementById('leave-btn');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.onlineUsersList = document.getElementById('online-users-list');
        this.roomUsersCount = document.getElementById('room-users-count');
    }

    bindEvents() {
        // 登录事件
        this.joinBtn.addEventListener('click', () => this.joinChat());
        this.usernameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.joinChat();
        });

        // 发送消息事件
        this.messageForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        // 离开聊天室
        this.leaveBtn.addEventListener('click', () => this.leaveChat());

        // 输入状态检测
        this.messageInput.addEventListener('input', () => this.handleTyping());
    }

    initSocket() {
        // 连接到WebSocket服务器
        this.socket = io('http://localhost:5000', {
            transports: ['websocket', 'polling']
        });

        // 连接成功
        this.socket.on('connect', () => {
            console.log('已连接到服务器');
        });

        // 断开连接
        this.socket.on('disconnect', () => {
            console.log('已断开连接');
            this.showSystemMessage('已断开与服务器的连接');
        });

        // 新消息
        this.socket.on('new_message', (data) => {
            this.displayMessage(data);
        });

        // 用户加入
        this.socket.on('user_joined', (data) => {
            this.showSystemMessage(`${data.username} 加入了聊天室`);
            this.updateOnlineUsers();
        });

        // 用户离开
        this.socket.on('user_left', (data) => {
            this.showSystemMessage(`${data.username} 离开了聊天室`);
            this.updateOnlineUsers();
        });

        // 在线用户列表
        this.socket.on('online_users', (data) => {
            this.displayOnlineUsers(data.users);
        });

        // 系统消息
        this.socket.on('system_message', (data) => {
            this.showSystemMessage(data.message);
        });

        // 用户输入状态
        this.socket.on('user_typing', (data) => {
            this.displayTypingIndicator(data);
        });
    }

    joinChat() {
        const username = this.usernameInput.value.trim();

        if (!username) {
            alert('请输入用户名');
            return;
        }

        this.username = username;
        this.currentUsername.textContent = username;

        // 初始化Socket连接
        this.initSocket();

        // 切换到聊天界面
        this.loginScreen.classList.add('hidden');
        this.chatScreen.classList.remove('hidden');

        // 加入聊天室
        this.socket.emit('join', {
            username: username,
            room: this.currentRoom
        });

        // 加载历史消息
        this.loadHistoryMessages();

        // 聚焦到消息输入框
        this.messageInput.focus();
    }

    leaveChat() {
        if (this.socket) {
            this.socket.emit('leave_room', {
                room: this.currentRoom
            });
            this.socket.disconnect();
        }

        // 切换回登录界面
        this.chatScreen.classList.add('hidden');
        this.loginScreen.classList.remove('hidden');

        // 清空消息
        this.messagesContainer.innerHTML = '';
        this.onlineUsersList.innerHTML = '';

        // 重置输入
        this.usernameInput.value = '';
    }

    sendMessage() {
        const message = this.messageInput.value.trim();

        if (!message) return;

        // 发送消息到服务器
        this.socket.emit('send_message', {
            message: message,
            room: this.currentRoom
        });

        // 清空输入框
        this.messageInput.value = '';
    }

    displayMessage(data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${data.user_id === this.socket?.id ? 'self' : ''}`;

        const avatar = data.user_id === this.socket?.id ? '' : `
            <div class="message-avatar">
                ${data.username.charAt(0).toUpperCase()}
            </div>
        `;

        messageDiv.innerHTML = `
            ${avatar}
            <div class="message-content">
                <div class="message-header">
                    <span class="message-username">${data.username}</span>
                    <span class="message-time">${data.timestamp}</span>
                </div>
                <div class="message-body">${this.escapeHtml(data.message)}</div>
            </div>
        `;

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showSystemMessage(message) {
        const systemDiv = document.createElement('div');
        systemDiv.className = 'system-message';
        systemDiv.textContent = message;
        this.messagesContainer.appendChild(systemDiv);
        this.scrollToBottom();
    }

    displayOnlineUsers(users) {
        this.onlineUsersList.innerHTML = '';
        this.roomUsersCount.textContent = users.length;

        users.forEach(user => {
            const userDiv = document.createElement('div');
            userDiv.className = 'user-item';
            userDiv.innerHTML = `
                <div class="user-avatar">
                    ${user.username.charAt(0).toUpperCase()}
                </div>
                <div class="user-name">${user.username}</div>
            `;
            this.onlineUsersList.appendChild(userDiv);
        });
    }

    updateOnlineUsers() {
        // 获取最新的在线用户列表
        fetch('http://localhost:5000/api/users/online')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.displayOnlineUsers(data.users);
                }
            })
            .catch(error => console.error('获取在线用户失败:', error));
    }

    handleTyping() {
        // 发送输入状态
        this.socket.emit('typing', {
            is_typing: true,
            room: this.currentRoom
        });

        // 清除之前的定时器
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
        }

        // 3秒后发送停止输入状态
        this.typingTimeout = setTimeout(() => {
            this.socket.emit('typing', {
                is_typing: false,
                room: this.currentRoom
            });
        }, 3000);
    }

    displayTypingIndicator(data) {
        if (data.is_typing) {
            this.typingIndicator.textContent = `${data.username} 正在输入...`;
        } else {
            this.typingIndicator.textContent = '';
        }
    }

    loadHistoryMessages() {
        fetch('http://localhost:5000/api/messages?limit=50')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    data.messages.forEach(msg => this.displayMessage(msg));
                }
            })
            .catch(error => console.error('加载历史消息失败:', error));
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
