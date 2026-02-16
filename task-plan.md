# 🪖 Plano de Guerra: Projeto CEITEC HUB - Módulo de Avaliações

## 🎯 Objetivo
Coordenar a integração do módulo de correção automatizada (OMR/QR/OCR) ao sistema CEITEC HUB, garantindo robustez, design profissional e prontidão para deploy no PythonAnywhere.

---

## 🏗️ Fase 1: Fundação e Estrutura (Backend & DB)
**Especialista: Backend / DBA**
- [ ] Inicializar estrutura de pastas do projeto.
- [ ] Criar `models.py` integrando as tabelas legadas e as novas tabelas de Provas, Questões, Gabaritos e Resultados.
- [ ] Implementar `app.py` com as rotas base de autenticação e dashboard.
- [ ] Configurar `requirements.txt` com as dependências de visão computacional (OpenCV, pytesseract, pyzbar).

## 👁️ Fase 2: Motores de Visão e PDF (Engenharia de Processamento)
**Especialista: Engenheiro de Imagem**
- [ ] Implementar `qr_engine.py` para identificação única de alunos/provas.
- [ ] Implementar `omr_engine.py` para leitura das bolhas do cartão-resposta.
- [ ] Implementar `ocr_engine.py` para reconhecimento de nomes e campos manuscritos.
- [ ] Implementar `pdf_generator.py` para gerar cartões-resposta dinâmicos com QR Code.

## 🎨 Fase 3: Interface e Experiência do Usuário (Frontend)
**Especialista: Design/Front**
- [ ] Desenvolver templates responsivos para Gestão de Provas (`avaliacoes/`).
- [ ] Criar interface de correção via upload/câmera com feedback em tempo real.
- [ ] Implementar Dashboard Analítico com `Chart.js` para visualização de dados BNCC.
- [ ] Polir o CSS (`style.css`) com estética premium (glassmorphism/dark mode).

## 🚀 Fase 4: Integração, Testes e Deploy
**Especialista: DevOps/Security**
- [ ] Integrar todos os motores ao fluxo de rotas do Flask.
- [ ] Realizar testes de ponta a ponta (Criação -> Impressão -> Simulação de Imagem -> Resultado).
- [ ] Configurar `wsgi.py` para PythonAnywhere.
- [ ] Preparar repositório Git e documentação final de deploy.

---

## 🛠️ Tecnologias Escolhidas
- **Linguagem:** Python 3.10
- **Framework Web:** Flask
- **Banco de Dados:** SQLite (nativo e eficiente para PythonAnywhere)
- **Visão Computacional:** 
  - `OpenCV` (Processamento de Imagem)
  - `PyZbar` (Leitura de QR Code)
  - `PyTesseract` (OCR)
- **Geração de PDF:** `ReportLab`
- **Frontend:** HTML5, CSS3 (Vanilla Moderna), JavaScript (ES6+), Chart.js
