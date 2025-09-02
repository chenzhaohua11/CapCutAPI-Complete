from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "message": "CapCut API Server",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

if __name__ == '__main__':
    print("启动简化版CapCut API服务器...")
    app.run(host='0.0.0.0', port=5000, debug=True)