from abc import ABC, abstractmethod

class OCREngine(ABC):
    """OCR引擎基类"""
    
    @abstractmethod
    def recognize(self, image):
        """
        识别图像中的文字
        Args:
            image: OpenCV/PIL格式的图像
        Returns:
            list: 识别到的文本列表
        """
        pass 