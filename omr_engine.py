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
            
        # OTIMIZAÇÃO: Redimensionar para acelerar OMR
        h, w = img.shape[:2]
        if w > 1200:
            escala = 1200 / w
            img = cv2.resize(img, (1200, int(h * escala)))

        img_processada = self._preprocessar(img)
        regioes = self._detectar_regioes_marcacao(img_processada)
        
        # Agrupamento Robusto por Linhas
        debug_img = img.copy() if img is not None else None
        questoes = self._agrupar_por_linhas(regioes, debug_img)
        
        respostas = self._ler_marcacoes(img_processada, questoes)
        multiplas = self._detectar_multiplas_marcacoes(respostas)
        
        # Salva imagem de debug para conferência
        if debug_img is not None:
            debug_path = image_path.replace(".jpg", "_debug.jpg").replace(".png", "_debug.png")
            cv2.imwrite(debug_path, debug_img)

        return {
            'respostas': {k: v['resposta'] for k, v in respostas.items()},
            'multiplas_marcacoes': multiplas,
            'total_processado': len(respostas),
            'confianca_media': self._calcular_confianca(respostas)
        }
    
    def _preprocessar(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Aumentar contraste
        alpha = 1.5 # Contraste
        beta = 0    # Brilho
        gray = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
        
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
                # Mais tolerante com circularidade (0.5 em vez de 0.7) e área (80 em vez de 100)
                if 0.5 < circularidade < 1.2 and 50 < area < 1500:
                    (x, y), raio = cv2.minEnclosingCircle(cnt)
                    bolhas.append((int(x), int(y), int(raio)))
        return bolhas

    def _agrupar_por_linhas(self, regioes: List[Tuple], debug_img=None) -> Dict:
        """Agrupa bolhas em linhas baseadas na coordenada Y"""
        if not regioes: return {}
        
        # Ordenar por Y
        regioes = sorted(regioes, key=lambda b: b[1])
        
        linhas = []
        if regioes:
            linha_atual = [regioes[0]]
            for i in range(1, len(regioes)):
                # Se a diferença de Y for pequena, pertence à mesma linha
                if abs(regioes[i][1] - linha_atual[-1][1]) < 20:
                    linha_atual.append(regioes[i])
                else:
                    linhas.append(sorted(linha_atual, key=lambda b: b[0]))
                    linha_atual = [regioes[i]]
            linhas.append(sorted(linha_atual, key=lambda b: b[0]))

        questoes = {}
        q_count = 1
        for linha in linhas:
            # Em nosso layout, cada linha tem 1 ou 2 questões (cada uma com 5 bolhas)
            # Total de bolhas esperado na linha: 5 ou 10
            if len(linha) >= 5:
                # Questão da Esquerda
                questoes[q_count] = linha[:5]
                if debug_img is not None:
                    for b in linha[:5]: cv2.circle(debug_img, (b[0], b[1]), b[2], (0, 255, 0), 2)
                q_count += 1
                
                # Questão da Direita (se houver mais bolhas)
                if len(linha) >= 10:
                    questoes[q_count] = linha[5:10]
                    if debug_img is not None:
                        for b in linha[5:10]: cv2.circle(debug_img, (b[0], b[1]), b[2], (255, 0, 0), 2)
                    q_count += 1
                    
        return questoes

    def _ler_marcacoes(self, img: np.ndarray, questoes: Dict) -> Dict:
        respostas = {}
        for num_questao, alternativas in questoes.items():
            if num_questao > self.config['total_questoes']:
                break
                
            resultados_alts = []
            for alt_idx, (x, y, r) in enumerate(alternativas):
                if alt_idx >= 5: break
                preenchimento = self._calcular_preenchimento(img, x, y, r)
                resultados_alts.append(preenchimento)
            
            # Encontrar a alternativa mais preenchida
            maior_p = max(resultados_alts) if resultados_alts else 0
            if maior_p > self.config['threshold']:
                idx = resultados_alts.index(maior_p)
                respostas[num_questao] = {
                    'resposta': self.config['alternativas'][idx],
                    'confianca': round(maior_p, 2)
                }
            else:
                respostas[num_questao] = {'resposta': None, 'confianca': 0}
                
        return respostas
    
    def _calcular_preenchimento(self, img: np.ndarray, x: int, y: int, r: int) -> float:
        mask = np.zeros(img.shape, dtype=np.uint8)
        cv2.circle(mask, (x, y), int(r * 0.8), 255, -1) # Usar 80% do raio para evitar bordas
        roi = cv2.bitwise_and(img, mask)
        pixels_totais = cv2.countNonZero(mask)
        pixels_preenchidos = cv2.countNonZero(roi)
        return pixels_preenchidos / pixels_totais if pixels_totais > 0 else 0
    
    def _detectar_multiplas_marcacoes(self, respostas: Dict) -> List[int]:
        multiplas = []
        # Implementação básica: se a confiança for baixa, pode ser múltipla
        # (Idealmente checaríamos se há duas alternativas com preenchimento alto)
        return multiplas

    def _calcular_confianca(self, respostas: Dict) -> float:
        if not respostas: return 0.0
        confiancas = [r['confianca'] for r in respostas.values() if r['resposta']]
        return round(np.mean(confiancas), 2) if confiancas else 0.0
