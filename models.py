"""
CEITEC HUB - Modelos e Operações do Banco de Dados SQLite
Integração com BNCC Computação e Sistema de Correção Automática
"""

import sqlite3
import hashlib
import json
import os
from datetime import datetime

DATABASE = 'database.db'

class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or DATABASE
        self.avaliacoes = AvaliacaoModels(self)
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Inicializa o banco de dados com todas as tabelas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # --- TABELAS ORIGINAIS ---
        
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                escola TEXT NOT NULL,
                serie TEXT NOT NULL,
                senha_hash TEXT NOT NULL,
                tipo TEXT CHECK(tipo IN ('aluno', 'professor')) NOT NULL,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de resultados de matemática
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resultados_matematica (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                nivel TEXT CHECK(nivel IN ('facil', 'medio', 'dificil')) NOT NULL,
                pontuacao INTEGER NOT NULL,
                data_jogo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Tabela de avaliações IA (Redação)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS avaliacoes_ia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                texto TEXT NOT NULL,
                nivel_classificacao TEXT CHECK(nivel_classificacao IN 
                    ('Iniciante', 'Intermediário', 'Proficiente', 'Avançado')) NOT NULL,
                feedback TEXT NOT NULL,
                pontuacao INTEGER,
                data_avaliacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Tabela de projetos de robótica
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projetos_robotica (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                titulo TEXT NOT NULL,
                descricao TEXT NOT NULL,
                area TEXT CHECK(area IN ('Arduino', 'Scratch', 'IA', 'Maker')) NOT NULL,
                nivel TEXT CHECK(nivel IN ('iniciante', 'intermediario', 'avancado')) NOT NULL,
                nota INTEGER CHECK(nota >= 0 AND nota <= 100),
                imagem TEXT,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')

        conn.commit()
        conn.close()
        
        # Inicializar tabelas do módulo de avaliações
        self.avaliacoes.criar_tabelas_avaliacoes()
        print("✅ Banco de dados oficial CEITEC HUB inicializado!")

    # ==================== OPERAÇÕES DE USUÁRIO ====================
    
    def hash_senha(self, senha):
        return hashlib.sha256(senha.encode()).hexdigest()
    
    def create_user(self, nome, escola, serie, senha, tipo):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            senha_hash = self.hash_senha(senha)
            cursor.execute('''
                INSERT INTO usuarios (nome, escola, serie, senha_hash, tipo)
                VALUES (?, ?, ?, ?, ?)
            ''', (nome, escola, serie, senha_hash, tipo))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def authenticate(self, nome, senha):
        conn = self.get_connection()
        cursor = conn.cursor()
        senha_hash = self.hash_senha(senha)
        cursor.execute('SELECT * FROM usuarios WHERE nome = ? AND senha_hash = ?', (nome, senha_hash))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def get_user_by_id(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None

    # ==================== OPERAÇÕES MÓDULOS BÁSICOS ====================
    
    def salvar_resultado_matematica(self, usuario_id, nivel, pontuacao):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO resultados_matematica (usuario_id, nivel, pontuacao) VALUES (?, ?, ?)', 
                       (usuario_id, nivel, pontuacao))
        conn.commit()
        conn.close()

    def get_ranking_geral(self, limit=10):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.nome, u.escola, 
                   COALESCE(SUM(r.pontuacao), 0) as total_pontos,
                   COUNT(r.id) as questoes_respondidas
            FROM usuarios u
            LEFT JOIN resultados_matematica r ON u.id = r.usuario_id
            WHERE u.tipo = 'aluno'
            GROUP BY u.id
            ORDER BY total_pontos DESC
            LIMIT ?
        ''', (limit,))
        ranking = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return ranking

    def get_ranking_por_escola(self, escola, limit=10):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.nome, u.serie,
                   COALESCE(SUM(r.pontuacao), 0) as total_pontos
            FROM usuarios u
            LEFT JOIN resultados_matematica r ON u.id = r.usuario_id
            WHERE u.escola = ? AND u.tipo = 'aluno'
            GROUP BY u.id
            ORDER BY total_pontos DESC
            LIMIT ?
        ''', (escola, limit))
        ranking = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return ranking

    def salvar_avaliacao_ia(self, usuario_id, texto, nivel_classificacao, feedback, pontuacao=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        pontos_nivel = {'Iniciante': 25, 'Intermediário': 50, 'Proficiente': 75, 'Avançado': 100}
        pontuacao = pontuacao or pontos_nivel.get(nivel_classificacao, 0)
        cursor.execute('''
            INSERT INTO avaliacoes_ia (usuario_id, texto, nivel_classificacao, feedback, pontuacao)
            VALUES (?, ?, ?, ?, ?)
        ''', (usuario_id, texto, nivel_classificacao, feedback, pontuacao))
        conn.commit()
        conn.close()

    def cadastrar_projeto(self, usuario_id, titulo, descricao, area, nivel, nota, imagem):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO projetos_robotica 
            (usuario_id, titulo, descricao, area, nivel, nota, imagem)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (usuario_id, titulo, descricao, area, nivel, nota, imagem))
        projeto_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return projeto_id

    def get_projetos_robotica(self, limit=50):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, u.nome as autor, u.escola
            FROM projetos_robotica p
            JOIN usuarios u ON p.usuario_id = u.id
            ORDER BY p.nota DESC, p.data_cadastro DESC
            LIMIT ?
        ''', (limit,))
        projetos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return projetos

    def get_pontuacao_total(self, usuario_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COALESCE(SUM(pontuacao), 0) FROM resultados_matematica WHERE usuario_id = ?', (usuario_id,))
        pts_mat = cursor.fetchone()[0] or 0
        cursor.execute('SELECT COALESCE(SUM(pontuacao), 0) FROM avaliacoes_ia WHERE usuario_id = ?', (usuario_id,))
        pts_ia = cursor.fetchone()[0] or 0
        cursor.execute('SELECT COALESCE(SUM(nota), 0) FROM projetos_robotica WHERE usuario_id = ?', (usuario_id,))
        pts_rob = cursor.fetchone()[0] or 0
        conn.close()
        return pts_mat + pts_ia + pts_rob

    def get_pontuacao_modulo(self, usuario_id, modulo):
        conn = self.get_connection()
        cursor = conn.cursor()
        if modulo == 'matematica':
            cursor.execute('SELECT COALESCE(SUM(pontuacao), 0) FROM resultados_matematica WHERE usuario_id = ?', (usuario_id,))
        elif modulo == 'avaliacao_ia':
            cursor.execute('SELECT COALESCE(SUM(pontuacao), 0) FROM avaliacoes_ia WHERE usuario_id = ?', (usuario_id,))
        elif modulo == 'robotica':
            cursor.execute('SELECT COALESCE(SUM(nota), 0) FROM projetos_robotica WHERE usuario_id = ?', (usuario_id,))
        else:
            return 0
        result = cursor.fetchone()[0] or 0
        conn.close()
        return result

    def get_historico_matematica(self, usuario_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT nivel, pontuacao, data_jogo FROM resultados_matematica WHERE usuario_id = ? ORDER BY data_jogo DESC LIMIT 10', (usuario_id,))
        historico = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return historico

    def get_historico_avaliacoes(self, usuario_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT nivel_classificacao, pontuacao, data_avaliacao FROM avaliacoes_ia WHERE usuario_id = ? ORDER BY data_avaliacao DESC LIMIT 10', (usuario_id,))
        historico = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return historico

    def get_historico_robotica(self, usuario_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT titulo, area, nota, data_cadastro FROM projetos_robotica WHERE usuario_id = ? ORDER BY data_cadastro DESC', (usuario_id,))
        historico = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return historico

    def get_posicao_ranking(self, usuario_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            WITH ranking AS (
                SELECT usuario_id, SUM(pontuacao) as total,
                       RANK() OVER (ORDER BY SUM(pontuacao) DESC) as posicao
                FROM resultados_matematica
                GROUP BY usuario_id
            )
            SELECT posicao FROM ranking WHERE usuario_id = ?
        ''', (usuario_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_total_alunos(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE tipo = 'aluno'")
        total = cursor.fetchone()[0]
        conn.close()
        return total

    def get_estatisticas_gerais(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        stats = {}
        cursor.execute("SELECT tipo, COUNT(*) FROM usuarios GROUP BY tipo")
        stats['usuarios'] = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.execute("SELECT COUNT(*) FROM resultados_matematica")
        stats['total_matematica'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM avaliacoes_ia")
        stats['total_avaliacoes'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM projetos_robotica")
        stats['total_projetos'] = cursor.fetchone()[0]
        cursor.execute("SELECT AVG(pontuacao) FROM resultados_matematica")
        stats['media_matematica'] = round(cursor.fetchone()[0] or 0, 2)
        conn.close()
        return stats

    def get_desempenho_por_escola(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.escola, 
                   COUNT(DISTINCT u.id) as total_alunos,
                   COALESCE(SUM(r.pontuacao), 0) as pontuacao_total
            FROM usuarios u
            LEFT JOIN resultados_matematica r ON u.id = r.usuario_id
            WHERE u.tipo = 'aluno'
            GROUP BY u.escola
            ORDER BY pontuacao_total DESC
        ''')
        escolas = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return escolas


class AvaliacaoModels:
    def __init__(self, db_instance):
        self.db = db_instance
    
    def criar_tabelas_avaliacoes(self):
        """Cria tabelas necessárias para o módulo de avaliações"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Tabela de provas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS provas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_aplicacao DATE,
                turma TEXT NOT NULL,
                professor_id INTEGER NOT NULL,
                status TEXT DEFAULT 'ativa' CHECK(status IN ('ativa', 'encerrada', 'rascunho')),
                num_questoes INTEGER DEFAULT 30,
                FOREIGN KEY (professor_id) REFERENCES usuarios(id)
            )
        ''')
        
        # Tabela de questões
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prova_id INTEGER NOT NULL,
                numero INTEGER NOT NULL,
                texto TEXT,
                alternativas TEXT, -- JSON: ["A", "B", "C", "D", "E"]
                resposta_correta TEXT NOT NULL,
                habilidade_bncc TEXT, -- Ex: EF09CI03
                descricao_habilidade TEXT,
                peso REAL DEFAULT 1.0,
                FOREIGN KEY (prova_id) REFERENCES provas(id) ON DELETE CASCADE
            )
        ''')
        
        # Tabela de gabaritos oficiais
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gabaritos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prova_id INTEGER NOT NULL,
                questoes_json TEXT NOT NULL, -- JSON com {numero: resposta}
                FOREIGN KEY (prova_id) REFERENCES provas(id) ON DELETE CASCADE
            )
        ''')
        
        # Tabela de respostas dos alunos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS respostas_alunos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prova_id INTEGER NOT NULL,
                aluno_id INTEGER,
                nome_ocr TEXT,
                turma TEXT,
                respostas_json TEXT, -- JSON: {numero: alternativa}
                qr_code_data TEXT,
                imagem_path TEXT,
                data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                nota_final REAL,
                acertos INTEGER,
                FOREIGN KEY (prova_id) REFERENCES provas(id),
                FOREIGN KEY (aluno_id) REFERENCES usuarios(id)
            )
        ''')
        
        # Tabela de desempenho por habilidade
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS desempenho_habilidades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resposta_id INTEGER NOT NULL,
                habilidade_bncc TEXT NOT NULL,
                total_questoes INTEGER DEFAULT 0,
                acertos INTEGER DEFAULT 0,
                percentual REAL DEFAULT 0,
                FOREIGN KEY (resposta_id) REFERENCES respostas_alunos(id) ON DELETE CASCADE
            )
        ''')

        # Tabela de turmas cadastradas (Gestão Pro)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS turmas_cadastradas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                professor_id INTEGER NOT NULL,
                serie TEXT,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (professor_id) REFERENCES usuarios(id)
            )
        ''')

        # Tabela de alunos cadastrados (Gestão Pro)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alunos_cadastrados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                turma_id INTEGER NOT NULL,
                professor_id INTEGER NOT NULL,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (turma_id) REFERENCES turmas_cadastradas(id) ON DELETE CASCADE,
                FOREIGN KEY (professor_id) REFERENCES usuarios(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ==================== OPERAÇÕES DE PROVAS ====================
    
    def criar_prova(self, nome, turma, professor_id, data_aplicacao=None, num_questoes=30):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO provas (nome, turma, professor_id, data_aplicacao, num_questoes)
            VALUES (?, ?, ?, ?, ?)
        ''', (nome, turma, professor_id, data_aplicacao, num_questoes))
        prova_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return prova_id
    
    def adicionar_questao(self, prova_id, numero, resposta_correta, 
                         habilidade_bncc=None, descricao_habilidade=None, 
                         peso=1.0, texto=None, alternativas=None):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        alts_json = json.dumps(alternativas if alternativas else ["A", "B", "C", "D", "E"])
        cursor.execute('''
            INSERT INTO questoes 
            (prova_id, numero, texto, alternativas, resposta_correta, 
             habilidade_bncc, descricao_habilidade, peso)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (prova_id, numero, texto, alts_json, resposta_correta,
              habilidade_bncc, descricao_habilidade, peso))
        conn.commit()
        conn.close()
    
    def salvar_gabarito(self, prova_id, gabarito_dict):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        gabarito_json = json.dumps(gabarito_dict)
        cursor.execute('''
            INSERT OR REPLACE INTO gabaritos (prova_id, questoes_json)
            VALUES (?, ?)
        ''', (prova_id, gabarito_json))
        conn.commit()
        conn.close()

    def excluir_prova(self, prova_id, professor_id):
        """Exclui uma prova e todos os seus dados relacionados (ON DELETE CASCADE)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        # Verificar se a prova pertence ao professor
        cursor.execute('DELETE FROM provas WHERE id = ? AND professor_id = ?', (prova_id, professor_id))
        conn.commit()
        conn.close()

    def limpar_questoes_prova(self, prova_id):
        """Remove todas as questões de uma prova para permitir re-inserir"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM questoes WHERE prova_id = ?', (prova_id,))
        conn.commit()
        conn.close()
    
    def get_prova(self, prova_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, u.nome as professor_nome 
            FROM provas p
            JOIN usuarios u ON p.professor_id = u.id
            WHERE p.id = ?
        ''', (prova_id,))
        res = cursor.fetchone()
        if not res: return None
        prova = dict(res)
        cursor.execute('SELECT * FROM questoes WHERE prova_id = ? ORDER BY numero', (prova_id,))
        prova['questoes'] = [dict(q) for q in cursor.fetchall()]
        cursor.execute('SELECT questoes_json FROM gabaritos WHERE prova_id = ?', (prova_id,))
        row = cursor.fetchone()
        prova['gabarito'] = json.loads(row['questoes_json']) if row else {}
        conn.close()
        return prova
    
    def listar_provas(self, professor_id=None, turma=None):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        query = '''
            SELECT p.*, u.nome as professor_nome,
                   (SELECT COUNT(*) FROM respostas_alunos WHERE prova_id = p.id) as total_correcoes
            FROM provas p
            JOIN usuarios u ON p.professor_id = u.id
            WHERE 1=1
        '''
        params = []
        if professor_id:
            query += ' AND p.professor_id = ?'
            params.append(professor_id)
        if turma:
            query += ' AND p.turma = ?'
            params.append(turma)
        query += ' ORDER BY p.data_criacao DESC'
        cursor.execute(query, params)
        provas = [dict(p) for p in cursor.fetchall()]
        conn.close()
        return provas

    def salvar_resposta_aluno(self, prova_id, respostas_dict, qr_data=None, 
                             nome_ocr=None, imagem_path=None, aluno_id=None):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        respostas_json = json.dumps(respostas_dict)
        cursor.execute('''
            INSERT INTO respostas_alunos 
            (prova_id, aluno_id, nome_ocr, respostas_json, qr_code_data, imagem_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (prova_id, aluno_id, nome_ocr, respostas_json, qr_data, imagem_path))
        resposta_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return resposta_id
    
    def calcular_nota(self, prova_id, respostas_dict):
        prova = self.get_prova(prova_id)
        gabarito = prova['gabarito']
        questoes = {q['numero']: q for q in prova['questoes']}
        acertos = 0
        nota_total = 0
        peso_total = 0
        desempenho_habilidades = {}
        for num, resposta_aluno in respostas_dict.items():
            num = int(num)
            if str(num) in gabarito:
                questao = questoes.get(num, {})
                peso = questao.get('peso', 1.0)
                habilidade = questao.get('habilidade_bncc', 'GERAL')
                if habilidade not in desempenho_habilidades:
                    desempenho_habilidades[habilidade] = {'total': 0, 'acertos': 0}
                desempenho_habilidades[habilidade]['total'] += 1
                peso_total += peso
                if resposta_aluno and resposta_aluno.upper() == gabarito[str(num)].upper():
                    acertos += 1
                    nota_total += peso
                    desempenho_habilidades[habilidade]['acertos'] += 1
        nota_final = (nota_total / peso_total * 10) if peso_total > 0 else 0
        for hab in desempenho_habilidades:
            dh = desempenho_habilidades[hab]
            dh['percentual'] = (dh['acertos'] / dh['total'] * 100) if dh['total'] > 0 else 0
        return {
            'nota_final': round(nota_final, 2),
            'acertos': acertos,
            'total_questoes': len(gabarito),
            'desempenho_habilidades': desempenho_habilidades
        }
    
    def salvar_desempenho_habilidades(self, resposta_id, desempenho_dict):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        for habilidade, dados in desempenho_dict.items():
            cursor.execute('''
                INSERT INTO desempenho_habilidades 
                (resposta_id, habilidade_bncc, total_questoes, acertos, percentual)
                VALUES (?, ?, ?, ?, ?)
            ''', (resposta_id, habilidade, dados['total'], 
                  dados['acertos'], dados['percentual']))
        conn.commit()
        conn.close()
    
    def atualizar_nota_resposta(self, resposta_id, nota_final, acertos):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE respostas_alunos SET nota_final = ?, acertos = ? WHERE id = ?', (nota_final, acertos, resposta_id))
        conn.commit()
        conn.close()

    def get_resultados_prova(self, prova_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, u.nome as aluno_nome
            FROM respostas_alunos r
            LEFT JOIN usuarios u ON r.aluno_id = u.id
            WHERE r.prova_id = ?
            ORDER BY r.nota_final DESC
        ''', (prova_id,))
        resultados = []
        for row in cursor.fetchall():
            res = dict(row)
            cursor.execute('SELECT * FROM desempenho_habilidades WHERE resposta_id = ?', (row['id'],))
            res['habilidades'] = [dict(h) for h in cursor.fetchall()]
            resultados.append(res)
        conn.close()
        return resultados
    
    def get_estatisticas_prova(self, prova_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as total_alunos, AVG(nota_final) as media_turma,
                   MAX(nota_final) as nota_maxima, MIN(nota_final) as nota_minima
            FROM respostas_alunos WHERE prova_id = ?
        ''', (prova_id,))
        stats = dict(cursor.fetchone())
        cursor.execute('''
            SELECT CASE 
                WHEN nota_final >= 9 THEN 'Excelente (9-10)'
                WHEN nota_final >= 7 THEN 'Bom (7-8.9)'
                WHEN nota_final >= 5 THEN 'Regular (5-6.9)'
                ELSE 'Insuficiente (<5)'
            END as faixa, COUNT(*) as quantidade
            FROM respostas_alunos WHERE prova_id = ? GROUP BY faixa
        ''', (prova_id,))
        stats['distribuicao'] = [dict(r) for r in cursor.fetchall()]
        cursor.execute('''
            SELECT dh.habilidade_bncc, AVG(dh.percentual) as media_percentual,
                   SUM(dh.total_questoes) as total_questoes, SUM(dh.acertos) as total_acertos
            FROM desempenho_habilidades dh
            JOIN respostas_alunos r ON dh.resposta_id = r.id
            WHERE r.prova_id = ?
            GROUP BY dh.habilidade_bncc
        ''', (prova_id,))
        stats['habilidades_turma'] = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return stats

    def get_analise_questoes(self, prova_id):
        """Retorna estatísticas de acertos/erros por questão"""
        prova = self.get_prova(prova_id)
        gabarito = prova['gabarito']
        resultados = self.get_resultados_prova(prova_id)
        
        analise = {}
        for num in gabarito:
            analise[num] = {'acertos': 0, 'erros': 0, 'total': 0, 'distribuicao': {'A':0, 'B':0, 'C':0, 'D':0, 'E':0}}

        for res in resultados:
            resp_aluno = json.loads(res['respostas_json']) if res['respostas_json'] else {}
            for num, alt in resp_aluno.items():
                if num in analise:
                    analise[num]['total'] += 1
                    if alt:
                        analise[num]['distribuicao'][alt.upper()] = analise[num]['distribuicao'].get(alt.upper(), 0) + 1
                    
                    if alt and alt.upper() == gabarito[num].upper():
                        analise[num]['acertos'] += 1
                    else:
                        analise[num]['erros'] += 1
        
        return analise

    # ==================== GESTÃO DE TURMAS E ALUNOS ====================

    def cadastrar_turma(self, nome, professor_id, serie=None):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO turmas_cadastradas (nome, professor_id, serie) VALUES (?, ?, ?)', 
                       (nome, professor_id, serie))
        turma_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return turma_id

    def cadastrar_aluno(self, nome, turma_id, professor_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO alunos_cadastrados (nome, turma_id, professor_id) VALUES (?, ?, ?)', 
                       (nome, turma_id, professor_id))
        conn.commit()
        conn.close()
        return True

    def get_turmas_completas(self, professor_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.*, 
                   (SELECT COUNT(*) FROM alunos_cadastrados WHERE turma_id = t.id) as total_alunos
            FROM turmas_cadastradas t
            WHERE t.professor_id = ?
            ORDER BY t.nome ASC
        ''', (professor_id,))
        turmas = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return turmas

    def get_turma_por_id(self, turma_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM turmas_cadastradas WHERE id = ?', (turma_id,))
        res = cursor.fetchone()
        conn.close()
        return dict(res) if res else None

    def get_alunos_por_turma_id(self, turma_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM alunos_cadastrados WHERE turma_id = ? ORDER BY nome ASC', (turma_id,))
        alunos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return alunos

    def excluir_turma(self, turma_id, professor_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM turmas_cadastradas WHERE id = ? AND professor_id = ?', (turma_id, professor_id))
        conn.commit()
        conn.close()

    def get_turmas_professor(self, professor_id):
        # Unificando: Pega as cadastradas e também as que existem em provas (compatibilidade)
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT nome as turma FROM turmas_cadastradas WHERE professor_id = ?
            UNION
            SELECT DISTINCT turma FROM provas WHERE professor_id = ?
        ''', (professor_id, professor_id))
        turmas = [row['turma'] for row in cursor.fetchall()]
        conn.close()
        return turmas

    def get_alunos_turma(self, professor_id, turma):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        # Busca unificada
        cursor.execute('''
            SELECT DISTINCT nome, 'Cadastrado' as origem
            FROM alunos_cadastrados 
            WHERE turma_id IN (SELECT id FROM turmas_cadastradas WHERE nome = ? AND professor_id = ?)
            UNION
            SELECT DISTINCT nome_ocr as nome, 'Prova' as origem
            FROM respostas_alunos 
            WHERE prova_id IN (SELECT id FROM provas WHERE professor_id = ? AND turma = ?)
        ''', (turma, professor_id, professor_id, turma))
        alunos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return alunos
