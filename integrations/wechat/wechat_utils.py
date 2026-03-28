"""
微信公众号工具函数
处理消息签名验证、XML 解析、消息构建
"""

import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime


def verify_signature(token: str, signature: str, timestamp: str, nonce: str) -> bool:
    """
    验证微信服务器签名
    微信服务器会发送 signature/timestamp/nonce 用于验证
    """
    params = sorted([token, timestamp, nonce])
    sign_str = ''.join(params)
    sha1 = hashlib.sha1(sign_str.encode('utf-8')).hexdigest()
    return sha1 == signature


def parse_message(xml_str: str) -> dict:
    """
    解析微信消息 XML
    返回消息字典
    """
    root = ET.fromstring(xml_str)
    msg = {}
    for child in root:
        msg[child.tag] = child.text
    return msg


def build_text_reply(to_user: str, from_user: str, content: str) -> str:
    """
    构建文本回复 XML
    """
    timestamp = int(datetime.now().timestamp())
    return f"""<xml>
  <ToUserName><![CDATA[{to_user}]]></ToUserName>
  <FromUserName><![CDATA[{from_user}]]></FromUserName>
  <CreateTime>{timestamp}</CreateTime>
  <MsgType><![CDATA[text]]></MsgType>
  <Content><![CDATA[{content}]]></Content>
</xml>"""


def build_image_reply(to_user: str, from_user: str, media_id: str) -> str:
    """
    构建图片回复 XML
    """
    timestamp = int(datetime.now().timestamp())
    return f"""<xml>
  <ToUserName><![CDATA[{to_user}]]></ToUserName>
  <FromUserName><![CDATA[{from_user}]]></FromUserName>
  <CreateTime>{timestamp}</CreateTime>
  <MsgType><![CDATA[image]]></MsgType>
  <Image>
    <MediaId><![CDATA[{media_id}]]></MediaId>
  </Image>
</xml>"""
