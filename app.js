const { spawn } = require("child_process");
const fs = require("fs");
const express = require("express");
const path = require("path");
const WebSocket = require("ws");

const app = express();
const PORT = 3010;
const LOG_FILE = "script_log.txt";
const PY_SCRIPT = "main.py"; 
const wss = new WebSocket.Server({ port: 3011 });

// WebSocket 连接池
wss.on("connection", (ws) => {
  console.log("WebSocket 客户端已连接");
});

// 创建初始日志文件
if (!fs.existsSync(LOG_FILE)) {
  fs.writeFileSync(LOG_FILE, "");
}

let dailyRunCounter = 0; // 每天重置一次的计数器
let nextRunTime = getNextRunTime(); // 每天的随机时间计数器

// 计算北京时间的 00:00 时间
function getNextMidnightBeijingTime() {
  const now = new Date();
  const beijingOffset = 8 * 60; // 北京时间比 UTC 时间快 8 小时
  const localOffset = now.getTimezoneOffset(); // 获取当前时区与 UTC 的偏移

  // 计算当前时间的 UTC 时间
  const utcNow = new Date(now.getTime() + (localOffset + beijingOffset) * 60000);
  
  // 设置为当天 00:00（UTC时间）
  const nextMidnightUtc = new Date(utcNow);
  nextMidnightUtc.setHours(0, 0, 0, 0);

  // 将 UTC 时间转回北京时间
  const nextMidnightBeijing = new Date(nextMidnightUtc.getTime() - beijingOffset * 60000);
  return nextMidnightBeijing;
}

// 计算随机的运行时间（在北京时间 00:00 之后的随机时间）
function getNextRunTime() {
  const nextMidnight = getNextMidnightBeijingTime();
  
  // 生成 0 - 24 小时内的随机偏移
  const randomOffset = Math.floor(Math.random() * 24 * 60 * 60 * 1000); // 随机偏移时间（毫秒）
  return new Date(nextMidnight.getTime() + randomOffset);
}

// 运行 Python 脚本并实时推送日志
function runPythonScript() {
  if (dailyRunCounter >= 1) {
    console.log("今天的脚本已经运行过了，等待明天重置计数器。");
    return;
  }

  const timestamp = new Date().toISOString();
  const logEntry = `\n\n=== 运行于: ${timestamp} ===\n`;

  fs.appendFileSync(LOG_FILE, logEntry);
  broadcastLog(`\n【脚本启动】时间：${timestamp}`);

  const process = spawn("python", [PY_SCRIPT]);

  process.stdout.on("data", (data) => {
    const output = data.toString();
    fs.appendFileSync(LOG_FILE, output);
    broadcastLog(output);
  });

  process.stderr.on("data", (data) => {
    const error = ` ${data.toString()}`;
    fs.appendFileSync(LOG_FILE, error);
    broadcastLog(error);
  });

  process.on("close", (code) => {
    const message = `脚本结束，退出码: ${code}\n`;
    fs.appendFileSync(LOG_FILE, message);
    broadcastLog(message);

    dailyRunCounter += 1; // 增加计数器
    scheduleNextRun();
  });
}

// 安排下次执行
function scheduleNextRun() {
  const nextRunTime = getNextRunTime();
  const delay = nextRunTime - new Date();

  if (delay <= 0) {
    // 如果当前时间已经超过了随机时间，重新计算下次运行时间
    nextRunTime = getNextRunTime();
    dailyRunCounter = 0; // 重置计数器
    scheduleNextRun();
  } else {
    console.log(`下次执行时间：${nextRunTime.toISOString()}（约 ${Math.floor(delay / 1000 / 60)} 分钟后）`);
    broadcastLog(`\n【下次执行时间】${nextRunTime.toISOString()}（约 ${Math.floor(delay / 1000 / 60)} 分钟后）`);
    setTimeout(runPythonScript, delay);
  }
}

// WebSocket 推送日志
function broadcastLog(message) {
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(message);
    }
  });
}

// Web 服务器显示日志
app.get("/", (req, res) => {
  fs.readFile(LOG_FILE, "utf8", (err, data) => {
    if (err) {
      res.status(500).send("无法读取日志文件");
      return;
    }

    // 默认显示最近的日志
    const recentLogs = data.split('\n').slice(-20).join('\n'); // 只显示最近的 20 行日志

    res.send(`
      <html>
        <head>
          <title>脚本运行日志</title>
          <meta http-equiv="refresh" content="10">
          <script>
            const ws = new WebSocket("ws://localhost:3011");
            ws.onmessage = (event) => {
              const logContainer = document.getElementById("log");
              logContainer.innerHTML += event.data.replace(/\\n/g, "<br>") + "<br>";
            };
          </script>
          <style>
            body { font-family: monospace; white-space: pre-wrap; padding: 20px; }
            .timestamp { color: #666; }
            .error { color: red; }
          </style>
        </head>
        <body>
          <h1>脚本运行日志</h1>
          <div id="log">${recentLogs.replace(/\n/g, "<br>")}</div>
        </body>
      </html>
    `);
  });
});

// 启动时立即运行一次
runPythonScript();

// 启动 Web 服务器
app.listen(PORT, () => {
  console.log(`Web 服务器运行在 http://localhost:${PORT}`);
});