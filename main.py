from astrbot.api.message_components import *
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api.all import *
import importlib
import subprocess
import sys

@register("mccloud_zhipu_img", "MC云-小馒头", "使用智谱AI生成图片。使用画一个什么什么。", "1.0")
class ZhipuImagePlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "cogView-4")
        
        # 检查并安装 zhipuai
        if not self._check_zhipuai():
            self._install_zhipuai()
        
        # 导入 zhipuai
        global ZhipuAI
        from zhipuai import ZhipuAI

    def _check_zhipuai(self) -> bool:
        """检查是否安装了 zhipuai"""
        try:
            importlib.import_module('zhipuai')
            return True
        except ImportError:
            return False

    def _install_zhipuai(self):
        """安装 zhipuai 包"""
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "zhipuai"])
            print("成功安装 zhipuai 包")
        except subprocess.CalledProcessError as e:
            print(f"安装 zhipuai 包失败: {str(e)}")
            raise

    @filter.event_message_type(EventMessageType.ALL)
    async def generate_image(self, event: AstrMessageEvent):
        """监听所有消息,识别关键词进行图片生成"""
        message = event.message_str
        
        # 检查是否包含绘画相关关键词
        draw_keywords = ["画", "绘画", "画个", "画张", "画一个", "画一张", "生图", "画画", "img", "painting"]
        if not any(keyword in message for keyword in draw_keywords):
            return  # 如果没有关键词就直接返回,不执行后续操作
            
        # 检查是否配置了API密钥
        if not self.api_key:
            yield event.plain_result("\n请先在配置文件中设置智谱AI的API密钥")
            return

        # 使用原始消息作为提示词
        prompt = message
            
        if not prompt:
            yield event.plain_result("\n请提供绘画内容的描述!")
            return

        # 检查尺寸参数
        valid_sizes = ["1024x1024", "1440x720", "768x1344", "864x1152", 
                      "1344x768", "1152x864", "1440x720", "720x1440"]
        size = "1024x1024"  # 默认尺寸
        
        # 检查消息中是否包含尺寸信息
        for valid_size in valid_sizes:
            if valid_size in message:
                size = valid_size
                break

        try:
            # 创建智谱AI客户端
            client = ZhipuAI(api_key=self.api_key)
            
            # 发送生成请求
            response = client.images.generations(
                model=self.model,
                prompt=prompt,
                size=size
            )
            
            # 获取生成的图片URL
            image_url = response.data[0].url
            
            # 构建消息链
            chain = [
                Plain(f"提示词：{prompt}\n大小：{size}\n"),
                Image.fromURL(image_url)
            ]
            
            yield event.chain_result(chain)
            
        except Exception as e:
            yield event.plain_result(f"\n生成图片失败: {str(e)}")
