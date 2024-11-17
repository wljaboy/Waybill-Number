def recognize(self, image_path: str) -> List[str]:
    try:
        # 读取图片并转为base64
        with open(image_path, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode()
            
        # 调用OCR API
        req = models.GeneralAccurateOCRRequest()
        req.ImageBase64 = img_data
        
        # 获取响应
        resp = self.client.GeneralAccurateOCR(req)
        logger.debug(f"腾讯云OCR原始响应: {resp}")
        
        # 检查错误
        if hasattr(resp, 'Error'):
            logger.error(f"腾讯云OCR返回错误: {resp.Error}")
            return []
            
        # 解析文本结果
        if not hasattr(resp, 'TextDetections'):
            logger.warning("腾讯云OCR响应中没有TextDetections字段")
            return []
            
        texts = []
        for detection in resp.TextDetections:
            if hasattr(detection, 'DetectedText'):
                text = detection.DetectedText.strip()
                logger.debug(f"检测到文本: {text}")
                texts.append(text)
            
        return texts
        
    except Exception as e:
        logger.error(f"腾讯云OCR处理异常: {str(e)}")
        return [] 