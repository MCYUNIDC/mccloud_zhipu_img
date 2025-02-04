from astrbot.api.message_components import *
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
import importlib
import subprocess
import sys

@register("mccloud_zhipu_img", "MC云-小馒头", "使用智谱AI生成图片。使用 /aimg <提示词> [大小] 生成图片。", "1.0")
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

    @filter.command("aimg")
    async def generate_image(self, event: AstrMessageEvent, prompt: str = "", size: str = "1024x1024"):
        # 检查是否配置了API密钥
        if not self.api_key:
            yield event.plain_result("\n请先在配置文件中设置智谱AI的API密钥")
            return

        # 检查提示词是否为空
        if not prompt:
            yield event.plain_result("\n请提供提示词！使用方法：/aimg <提示词> [大小]\n支持的尺寸：1024x1024, 1440x720, 768x1344, 864x1152, 1344x768, 1152x864, 1440x720, 720x1440")
            return

        # 验证尺寸参数
        valid_sizes = ["1024x1024", "1440x720", "768x1344", "864x1152", "1344x768", "1152x864", "1440x720", "720x1440"]
        if size not in valid_sizes:
            yield event.plain_result(f"\n不支持的图片尺寸！请使用以下尺寸之一：{', '.join(valid_sizes)}")
            return

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
