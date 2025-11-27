from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import os

# Inicializa o SQLAlchemy
db = SQLAlchemy()

def init_db(app):
    """
    Inicializa o banco de dados MySQL com as tabelas necessárias
    """
    # Configura o SQLAlchemy com o app Flask
    db.init_app(app)
    
    with app.app_context():
        try:
            # Cria todas as tabelas
            db.create_all()
            
            # ============================================
            # Cria usuário administrador padrão
            # ============================================
            from models import Usuario  # Import aqui para evitar circular imports
            
            # Verifica se já existe algum usuário administrador
            admin_existente = Usuario.query.filter_by(email='admin@sistema.com').first()
            
            if not admin_existente:
                # Cria o usuário administrador
                admin = Usuario(
                    nome='Administrador',
                    email='admin@sistema.com',
                    senha_hash=generate_password_hash('admin123'),
                    tipo='admin',
                    ativo=True
                )
                db.session.add(admin)
                db.session.commit()
                
                print("   Usuário admin criado:")
                print("   Email: admin@sistema.com")
                print("   Senha: admin123")
            
            print("✓ Banco de dados MySQL inicializado com sucesso!")
            
        except Exception as e:
            print(f"✗ Erro ao inicializar banco de dados MySQL: {e}")
            db.session.rollback()
            raise

def get_connection():
    """
    Retorna uma conexão com o banco de dados
    Para compatibilidade com código existente
    """
    return db