"""
Models - Modelos de Dados e Operações no Banco
Contém todas as funções para manipular clientes e pagamentos
Usando SQLAlchemy ORM para MySQL
"""

from database import db
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

# ==================== MODELOS (TABELAS) ====================

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(20), default='operador')
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acesso = db.Column(db.DateTime)
    
    # Relacionamentos
    historico_acoes = db.relationship('Historico', backref='usuario', lazy=True)
    pagamentos_registrados = db.relationship('Pagamento', backref='usuario_registro', lazy=True)
    
    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)
    
    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(20))
    cpf = db.Column(db.String(14), unique=True)
    endereco = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    pagamentos = db.relationship('Pagamento', backref='cliente', lazy=True)

class Pagamento(db.Model):
    __tablename__ = 'pagamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date)
    status = db.Column(db.String(20), default='pendente')
    descricao = db.Column(db.Text)
    metodo_pagamento = db.Column(db.String(50))
    observacoes = db.Column(db.Text)
    usuario_registro_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

class Historico(db.Model):
    __tablename__ = 'historico'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    acao = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    data_acao = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== OPERAÇÕES DE CLIENTES ====================

def criar_cliente(nome, email, telefone, cpf, endereco='', observacoes=''):
    """
    Cria um novo cliente no banco de dados
    """
    try:
        cliente = Cliente(
            nome=nome,
            email=email,
            telefone=telefone,
            cpf=cpf,
            endereco=endereco,
            observacoes=observacoes
        )
        
        db.session.add(cliente)
        db.session.commit()
        return {"success": True, "id": cliente.id}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": "CPF já cadastrado"}

def listar_clientes(busca=None):
    """
    Lista todos os clientes ou filtra por nome/CPF
    """
    query = Cliente.query.filter_by(ativo=True)
    
    if busca:
        query = query.filter(
            (Cliente.nome.like(f'%{busca}%')) | 
            (Cliente.cpf.like(f'%{busca}%'))
        )
    
    clientes = query.order_by(Cliente.nome).all()
    
    # Converter para dicionário
    return [{
        'id': c.id,
        'nome': c.nome,
        'email': c.email,
        'telefone': c.telefone,
        'cpf': c.cpf,
        'endereco': c.endereco,
        'observacoes': c.observacoes,
        'data_cadastro': c.data_cadastro.isoformat() if c.data_cadastro else None
    } for c in clientes]

def obter_cliente(cliente_id):
    """
    Obtém um cliente específico por ID com estatísticas
    """
    cliente = Cliente.query.get(cliente_id)
    
    if not cliente:
        return None
    
    # Estatísticas de pagamentos
    total_pagamentos = Pagamento.query.filter_by(cliente_id=cliente_id).count()
    pagamentos_pagos = Pagamento.query.filter_by(cliente_id=cliente_id, status='pago').count()
    pagamentos_pendentes = Pagamento.query.filter_by(cliente_id=cliente_id, status='pendente').count()
    
    valor_pendente_result = db.session.query(db.func.sum(Pagamento.valor)).filter(
        Pagamento.cliente_id == cliente_id,
        Pagamento.status == 'pendente'
    ).first()
    valor_pendente = valor_pendente_result[0] or 0
    
    cliente_dict = {
        'id': cliente.id,
        'nome': cliente.nome,
        'email': cliente.email,
        'telefone': cliente.telefone,
        'cpf': cliente.cpf,
        'endereco': cliente.endereco,
        'observacoes': cliente.observacoes,
        'data_cadastro': cliente.data_cadastro.isoformat() if cliente.data_cadastro else None,
        'estatisticas': {
            'total_pagamentos': total_pagamentos,
            'pagamentos_pagos': pagamentos_pagos,
            'pagamentos_pendentes': pagamentos_pendentes,
            'valor_pendente': float(valor_pendente)
        }
    }
    
    return cliente_dict

def atualizar_cliente(cliente_id, nome, email, telefone, cpf, endereco='', observacoes=''):
    """
    Atualiza os dados de um cliente
    """
    try:
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return {"success": False, "error": "Cliente não encontrado"}
        
        cliente.nome = nome
        cliente.email = email
        cliente.telefone = telefone
        cliente.cpf = cpf
        cliente.endereco = endereco
        cliente.observacoes = observacoes
        
        db.session.commit()
        return {"success": True}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": "CPF já cadastrado para outro cliente"}

