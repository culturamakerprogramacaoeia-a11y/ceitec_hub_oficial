"""
Motor de Leitura de QR Code
Extração de metadados dos cartões-resposta
"""

import cv2
import numpy as np
from pyzbar.pyzbar import decode
from typing import Dict, Optional, List
import json

class QREngine:
    def ler_qr_code(self, image_path: str) -> Dict:
        img = cv2.imread(image_path)
        if img is None:
            return {'sucesso': False, 'erro': 'Imagem não encontrada'}
            
        resultados = decode(img)
        if not resultados:
            img_proc = self._preprocessar_para_qr(img)
            resultados = decode(img_proc)
            
        if not resultados:
            return {'sucesso': False, 'erro': 'QR Code não detectado'}
            
        qr_data = resultados[0].data.decode('utf-8')
        return self._parse_qr_data(qr_data)
    
    def _preprocessar_para_qr(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        return enhanced
    
    def _parse_qr_data(self, data: str) -> Dict:
        resultado = {'sucesso': True, 'raw_data': data, 'dados': {}}
        try:
            json_data = json.loads(data)
            resultado['dados'] = json_data
            return resultado
        except:
            pass
            
        if data.startswith('CEITEC|'):
            partes = data.split('|')
            if len(partes) >= 4:
                resultado['dados'] = {
                    'prova_id': int(partes[1]) if partes[1].isdigit() else None,
                    'aluno_id': int(partes[2]) if partes[2].isdigit() else None,
                    'turma': partes[3]
                }
                return resultado
        return resultado

    def gerar_qr_data(self, prova_id: int, aluno_id: int = None, turma: str = "", nome: str = "") -> str:
        dados = {'prova_id': prova_id, 'aluno_id': aluno_id, 'turma': turma, 'nome': nome}
        return json.dumps(dados, ensure_ascii=False)
