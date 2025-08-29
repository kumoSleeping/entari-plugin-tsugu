from arclet.entari import metadata
import json
from typing import List, Optional, Union
from arclet.entari import Entari, WS, load_plugin
from arclet.entari import metadata
import time
from arclet.entari import Entari, WS, load_plugin
import arclet.letoderea as leto
from arclet.entari import MessageCreatedEvent, Session, MessageChain
from satori.element import Custom
from satori.exception import ServerException
from arclet.entari import MessageChain, At, Image

from tsugu import cmd_generator


metadata(
    name="entari-plugin-tsugu",
    author=[{"name": "kumoSleeping", "email": "zjr2992@outlook.com"}],
    version="0.1.0",
    description="Tsugu BanGDream Bot",
)



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
                return pure_text[len(p):].strip()
    else:
        return pure_text

    return ''


@leto.on(MessageCreatedEvent)
async def on_message_created(session: Session[MessageCreatedEvent]):
        
    async def _send(result):
        more_mc = None
            
        try:
            if isinstance(result, list):                    
                mc = MessageChain()
                exist_image = False
                for item in result:
                    if item['type'] == 'string':
                        # 处理字符串类型的结果，可能是文本消息
                        mc.append(item['string'])
                    elif item['type'] == 'base64' and not exist_image:
                        # 处理Base64编码的图像数据
                        mc.append(Image(f'data:image/png;base64,{item["string"]}'))
                        exist_image = True
                    elif item['type'] == 'base64' and exist_image:
                        # 处理Base64编码的图像数据
                        more_mc = MessageChain()
                        more_mc.append(Image(f'data:image/png;base64,{item["string"]}'))

                await session.send(mc)
                if more_mc:
                    for item in more_mc:
                        await session.send(item)
            elif isinstance(result, str):
                await session.send(result)
            else:
                await session.send("消息发送失败, 内部错误.")

        except ServerException as e:
            try:
                error_data = json.loads(str(e).split("text:")[1].split(", traceID")[0])
                await session.send(f"消息发送失败, 返回错误：{error_data['message']}")
            except (IndexError, json.JSONDecodeError):
                raise e
        except Exception as e:
            raise e

    if msg := cmd_select(session, prefix=['/', '']):
        print(f"Received command: {msg} from user {session.event.user.id} on platform {session.event.login.platform}")
        await cmd_generator(message=msg, user_id=session.event.user.id,platform=session.event.login.platform, send_func=_send)
        
