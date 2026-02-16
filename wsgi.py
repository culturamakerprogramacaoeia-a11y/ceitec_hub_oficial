"""
Arquivo WSGI para deploy no PythonAnywhere
"""
import sys
import os

# Adicionar o diretório do projeto ao path
path = '/home/ceitecitapipoca/ceitec_hub'
if path not in sys.path:
    sys.path.insert(0, path)

# Configurar variáveis de ambiente
os.environ['SECRET_KEY'] = 'ceitec-hub-prod-key-2024-ita'

from app import app as application

# Inicializar banco de dados
from models import Database
db = Database(os.path.join(path, 'database.db'))
try:
    db.init_db()
except:
    pass