def deletar_cliente(cliente_id):
    """
    Desativa um cliente (soft delete)
    """
    cliente = Cliente.query.get(cliente_id)
    if cliente:
        cliente.ativo = False
        db.session.commit()
    
    return {"success": True}

# ==================== OPERAÇÕES DE PAGAMENTOS ====================

def criar_pagamento(cliente_id, valor, vencimento, descricao, usuario_id=None):
    """
    Cria um novo pagamento para um cliente
    """
    # Validação: não aceitar valores negativos
    if valor <= 0:
        return {"success": False, "error": "O valor do pagamento deve ser maior que zero"}
    
    try:
        pagamento = Pagamento(
            cliente_id=cliente_id,
            valor=valor,
            vencimento=datetime.strptime(vencimento, '%Y-%m-%d').date(),
            descricao=descricao,
            usuario_registro_id=usuario_id
        )
        
        db.session.add(pagamento)
        db.session.commit()
        return {"success": True, "id": pagamento.id}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}

def listar_pagamentos(cliente_id=None, status=None, mes=None):
    """
    Lista pagamentos com filtros opcionais
    """
    query = Pagamento.query.join(Cliente)
    
    if cliente_id:
        query = query.filter(Pagamento.cliente_id == cliente_id)
    
    if status:
        query = query.filter(Pagamento.status == status)
    
    if mes:
        query = query.filter(db.func.to_char(Pagamento.data_pagamento, 'YYYY-MM') == mes)
    
    pagamentos = query.order_by(Pagamento.vencimento.desc()).all()
    
    return [{
        'id': p.id,
        'cliente_id': p.cliente_id,
        'cliente_nome': p.cliente.nome,
        'cliente_cpf': p.cliente.cpf,
        'cliente_telefone': p.cliente.telefone,
        'valor': p.valor,
        'vencimento': p.vencimento.isoformat() if p.vencimento else None,
        'data_pagamento': p.data_pagamento.isoformat() if p.data_pagamento else None,
        'status': p.status,
        'descricao': p.descricao,
        'metodo_pagamento': p.metodo_pagamento,
        'observacoes': p.observacoes,
        'data_criacao': p.data_criacao.isoformat() if p.data_criacao else None
    } for p in pagamentos]

def obter_historico_pagamentos(cliente_id):
    """
    Obtém o histórico completo de pagamentos de um cliente
    """
    pagamentos = Pagamento.query\
        .filter_by(cliente_id=cliente_id)\
        .outerjoin(Usuario)\
        .order_by(Pagamento.vencimento.desc())\
        .all()
    
    return [{
        'id': p.id,
        'valor': p.valor,
        'vencimento': p.vencimento.isoformat() if p.vencimento else None,
        'data_pagamento': p.data_pagamento.isoformat() if p.data_pagamento else None,
        'status': p.status,
        'descricao': p.descricao,
        'metodo_pagamento': p.metodo_pagamento,
        'usuario_nome': p.usuario_registro.nome if p.usuario_registro else None,
        'data_criacao': p.data_criacao.isoformat() if p.data_criacao else None
    } for p in pagamentos]

def registrar_pagamento(pagamento_id, metodo_pagamento):
    """
    Registra um pagamento como pago
    """
    pagamento = Pagamento.query.get(pagamento_id)
    if pagamento:
        pagamento.status = 'pago'
        pagamento.data_pagamento = date.today()
        pagamento.metodo_pagamento = metodo_pagamento
        db.session.commit()
    
    return {"success": True}

def cancelar_pagamento(pagamento_id):
    """
    Cancela um pagamento
    """
    pagamento = Pagamento.query.get(pagamento_id)
    if pagamento:
        pagamento.status = 'cancelado'
        db.session.commit()
    
    return {"success": True}

def deletar_pagamento(pagamento_id):
    """
    Deleta permanentemente um pagamento
    """
    pagamento = Pagamento.query.get(pagamento_id)
    if pagamento:
        db.session.delete(pagamento)
        db.session.commit()
    
    return {"success": True}

# ==================== RELATÓRIOS E DASHBOARD ====================

