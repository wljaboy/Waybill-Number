import os
import logging
from typing import Dict, List, Tuple, Optional
from .image_processor import ImageProcessor

logger = logging.getLogger(__name__)

class WaybillScanner:
    """运单扫描器"""
    
    def __init__(self, config_path: str = 'config.json'):
        """初始化扫描器"""
        self.processor = ImageProcessor()
        logger.info("扫描器初始化完成")
    
    def scan_single(self, image_path: str, options: Dict) -> Optional[str]:
        """
        扫描单个图片
        Args:
            image_path: 图片路径
            options: 识别选项
        Returns:
            str: 识别到的运单号，失败返回None
        """
        try:
            logger.debug(f"开始处理图片: {image_path}")
            result = self.processor.process_image(image_path, options)
            logger.debug(f"处理结果: {result}")
            return result
        except Exception as e:
            logger.error(f"处理图片失败 {image_path}: {str(e)}")
            return None

    def scan_batch(self, folder_path: str, options: Dict) -> Tuple[List[Tuple[str, str]], List[str]]:
        """
        批量扫描图片
        Args:
            folder_path: 图片文件夹路径
            options: 识别选项
        Returns:
            Tuple[List[Tuple[str, str]], List[str]]: 
            (成功列表[(文件名,运单号)], 失败列表[文件名])
        """
        try:
            logger.info(f"开始批量处理文件夹: {folder_path}")
            success_files = []
            failed_files = []
            
            # 获取所有图片文件
            image_files = [
                f for f in os.listdir(folder_path)
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))
            ]
            
            for filename in image_files:
                try:
                    image_path = os.path.join(folder_path, filename)
                    result = self.scan_single(image_path, options)
                    
                    if result:
                        success_files.append((filename, result))
                        logger.info(f"成功识别: {filename} -> {result}")
                    else:
                        failed_files.append(filename)
                        logger.warning(f"识别失败: {filename}")
                        
                except Exception as e:
                    logger.error(f"处理文件失败 {filename}: {str(e)}")
                    failed_files.append(filename)
            
            logger.info(f"批量处理完成: 成功 {len(success_files)}, 失败 {len(failed_files)}")
            return success_files, failed_files
            
        except Exception as e:
            logger.error(f"批量处理失败: {str(e)}")
            return [], []