# 🚀 CEITEC HUB - Plataforma Educacional Avançada

Bem-vindo ao **CEITEC HUB**, uma plataforma integrada desenvolvida para o Centro de Inovação em Tecnologia e Educação do Ceará. Este sistema combina gamificação educacional com ferramentas de visão computacional de ponta para automatizar a correção de avaliações.

---

## ✨ Funcionalidades Principais

- **🎮 Gamificação:** Módulos de Matemática, IA e Robótica com ranking global.
- **👁️ Visão Computacional (OMR):** Correção automática de cartões-resposta via fotos.
- **📷 Leitura de QR Code:** Identificação instantânea de provas e turmas.
- **📝 OCR Manuscrito:** Reconhecimento automático de nomes nos cartões.
- **📊 Analytics BNCC:** Dashboard detalhado com desempenho por habilidades da BNCC Computação.
- **🖨️ PDF Generator:** Geração dinâmica de cartões-resposta personalizados.

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Flask (Python 3.10)
- **Banco de Dados:** SQLite
- **Visão Computacional:** OpenCV, PyZbar, PyTesseract
- **Relatórios:** ReportLab (PDF), Chart.js (Gráficos)
- **Frontend:** HTML5, CSS3 (Glassmorphism Design), JavaScript Premium

---

## 🌎 Guia de Deploy (PythonAnywhere)

Para configurar o CEITEC HUB no seu painel [PythonAnywhere](https://www.pythonanywhere.com/user/ceitecitapipoca/):

### 1. Clonagem e Dependências
Abra um Bash Console e execute:
```bash
mkvirtualenv --python=/usr/bin/python3.10 ceitec_env
pip install -r requirements.txt
```

### 2. Configuração Web
No painel **Web** do PythonAnywhere:
- **Source Code:** `/home/ceitecitapipoca/ceitec_hub`
- **Working Directory:** `/home/ceitecitapipoca/ceitec_hub`
- **Virtualenv:** `/home/ceitecitapipoca/.virtualenvs/ceitec_env`
- **WSGI Configuration File:** Configure conforme o arquivo `wsgi.py` fornecido no projeto.

### 3. Arquivos Estáticos
Configure na aba **Static Files**:
- URL: `/static/` -> Directory: `/home/ceitecitapipoca/ceitec_hub/static/`

### 4. Inicialização do Banco
No Bash Console:
```bash
python -c "from models import Database; db = Database(); db.init_db()"
```

---

## 🧑‍💻 Comandos Úteis (Git)

Para versionar suas alterações:
```bash
git add .
git commit -m "feat: implementado módulo de correção OMR/OCR com integração BNCC"
git push origin main
```

---

## 📞 Suporte e Contato
Desenvolvido com foco na BNCC de Computação (9º Ano). Para suporte técnico, acesse o portal administrativo.
