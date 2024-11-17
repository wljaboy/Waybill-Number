import json
import logging
import numpy as np
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.ocr.v20181119 import ocr_client, models
from . import OCREngine
import cv2
import base64
from PIL import Image

logger = logging.getLogger(__name__)

class TencentOCR(OCREngine):
    """腾讯云OCR引擎"""
    
    def __init__(self, secret_id, secret_key, region="ap-guangzhou"):
        """
        初始化腾讯云OCR
        Args:
            secret_id: 腾讯云API密钥ID
            secret_key: 腾讯云API密钥Key
            region: 地域信息
        """
        try:
            cred = credential.Credential(secret_id, secret_key)
            http_profile = HttpProfile()
            http_profile.endpoint = "ocr.tencentcloudapi.com"
            
            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile
            
            self.client = ocr_client.OcrClient(cred, region, client_profile)
            logger.info("腾讯云OCR初始化成功")
            
        except Exception as e:
            logger.error(f"腾讯云OCR初始化失败: {str(e)}")
            raise

    def recognize(self, image):
        """
        使用腾讯云OCR识别图像文字
        Args:
            image: PIL.Image 或 numpy.ndarray 格式的图像
        Returns:
            list: 识别到的文本列表
        """
        try:
            # 将PIL Image转换为OpenCV格式
            if isinstance(image, Image.Image):
                # 转换为RGB模式（如果不是的话）
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                # 转换为numpy数组
                image = np.array(image)
                # 转换颜色通道顺序从RGB到BGR
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # 确保图像是numpy数组格式
            if not isinstance(image, np.ndarray):
                raise ValueError("不支持的图像格式")
            
            # 将图像编码为base64
            _, buffer = cv2.imencode('.jpg', image)
            img_base64 = base64.b64encode(buffer).decode()
            
            # 创建请求
            req = models.GeneralAccurateOCRRequest()
            req.ImageBase64 = img_base64
            
            # 发送请求
            resp = self.client.GeneralAccurateOCR(req)
            
            # 解析结果
            results = []
            waybill_number = None
            
            for text_detection in resp.TextDetections:
                text = text_detection.DetectedText
                results.append(text)
                
                # 提取运单号
                if 'NO:' in text or '编号:' in text:
                    # 提取YS开头的数字
                    import re
                    match = re.search(r'YS\d+', text)
                    if match:
                        waybill_number = match.group()
            
            # 如果找到运单号，将其放在结果列表的最前面
            if waybill_number:
                results.insert(0, waybill_number)
            
            return results
            
        except TencentCloudSDKException as e:
            logger.error(f"腾讯云OCR识别失败: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"OCR处理失败: {str(e)}")
            return [] 