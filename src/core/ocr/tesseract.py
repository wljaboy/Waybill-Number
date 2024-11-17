import os
import sys
import logging
import pytesseract
from PIL import Image
from . import OCREngine

logger = logging.getLogger(__name__)

class TesseractOCR(OCREngine):
    """Tesseract OCR引擎"""
    
    def __init__(self):
        """初始化Tesseract OCR"""
        try:
            import sys
            import os
            
            if getattr(sys, 'frozen', False):
                # 如果是打包后的可执行文件
                base_path = os.path.dirname(sys.executable)
                tesseract_cmd = os.path.join(base_path, 'tesseract.exe')
                os.environ['TESSDATA_PREFIX'] = os.path.join(base_path, 'tessdata')
            else:
                # 如果是开发环境
                tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            
            # 设置 Tesseract 路径
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
            logger.info(f"Tesseract OCR 初始化成功，使用路径: {tesseract_cmd}")
            
        except Exception as e:
            logger.error(f"Tesseract OCR 初始化失败: {str(e)}")
            raise

    def recognize(self, image):
        """
        使用Tesseract识别图像文字
        Args:
            image: OpenCV/PIL格式的图像
        Returns:
            list: 识别到的文本列表
        """
        try:
            # 确保图像是PIL格式
            if not isinstance(image, Image.Image):
                image = Image.fromarray(image)
            
            # OCR配置列表
            configs = [
                {
                    'lang': 'chi_sim+eng',  # 中文简体+英文
                    'config': '--oem 3 --psm 3'  # 自动页面分割
                },
                {
                    'lang': 'chi_sim+eng',
                    'config': '--oem 3 --psm 6'  # 假设统一的文本块
                },
                {
                    'lang': 'eng',  # 仅英文模式可能对数字字母组合更准确
                    'config': '--oem 3 --psm 11'  # 稀疏文本
                }
            ]
            
            results = []
            waybill_number = None
            
            for config in configs:
                try:
                    text = pytesseract.image_to_string(
                        image,
                        lang=config['lang'],
                        config=config['config']
                    )
                    logger.debug(f"OCR配置 {config} 识别结果: {text}")
                    
                    # 分行处理
                    for line in text.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 清理特殊字符
                        line = ''.join(c for c in line if c.isalnum() or c in ':-.')
                        
                        # 查找运单号
                        if 'NO' in line.upper() or 'YS' in line.upper():
                            import re
                            match = re.search(r'YS\d{8}', line.upper())
                            if match:
                                waybill_number = match.group()
                                results.insert(0, waybill_number)  # 将运单号放在最前面
                                continue
                        
                        results.append(line)
                        
                except Exception as e:
                    logger.warning(f"使用配置 {config} 识别失败: {str(e)}")
                    continue
            
            # 去重并清理结果
            cleaned_results = []
            seen = set()
            for result in results:
                if result and result not in seen:
                    seen.add(result)
                    cleaned_results.append(result)
            
            return cleaned_results
            
        except Exception as e:
            logger.error(f"Tesseract识别失败: {str(e)}")
            return [] 