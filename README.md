# maimai-mcstatus-plugin

Minecraft 服务器状态查询插件，支持查询 MOTD、在线人数、延迟等，并生成精美的卡片图片。

## 功能

- `/mcstatus motd <地址>` — 查询服务器状态/延迟
- `/mcstatus players <地址>` — 获取在线玩家列表
- `/mcstatus add <名称> <地址>` — 添加常用服务器
- `/mcstatus del <名称>` — 删除已存服务器
- `/mcstatus look <名称>` — 查询已存服务器
- `/mcstatus list` — 显示服务器列表
- `/mcstatus clear` — 清空所有服务器
- `/mcstatus help` — 获取帮助信息

## 配置

在 `config.toml` 中可配置：

- `font` — 绘图字体文件名（放在 assets/ 目录下）
- `bg` — 绘图背景文件名（放在 assets/ 目录下）
- `max_temp` — 最大缓存图片数量
- `divide_data` — 是否启用分群存储

## 依赖

- mcstatus >= 12.0.0
- pillow
