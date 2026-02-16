"""
Motor de OCR (Optical Character Recognition)
Reconhecimento de texto manuscrito
tes
"""

import cv2
import numpy as np
import pytesseract
import re
from typing import Dict

class OCREngine:
    def __init__(self):
        self.config_letras = '--oem 3 --psm 6 -l por'
        # Tentar definir caminho padrão no Linux se necessário
        if os.name != 'nt':
            import shutil
            tess_path = shutil.which('tesseract')
            if tess_path:
                pytesseract.pytesseract.tesseract_cmd = tess_path
    
    def extrair_nome(self, image_path: str, regiao: tuple = None) -> Dict:
        img = cv2.imread(image_path)
        if img is None:
            return {'sucesso': False, 'erro': 'Imagem não encontrada'}
            
        if regiao:
            x, y, w, h = regiao
            roi = img[y:y+h, x:x+w]
        else:
            altura, largura = img.shape[:2]
            roi = img[50:150, 50:largura-50]
            
        roi_processada = self._preprocessar_texto(roi)
        
        try:
            texto = pytesseract.image_to_string(roi_processada, config=self.config_letras)
            nome_limpo = self._limpar_nome(texto)
            return {
                'sucesso': True,
                'nome': nome_limpo,
                'confianca': 0.8 # Simulado sem image_to_data complexo
            }
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}
    
    def _preprocessar_texto(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        # Binarização
        _, binary = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    
    def _limpar_nome(self, texto: str) -> str:
        limpo = re.sub(r'[^a-zA-ZáéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ\s]', '', texto)
        limpo = ' '.join(limpo.split())
        return limpo.title().strip()
