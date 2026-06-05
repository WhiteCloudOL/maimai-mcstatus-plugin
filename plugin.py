"""Minecraft 服务器状态查询插件

查询 Minecraft 服务器状态，支持 MOTD、在线人数、延迟等，并生成精美的卡片图片。
"""
import os
from pathlib import Path
from typing import Any

from maibot_sdk import Command, Field, MaiBotPlugin, PluginConfigBase

from .core.command_func import CommandFunc
from .core.data_manager import DataManager


class PluginSectionConfig(PluginConfigBase):
    """插件基础配置。"""

    __ui_label__ = "插件基础配置"
    __ui_icon__ = "package"
    __ui_order__ = 0

    enabled: bool = Field(default=True, description="是否启用插件")
    config_version: str = Field(default="1.0.0", description="配置版本")


class DrawConfig(PluginConfigBase):
    """绘图配置。"""

    __ui_label__ = "绘图"
    __ui_icon__ = "palette"
    __ui_order__ = 1

    font: str = Field(default="cute_font.ttf", description="绘图字体文件名（放在 assets/ 目录下）")
    bg: str = Field(default="bg.jpg", description="绘图背景文件名（放在 assets/ 目录下）")
    max_temp: int = Field(default=5, description="最大缓存图片数量")


class DataConfig(PluginConfigBase):
    """数据配置。"""

    __ui_label__ = "数据"
    __ui_icon__ = "database"
    __ui_order__ = 2

    divide_data: bool = Field(default=False, description="是否启用分群存储")


class MCStatusPluginConfig(PluginConfigBase):
    """Minecraft 状态查询插件配置。"""

    plugin: PluginSectionConfig = Field(default_factory=PluginSectionConfig)
    draw: DrawConfig = Field(default_factory=DrawConfig)
    data: DataConfig = Field(default_factory=DataConfig)


class MCStatusPlugin(MaiBotPlugin):
    """Minecraft 服务器状态查询插件"""

    config_model = MCStatusPluginConfig

    async def on_load(self) -> None:
        """处理插件加载。"""
        # 数据目录
        self._data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(self._data_dir, exist_ok=True)

        # 初始化数据管理器
        self._datamanager = DataManager(data_dir=Path(self._data_dir))
        self._datamanager.load_config()

        # 初始化命令处理器
        self._command_func = CommandFunc(
            datamanager=self._datamanager,
            plugin_data_dir=self._data_dir,
            font_name=self.config.draw.font,
            bg_name=self.config.draw.bg,
            max_temp=self.config.draw.max_temp,
            divide_data=self.config.data.divide_data,
        )

        self.ctx.logger.info("MCStatus 插件已加载")

    async def on_unload(self) -> None:
        """处理插件卸载。"""
        if self._datamanager.save_config():
            self.ctx.logger.info("数据保存成功，已卸载 MCStatus 插件！")

    async def on_config_update(self, scope: str, config_data: dict[str, object], version: str) -> None:
        """处理配置热重载事件。"""
        # 更新命令处理器的配置
        self._command_func.font_name = self.config.draw.font
        self._command_func.bg_name = self.config.draw.bg
        self._command_func.max_temp = self.config.draw.max_temp
        self._command_func.divide_data = self.config.data.divide_data
        self.ctx.logger.info("MCStatus 插件配置已更新")

    @Command(
        "mcstatus",
        description="Minecraft 服务器状态查询",
        pattern=r"^/(?:mcstatus|mcs)\s*(?P<args>.*)",
    )
    async def handle_mcstatus(self, stream_id: str = "", **kwargs: Any) -> tuple[bool, str, int]:
        """MCStatus 主命令处理"""
        # 从 matched_groups 提取参数
        matched_groups = kwargs.get("matched_groups", {})
        if not isinstance(matched_groups, dict):
            matched_groups = {}

        raw_args = str(matched_groups.get("args") or "").strip()

        # fallback: 从 kwargs["text"] 直接解析
        if not raw_args:
            raw_text = str(kwargs.get("text") or "").strip()
            import re as _re
            _m = _re.match(r"^/(?:mcstatus|mcs)\s*(?P<args>.*)", raw_text, _re.DOTALL)
            if _m:
                raw_args = _m.group("args").strip()

        # 解析子命令和参数
        parts = raw_args.split(None, 2) if raw_args else []
        subcommand = parts[0] if len(parts) > 0 else ""
        arg1 = parts[1] if len(parts) > 1 else ""
        arg2 = parts[2] if len(parts) > 2 else ""

        # 获取 user_id 和 group_id
        user_id = str(kwargs.get("user_id", ""))
        group_id = str(kwargs.get("group_id", ""))

        result_tuple: tuple[bool, str] = (False, "")

        if subcommand == "":
            result_tuple = (False, "❌缺少参数，请输入/mcstatus help查询用法")
        elif subcommand == "motd":
            result_tuple = await self._command_func._handle_motd(server_addr=arg1, group_id=group_id, user_id=user_id)
        elif subcommand == "add":
            result_tuple = await self._command_func._handle_add(server_name=arg1, server_addr=arg2, group_id=group_id, user_id=user_id)
        elif subcommand == "players":
            result_tuple = await self._command_func._handle_players(server_addr=arg1, group_id=group_id, user_id=user_id)
        elif subcommand == "del":
            result_tuple = await self._command_func._handle_del(server_name=arg1, group_id=group_id, user_id=user_id)
        elif subcommand == "look":
            result_tuple = await self._command_func._handle_look(server_name=arg1, group_id=group_id, user_id=user_id)
        elif subcommand == "set":
            result_tuple = await self._command_func._handle_set(server_name=arg1, server_addr=arg2, group_id=group_id, user_id=user_id)
        elif subcommand == "list":
            result_tuple = await self._command_func._handle_list(group_id=group_id, user_id=user_id)
        elif subcommand == "clear":
            result_tuple = await self._command_func._handle_clear(group_id=group_id, user_id=user_id)
        elif subcommand == "help":
            result_tuple = await self._command_func._handle_help()
        else:
            result_tuple = (False, "❌无相关指令，请输入/mcstatus help查询用法")

        # 根据返回的 tuple 判断发送图片还是文本
        is_image, data = result_tuple
        if is_image:
            await self.ctx.send.image(data, stream_id)
        else:
            await self.ctx.send.text(data, stream_id)

        return True, data, 2


def create_plugin() -> MCStatusPlugin:
    """创建 MCStatus 插件实例。"""
    return MCStatusPlugin()