def obter_estatisticas():
    """
    Obtém estatísticas gerais do sistema
    """
    # Total de clientes ativos
    total_clientes = Cliente.query.filter_by(ativo=True).count()
    
    # Pagamentos pendentes
    pagamentos_pendentes = Pagamento.query.filter_by(status='pendente').count()
    
    # Valor total em aberto
    valor_em_aberto_result = db.session.query(db.func.sum(Pagamento.valor))\
        .filter(Pagamento.status == 'pendente').first()
    valor_em_aberto = valor_em_aberto_result[0] or 0
    
    # Pagamentos vencidos (data de vencimento já passou)
    pagamentos_vencidos = Pagamento.query.filter(
        Pagamento.status == 'pendente',
        Pagamento.vencimento < date.today()
    ).count()
    
    # Valor recebido no mês atual
    mes_atual = datetime.now().strftime('%Y-%m')
    valor_recebido_mes_result = db.session.query(db.func.sum(Pagamento.valor))\
        .filter(
            Pagamento.status == 'pago',
            db.func.to_char(Pagamento.data_pagamento, 'YYYY-MM') == mes_atual
        ).first()
    valor_recebido_mes = valor_recebido_mes_result[0] or 0
    
    # Clientes que pagaram este mês
    clientes_pagaram_mes = db.session.query(db.func.count(db.func.distinct(Pagamento.cliente_id)))\
        .filter(
            Pagamento.status == 'pago',
            db.func.to_char(Pagamento.data_pagamento, 'YYYY-MM') == mes_atual
        ).first()[0] or 0
    
    return {
        "total_clientes": total_clientes,
        "pagamentos_pendentes": pagamentos_pendentes,
        "valor_em_aberto": float(valor_em_aberto),
        "pagamentos_vencidos": pagamentos_vencidos,
        "valor_recebido_mes": float(valor_recebido_mes),
        "clientes_pagaram_mes": clientes_pagaram_mes
    }

def obter_inadimplentes():
    """
    Lista clientes com pagamentos vencidos
    """
    data_hoje = date.today()
    
    # Subquery para clientes inadimplentes
    inadimplentes = db.session.query(
        Cliente.id,
        Cliente.nome,
        Cliente.telefone,
        Cliente.email,
        db.func.count(Pagamento.id).label('qtd_pendencias'),
        db.func.sum(Pagamento.valor).label('valor_total'),
        db.func.min(Pagamento.vencimento).label('vencimento_mais_antigo')
    ).join(Pagamento).filter(
        Pagamento.status == 'pendente',
        Pagamento.vencimento < data_hoje
    ).group_by(Cliente.id).order_by('vencimento_mais_antigo').all()
    
    return [{
        'id': row.id,
        'nome': row.nome,
        'telefone': row.telefone,
        'email': row.email,
        'qtd_pendencias': row.qtd_pendencias,
        'valor_total': float(row.valor_total) if row.valor_total else 0,
        'vencimento_mais_antigo': row.vencimento_mais_antigo.isoformat() if row.vencimento_mais_antigo else None
    } for row in inadimplentes]

def obter_clientes_pagaram_mes():
    """
    Lista clientes que pagaram no mês atual
    """
    mes_atual = datetime.now().strftime('%Y-%m')
    
    clientes = db.session.query(
        Cliente.id,
        Cliente.nome,
        Cliente.telefone,
        db.func.count(Pagamento.id).label('qtd_pagamentos'),
        db.func.sum(Pagamento.valor).label('valor_total'),
        db.func.max(Pagamento.data_pagamento).label('ultimo_pagamento')
    ).join(Pagamento).filter(
        Pagamento.status == 'pago',
        db.func.to_char(Pagamento.data_pagamento, 'YYYY-MM') == mes_atual
    ).group_by(Cliente.id).order_by(Cliente.nome).all()
    
    return [{
        'id': row.id,
        'nome': row.nome,
        'telefone': row.telefone,
        'qtd_pagamentos': row.qtd_pagamentos,
        'valor_total': float(row.valor_total) if row.valor_total else 0,
        'ultimo_pagamento': row.ultimo_pagamento.isoformat() if row.ultimo_pagamento else None
    } for row in clientes]