"""
Motor de Processamento OMR (Optical Mark Recognition)
Detecção de marcações em cartões-resposta
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional

class OMREngine:
    def __init__(self):
        # Configurações padrão do cartão
        self.config = {
            'questoes_per_coluna': 15,
            'total_questoes': 30,
            'alternativas': ['A', 'B', 'C', 'D', 'E'],
            'margem_superior': 150,
            'margem_lateral': 50,
            'espacamento_vertical': 35,
            'espacamento_horizontal': 45,
            'tamanho_bolha': 20,
            'threshold': 0.4
        }
    
    def processar_imagem(self, image_path: str, prova_config: dict = None) -> Dict:
        if prova_config:
            self.config.update(prova_config)
            
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Não foi possível carregar a imagem")
            
        img_processada = self._preprocessar(img)
        regioes = self._detectar_regioes_marcacao(img_processada)
        respostas = self._ler_marcacoes(img_processada, regioes)
        multiplas = self._detectar_multiplas_marcacoes(respostas)
        
        return {
            'respostas': {k: v['resposta'] for k, v in respostas.items()},
            'multiplas_marcacoes': multiplas,
            'total_processado': len(respostas),
            'confianca_media': self._calcular_confianca(respostas)
        }
    
    def _preprocessar(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        return thresh
    
    def _detectar_regioes_marcacao(self, img: np.ndarray) -> List[Tuple]:
        contornos, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        bolhas = []
        for cnt in contornos:
            area = cv2.contourArea(cnt)
            perimetro = cv2.arcLength(cnt, True)
            if perimetro > 0:
                circularidade = 4 * np.pi * area / (perimetro ** 2)
                if 0.7 < circularidade < 1.0 and 100 < area < 1000:
                    (x, y), raio = cv2.minEnclosingCircle(cnt)
                    bolhas.append((int(x), int(y), int(raio)))
        bolhas = sorted(bolhas, key=lambda b: (b[1], b[0]))
        return bolhas
    
    def _ler_marcacoes(self, img: np.ndarray, regioes: List[Tuple]) -> Dict:
        respostas = {}
        questoes = self._agrupar_bolhas(regioes)
        for num_questao, alternativas in questoes.items():
            if num_questao > self.config['total_questoes']:
                break
            melhor_marcacao = None
            maior_preenchimento = 0
            for alt, (x, y, r) in zip(self.config['alternativas'], alternativas):
                preenchimento = self._calcular_preenchimento(img, x, y, r)
                if preenchimento > self.config['threshold'] and preenchimento > maior_preenchimento:
                    maior_preenchimento = preenchimento
                    melhor_marcacao = alt
            respostas[num_questao] = {
                'resposta': melhor_marcacao,
                'confianca': round(maior_preenchimento, 2)
            }
        return respostas
    
    def _agrupar_bolhas(self, regioes: List[Tuple]) -> Dict:
        questoes = {}
        for i in range(0, len(regioes) - 4, 5):
            num_questao = (i // 5) + 1
            questoes[num_questao] = regioes[i:i+5]
        return questoes
    
    def _calcular_preenchimento(self, img: np.ndarray, x: int, y: int, r: int) -> float:
        mask = np.zeros(img.shape, dtype=np.uint8)
        cv2.circle(mask, (x, y), r, 255, -1)
        roi = cv2.bitwise_and(img, mask)
        pixels_totais = cv2.countNonZero(mask)
        pixels_preenchidos = cv2.countNonZero(roi)
        return pixels_preenchidos / pixels_totais if pixels_totais > 0 else 0
    
    def _detectar_multiplas_marcacoes(self, respostas: Dict) -> List[int]:
        multiplas = []
        for num, dados in respostas.items():
            if dados['confianca'] < 0.6 and dados['confianca'] > 0.2:
                multiplas.append(num)
        return multiplas
    
    def _calcular_confianca(self, respostas: Dict) -> float:
        if not respostas: return 0.0
        confiancas = [r['confianca'] for r in respostas.values() if r['resposta']]
        return round(np.mean(confiancas), 2) if confiancas else 0.0
