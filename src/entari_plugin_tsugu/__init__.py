# entari-plugin-tsugu
# Tsugu BanGDream Bot Plugin for Entari Framework

__version__ = "0.1.6"

from arclet.entari import metadata, BasicConfModel, plugin_config
import json
from typing import List, Optional, Union
from arclet.entari import Entari, WS, load_plugin
import time
import arclet.letoderea as leto
from arclet.entari import MessageCreatedEvent, Session, MessageChain
from satori.element import Custom
from satori.exception import ServerException
from arclet.entari import MessageChain, At, Image
from dataclasses import field

from tsugu import cmd_generator

# 设置日志
import logging
logger = logging.getLogger(__name__)


class TsuguPluginConfig(BasicConfModel):
    qq_passive: bool = False  # passive mode for QQ platform
    prefix: List[str] = field(default_factory=lambda: ['/', ''])  # command prefix list
    platform: Optional[str] = None  # specify platform, None for auto-detection


metadata(
    name="entari_plugin_tsugu",
    author=[{"name": "kumoSleeping", "email": "zjr2992@outlook.com"}],
    version="0.1.7",
    description="Tsugu BanGDream Bot",
    config=TsuguPluginConfig,
)

# 获取配置实例
config = plugin_config(TsuguPluginConfig)

# 常量：QQ平台被动模式配置
QQ_PASSIVE = config.qq_passive
# 常量：命令前缀配置
COMMAND_PREFIX = config.prefix
# 常量：平台配置
PLATFORM = config.platform


def cmd_select(
        session: Session[MessageCreatedEvent],
        prefix: Union[str, List[str]] = '',
        ) -> Optional[str]:
    msg = session.event.message.message
    pure_text = ''.join(str(e) for e in msg if e.tag == 'text').strip()

    if prefix != ['']:
        prefix = prefix if isinstance(prefix, list) else [prefix]
        for p in prefix:
            if p == '' or pure_text.startswith(p):
                result = pure_text[len(p):].strip()
                return result
    else:
        return pure_text

    return ''


@leto.on(MessageCreatedEvent)
async def on_message_created(session: Session[MessageCreatedEvent]):
    async def func_send(result):
        async def _send(mc: MessageChain):
            if QQ_PASSIVE:
                # 添加 qq:passive 自定义元素到消息链中
                mc.append(Custom("qq:passive", {"id": session.event.message.id, "seq": int(time.time())}))
            await session.send(mc)

        try:
            
            # 处理列表类型的复杂结果
            mc = MessageChain()
            exist_image = False
            more_mc = None
            
            for i, item in enumerate(result):
                # 确保 item 是字典
                if not isinstance(item, dict):
                    logger.warning(f"结果项 {i} 不是字典，跳过: {item}")
                    continue
                
                if item.get('type') == 'string':
                    # 处理字符串类型的结果，可能是文本消息
                    mc.append(item.get('string', ''))
                elif item.get('type') == 'base64' and not exist_image:
                    # 处理Base64编码的图像数据
                    mc.append(Image(f'data:image/png;base64,{item.get("string", "")}'))
                    exist_image = True
                elif item.get('type') == 'base64' and exist_image:
                    # 处理Base64编码的图像数据
                    if more_mc is None:
                        more_mc = MessageChain()
                    more_mc.append(Image(f'data:image/png;base64,{item.get("string", "")}'))

            await _send(mc)
            if more_mc:
                await _send(more_mc)
        

        except ServerException as e:
            logger.error(f"服务器异常: {e}")
            try:
                error_data = json.loads(str(e).split("text:")[1].split(", traceID")[0])
                await _send(MessageChain(f"消息发送失败, 返回错误：{error_data['message']}"))
            except (IndexError, json.JSONDecodeError):
                logger.error(f"无法解析服务器错误")
                raise e
        except Exception as e:
            logger.error(f"未知异常: {e}")
            raise e

    if msg := cmd_select(session, prefix=COMMAND_PREFIX):
        try:
            # 使用配置的平台或自动检测的平台
            platform = PLATFORM if PLATFORM is not None else session.event.login.platform
            await cmd_generator(message=msg, user_id=session.event.user.id, platform=platform, send_func=func_send)
        except Exception as e:
            logger.error(f"cmd_generator 执行失败: {e}")
            raise e
