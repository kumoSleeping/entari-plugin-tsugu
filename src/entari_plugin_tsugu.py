# entari-plugin-tsugu
# Tsugu BanGDream Bot Plugin for Entari Framework

__version__ = "0.1.3"

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

from tsugu import cmd_generator

# 添加调试日志
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TsuguPluginConfig(BasicConfModel):
    qq_passive: bool = False  # passive mode for QQ platform
    prefix: List[str] = ['/', '']  # command prefix list


metadata(
    name="entari-plugin-tsugu",
    author=[{"name": "kumoSleeping", "email": "zjr2992@outlook.com"}],
    version="0.1.3",
    description="Tsugu BanGDream Bot",
    config=TsuguPluginConfig,
)

# 获取配置实例
config = plugin_config(TsuguPluginConfig)

# 常量：QQ平台被动模式配置
QQ_PASSIVE = config.qq_passive
# 常量：命令前缀配置
COMMAND_PREFIX = config.prefix



def cmd_select(
        session: Session[MessageCreatedEvent],
        prefix: Union[str, List[str]] = '',
        ) -> Optional[str]:
    logger.debug(f"[DEBUG] cmd_select 函数被调用")
    msg = session.event.message.message
    pure_text = ''.join(str(e) for e in msg if e.tag == 'text').strip()
    logger.debug(f"[DEBUG] 提取的纯文本: '{pure_text}'")
    logger.debug(f"[DEBUG] 当前前缀配置: {prefix}")

    if prefix != ['']:
        prefix = prefix if isinstance(prefix, list) else [prefix]
        for p in prefix:
            logger.debug(f"[DEBUG] 检查前缀: '{p}'")
            if p == '' or pure_text.startswith(p):
                result = pure_text[len(p):].strip()
                logger.debug(f"[DEBUG] 匹配成功! 返回命令: '{result}'")
                return result
    else:
        logger.debug(f"[DEBUG] 使用空前缀，返回: '{pure_text}'")
        return pure_text

    logger.debug(f"[DEBUG] 没有匹配的前缀，返回空字符串")
    return ''


@leto.on(MessageCreatedEvent)
async def on_message_created(session: Session[MessageCreatedEvent]):
    logger.debug(f"[DEBUG] ========== 消息事件触发 ==========")
    logger.debug(f"[DEBUG] 用户ID: {session.event.user.id}")
    logger.debug(f"[DEBUG] 平台: {session.event.login.platform}")
    logger.debug(f"[DEBUG] 消息内容: {session.event.message.message}")
    logger.debug(f"[DEBUG] 当前配置 - QQ被动模式: {QQ_PASSIVE}")
    logger.debug(f"[DEBUG] 当前配置 - 命令前缀: {COMMAND_PREFIX}")

    async def func_send(result):
        logger.debug(f"[DEBUG] func_send 被调用，结果类型: {type(result)}")
        logger.debug(f"[DEBUG] func_send 结果内容: {result}")

        async def _send(mc: MessageChain):
            logger.debug(f"[DEBUG] _send 被调用，消息链: {mc}")
            if QQ_PASSIVE:
                logger.debug(f"[DEBUG] 添加QQ被动模式元素")
                # 添加 qq:passive 自定义元素到消息链中
                mc.append(Custom("qq:passive", {"id": session.event.message.id, "seq": int(time.time())}))
            logger.debug(f"[DEBUG] 准备发送消息...")
            await session.send(mc)
            logger.debug(f"[DEBUG] 消息发送完成")

        try:
            logger.debug(f"[DEBUG] 开始处理发送结果...")
            mc = MessageChain()
            exist_image = False
            more_mc = None
            for i, item in enumerate(result):
                logger.debug(f"[DEBUG] 处理结果项 {i}: {item}")
                if item['type'] == 'string':
                    logger.debug(f"[DEBUG] 添加文本: {item['string']}")
                    # 处理字符串类型的结果，可能是文本消息
                    mc.append(item['string'])
                elif item['type'] == 'base64' and not exist_image:
                    logger.debug(f"[DEBUG] 添加第一张图片")
                    # 处理Base64编码的图像数据
                    mc.append(Image(f'data:image/png;base64,{item["string"]}'))
                    exist_image = True
                elif item['type'] == 'base64' and exist_image:
                    logger.debug(f"[DEBUG] 添加额外图片")
                    # 处理Base64编码的图像数据
                    more_mc = MessageChain()
                    more_mc.append(Image(f'data:image/png;base64,{item["string"]}'))

            logger.debug(f"[DEBUG] 发送主消息...")
            await _send(mc)
            if more_mc:
                logger.debug(f"[DEBUG] 发送额外消息...")
                for item in more_mc:
                    await _send(item)

        except ServerException as e:
            logger.error(f"[ERROR] 服务器异常: {e}")
            try:
                error_data = json.loads(str(e).split("text:")[1].split(", traceID")[0])
                await _send(MessageChain(f"消息发送失败, 返回错误：{error_data['message']}"))
            except (IndexError, json.JSONDecodeError):
                logger.error(f"[ERROR] 无法解析服务器错误")
                raise e
        except Exception as e:
            logger.error(f"[ERROR] 未知异常: {e}")
            raise e

    logger.debug(f"[DEBUG] 调用 cmd_select...")
    if msg := cmd_select(session, prefix=COMMAND_PREFIX):
        logger.info(f"[INFO] ========== 处理命令 ==========")
        print(f"Received command: {msg} from user {session.event.user.id} on platform {session.event.login.platform}")
        logger.info(f"[INFO] 接收到命令: {msg}")
        logger.info(f"[INFO] 用户ID: {session.event.user.id}")
        logger.info(f"[INFO] 平台: {session.event.login.platform}")

        logger.debug(f"[DEBUG] 调用 cmd_generator...")
        try:
            await cmd_generator(message=msg, user_id=session.event.user.id,platform=session.event.login.platform, send_func=func_send)
            logger.debug(f"[DEBUG] cmd_generator 执行完成")
        except Exception as e:
            logger.error(f"[ERROR] cmd_generator 执行失败: {e}")
            raise e
    else:
        logger.debug(f"[DEBUG] 消息不匹配任何命令前缀，忽略")
        logger.debug(f"[DEBUG] ========== 消息事件结束 ==========")
