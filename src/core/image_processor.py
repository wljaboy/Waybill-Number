import cv2
import numpy as np
import logging
from typing import Optional, Dict, Any
from PIL import Image
from pyzbar.pyzbar import decode
import os
import json
import sys

logger = logging.getLogger(__name__)

class ImageProcessor:
    """图像处理器"""
    
    def __init__(self):
        """初始化图像处理器"""
        from .ocr.tesseract import TesseractOCR
        self.tesseract = TesseractOCR()
        
        # 尝试初始化腾讯云OCR
        try:
            from .ocr.tencent import TencentOCR
            
            # 获取配置文件路径
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            config_path = os.path.join(app_dir, 'config.json')
            
            # 如果程序目录的配置文件不存在或无法访问，尝试用户目录
            if not os.path.exists(config_path):
                user_config_path = os.path.join(os.path.expanduser('~'), 'waybill_config.json')
                if os.path.exists(user_config_path):
                    config_path = user_config_path
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if config.get('tencent_ocr', {}).get('enabled'):
                        self.tencent = TencentOCR(
                            config['tencent_ocr']['secret_id'],
                            config['tencent_ocr']['secret_key']
                        )
                        logger.info("腾讯云OCR初始化成功")
        except Exception as e:
            logger.warning(f"腾讯云OCR初始化失败: {str(e)}")
        
        logger.info("图像处理器初始化完成")

    def process_image(self, image_path: str, options: Dict[str, Any]) -> Optional[str]:
        """
        处理图像
        Args:
            image_path: 图片路径
            options: 处理选项
        Returns:
            str: 识别到的运单号，失败返回None
        """
        try:
            logger.debug(f"开始处理图片: {image_path}")
            
            # 使用正确的编码读取图像
            image = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError(f"无法读取图像: {image_path}")
            
            results = []
            
            # 条码识别
            if options.get('scan_barcode') or options.get('scan_qrcode'):
                try:
                    codes = decode(image)
                    for code in codes:
                        text = code.data.decode('utf-8')
                        results.append(text)
                        logger.debug(f"条码识别结果: {text}")
                except Exception as e:
                    logger.error(f"条码识别失败: {str(e)}")
            
            # 文字识别
            if options.get('scan_text'):
                try:
                    # 转换为PIL图像
                    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                    
                    # 如果指定了识别区域，裁剪图片
                    if options.get('region'):
                        region = options['region']
                        width, height = pil_image.size
                        x1 = int(region['x1'] * width)
                        y1 = int(region['y1'] * height)
                        x2 = int(region['x2'] * width)
                        y2 = int(region['y2'] * height)
                        pil_image = pil_image.crop((x1, y1, x2, y2))
                    
                    # 先使用Tesseract OCR
                    texts = self.tesseract.recognize(pil_image)
                    results.extend(texts)
                    logger.debug(f"Tesseract OCR识别结果: {texts}")
                    
                    # 如果Tesseract没有识别到结果，并且启用了腾讯云OCR，则使用腾讯云OCR
                    waybill_number = self._filter_results(results, options)
                    if not waybill_number and options.get('use_tencent') and hasattr(self, 'tencent'):
                        try:
                            texts = self.tencent.recognize(pil_image)
                            logger.debug(f"腾讯云OCR识别结果: {texts}")
                            results.extend(texts)
                        except Exception as e:
                            logger.error(f"腾讯云OCR识别失败: {str(e)}")
                
                except Exception as e:
                    logger.error(f"OCR识别失败: {str(e)}")
            
            # 过滤结果
            waybill_number = self._filter_results(results, options)
            if waybill_number:
                logger.info(f"成功识别运单号: {waybill_number}")
                return waybill_number
            else:
                logger.warning("未能识别到有效运单号")
                return None
            
        except Exception as e:
            logger.error(f"处理图片失败: {str(e)}")
            return None

    def _filter_results(self, results: list, options: Dict[str, Any]) -> Optional[str]:
        """
        过滤识别结果
        Args:
            results: 识别结果列表
            options: 过滤选项
        Returns:
            str: 符合条件的运单号，没有找到返回None
        """
        try:
            min_length = int(options.get('min_length', 8))
            max_length = int(options.get('max_length', 12))
            prefix = options.get('prefix', '')
            suffix = options.get('suffix', '')
            
            for result in results:
                if not result:
                    continue
                    
                # 清理结果
                result = ''.join(c for c in result if c.isalnum())
                
                # 检查长度
                if len(result) < min_length or len(result) > max_length:
                    continue
                
                # 检查前缀
                if prefix and not result.upper().startswith(prefix.upper()):
                    continue
                
                # 检查后缀
                if suffix and not result.upper().endswith(suffix.upper()):
                    continue
                
                return result
                
            return None
            
        except Exception as e:
            logger.error(f"过滤结果失败: {str(e)}")
            return None 