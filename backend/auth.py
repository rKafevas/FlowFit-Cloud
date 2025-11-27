"""
Auth - Sistema de Autenticação e Autorização
Gerencia login, logout e controle de acesso
Usando SQLAlchemy ORM para MySQL
"""

from database import db
from models import Usuario, Historico
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import os
import datetime
from functools import wraps
from flask import request, jsonify

# Chave secreta para JWT (em produção, use variável de ambiente)
SECRET_KEY = os.environ.get('SECRET_KEY', 'chave-temporaria-desenvolvimento')

# ==================== FUNÇÕES DE USUÁRIO ====================

def criar_usuario(nome, email, senha, tipo='operador'):
    """
    Cria um novo usuário no sistema
    Tipos: 'admin' ou 'operador'
    """
    try:
        # Verifica se email já existe
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            return {"success": False, "error": "Email já cadastrado"}
        
        usuario = Usuario(
            nome=nome,
            email=email,
            tipo=tipo
        )
        usuario.set_senha(senha)
        
        db.session.add(usuario)
        db.session.commit()
        return {"success": True, "id": usuario.id}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}

def listar_usuarios():
    """
    Lista todos os usuários do sistema
    """
    usuarios = Usuario.query.filter_by(ativo=True).order_by(Usuario.nome).all()
    
    return [{
        'id': u.id,
        'nome': u.nome,
        'email': u.email,
        'tipo': u.tipo,
        'ativo': u.ativo,
        'data_criacao': u.data_criacao.isoformat() if u.data_criacao else None,
        'ultimo_acesso': u.ultimo_acesso.isoformat() if u.ultimo_acesso else None
    } for u in usuarios]

def obter_usuario(usuario_id):
    """
    Obtém dados de um usuário específico
    """
    usuario = Usuario.query.get(usuario_id)
    
    if not usuario:
        return None
    
    return {
        'id': usuario.id,
        'nome': usuario.nome,
        'email': usuario.email,
        'tipo': usuario.tipo,
        'ativo': usuario.ativo,
        'data_criacao': usuario.data_criacao.isoformat() if usuario.data_criacao else None,
        'ultimo_acesso': usuario.ultimo_acesso.isoformat() if usuario.ultimo_acesso else None
    }

def atualizar_usuario(usuario_id, nome, email, tipo, senha=None):
    """
    Atualiza dados de um usuário
    """
    try:
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return {"success": False, "error": "Usuário não encontrado"}
        
        # Verifica se email já existe para outro usuário
        usuario_existente = Usuario.query.filter(
            Usuario.email == email,
            Usuario.id != usuario_id
        ).first()
        if usuario_existente:
            return {"success": False, "error": "Email já cadastrado para outro usuário"}
        
        usuario.nome = nome
        usuario.email = email
        usuario.tipo = tipo
        
        if senha:
            usuario.set_senha(senha)
        
        db.session.commit()
        return {"success": True}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}

def deletar_usuario(usuario_id):
    """
    Desativa um usuário (soft delete)
    """
    usuario = Usuario.query.get(usuario_id)
    if usuario:
        usuario.ativo = False
        db.session.commit()
    
    return {"success": True}

# ==================== AUTENTICAÇÃO ====================

def fazer_login(email, senha):
    """
    Autentica um usuário e retorna token JWT
    """
    usuario = Usuario.query.filter_by(email=email, ativo=True).first()
    
    if not usuario:
        return {"success": False, "error": "Usuário não encontrado"}
    
    # Verifica a senha
    if not usuario.check_senha(senha):
        return {"success": False, "error": "Senha incorreta"}
    
    # Atualiza último acesso
    usuario.ultimo_acesso = datetime.datetime.utcnow()
    
    # Registra no histórico
    historico = Historico(
        usuario_id=usuario.id,
        acao='LOGIN',
        descricao=f'Usuário {usuario.nome} fez login'
    )
    
    db.session.add(historico)
    db.session.commit()
    
    # Gera token JWT
    token = gerar_token(usuario.id, usuario.email, usuario.tipo)
    
    return {
        "success": True,
        "token": token,
        "usuario": {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
            "tipo": usuario.tipo
        }
    }

def gerar_token(usuario_id, email, tipo):
    """
    Gera um token JWT para o usuário
    """
    payload = {
        'usuario_id': usuario_id,
        'email': email,
        'tipo': tipo,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=8)  # Token expira em 8 horas
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verificar_token(token):
    """
    Verifica se um token JWT é válido
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return {"success": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"success": False, "error": "Token expirado"}
    except jwt.InvalidTokenError:
        return {"success": False, "error": "Token inválido"}

# ==================== DECORADOR DE AUTENTICAÇÃO ====================

def requer_autenticacao(f):
    """
    Decorador que verifica se o usuário está autenticado
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"error": "Token não fornecido"}), 401
        
        # Remove 'Bearer ' do token se existir
        if token.startswith('Bearer '):
            token = token[7:]
        
        resultado = verificar_token(token)
        
        if not resultado['success']:
            return jsonify({"error": resultado['error']}), 401
        
        # Adiciona dados do usuário à requisição
        request.usuario = resultado['payload']
        
        return f(*args, **kwargs)
    
    return decorated

def requer_admin(f):
    """
    Decorador que verifica se o usuário é administrador
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"error": "Token não fornecido"}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        resultado = verificar_token(token)
        
        if not resultado['success']:
            return jsonify({"error": resultado['error']}), 401
        
        if resultado['payload']['tipo'] != 'admin':
            return jsonify({"error": "Acesso negado. Apenas administradores."}), 403
        
        request.usuario = resultado['payload']
        
        return f(*args, **kwargs)
    
    return decorated

# ==================== HISTÓRICO ====================

def registrar_historico(usuario_id, acao, descricao):
    """
    Registra uma ação no histórico do sistema
    """
    try:
        historico = Historico(
            usuario_id=usuario_id,
            acao=acao,
            descricao=descricao
        )
        
        db.session.add(historico)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao registrar histórico: {e}")

def obter_historico(limite=50):
    """
    Obtém o histórico de ações do sistema
    """
    historico = Historico.query\
        .join(Usuario)\
        .order_by(Historico.data_acao.desc())\
        .limit(limite)\
        .all()
    
    return [{
        'id': h.id,
        'usuario_id': h.usuario_id,
        'usuario_nome': h.usuario.nome,
        'acao': h.acao,
        'descricao': h.descricao,
        'data_acao': h.data_acao.isoformat() if h.data_acao else None
    } for h in historico]