"""
Script de inicialização do banco de dados PostgreSQL para Supabase
Gerencia a criação de tabelas e atualizações de esquema
"""
import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import streamlit as st
from db_utils import get_db_connection, table_exists, column_exists, add_column_if_not_exists

# Garante que o diretório de logs existe
os.makedirs('logs', exist_ok=True)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/db_init.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()

# Configurações do banco de dados
DB_CONFIG = {
    'db_type': os.getenv('DB_TYPE', 'postgresql'),
    'db_host': os.getenv('DB_HOST', 'localhost'),
    'db_port': os.getenv('DB_PORT', '5432'),
    'db_name': os.getenv('DB_NAME', 'locadora'),
    'db_user': os.getenv('DB_USER', 'postgres'),
    'db_password': os.getenv('DB_PASSWORD', 'postgres')
}

# Definição das tabelas
TABLES = {
    'carros': """
    CREATE TABLE IF NOT EXISTS carros (
        id BIGSERIAL PRIMARY KEY,
        marca TEXT NOT NULL,
        modelo TEXT NOT NULL,
        placa TEXT UNIQUE NOT NULL,
        cor TEXT,
        diaria DECIMAL(10,2) NOT NULL,
        preco_km DECIMAL(10,2) NOT NULL,
        km_atual INTEGER DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'Disponível', 
        numero_chassi TEXT,
        numero_renavam TEXT,
        ano_veiculo INTEGER,
        km_troca_oleo INTEGER DEFAULT 10000,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    )
    """,
    
    'clientes': """
    CREATE TABLE IF NOT EXISTS clientes (
        id BIGSERIAL PRIMARY KEY,
        nome TEXT NOT NULL,
        cpf TEXT UNIQUE NOT NULL,
        rg TEXT,
        cnh TEXT,
        validade_cnh DATE,
        uf_cnh TEXT,
        telefone TEXT,
        endereco TEXT,
        observacoes TEXT,
        status TEXT NOT NULL DEFAULT 'Ativo',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    )
    """,
    
    'reservas': """
    CREATE TABLE IF NOT EXISTS reservas (
        id BIGSERIAL PRIMARY KEY,
        carro_id BIGINT NOT NULL REFERENCES carros(id) ON DELETE RESTRICT,
        cliente_id BIGINT NOT NULL REFERENCES clientes(id) ON DELETE RESTRICT,
        data_inicio DATE NOT NULL,
        data_fim DATE NOT NULL,
        horario_entrega TIME,
        reserva_status TEXT NOT NULL DEFAULT 'Reservada',
        status TEXT,
        custo_lavagem DECIMAL(10,2) DEFAULT 0,
        valor_total DECIMAL(10,2) DEFAULT 0,
        km_saida INTEGER,
        km_volta INTEGER,
        km_franquia INTEGER DEFAULT 300,
        adiantamento DECIMAL(10,2) DEFAULT 0.0,
        valor_multas DECIMAL(10,2) DEFAULT 0.0,
        valor_danos DECIMAL(10,2) DEFAULT 0.0,
        valor_outros DECIMAL(10,2) DEFAULT 0.0,
        desconto_cliente DECIMAL(10,2) DEFAULT 0.0,
        meia_diaria BOOLEAN DEFAULT FALSE,
        total_diarias DECIMAL(10,2) DEFAULT 0.0,
        pagamento_parcial_entrega DECIMAL(10,2) DEFAULT 0.0,
        valor_restante DECIMAL(10,2) DEFAULT 0.0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        CHECK (data_fim >= data_inicio)
    )
    """,
    
    'multas': """
    CREATE TABLE IF NOT EXISTS multas (
        id BIGSERIAL PRIMARY KEY,
        reserva_id BIGINT NOT NULL REFERENCES reservas(id) ON DELETE CASCADE,
        tipo TEXT NOT NULL,
        valor DECIMAL(10,2) NOT NULL,
        data_multa TIMESTAMP WITH TIME ZONE NOT NULL,
        local_infracao TEXT,
        data_pagamento TIMESTAMP WITH TIME ZONE,
        status TEXT NOT NULL DEFAULT 'Pendente',
        observacao TEXT,
        comprovante_url TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        CHECK (status IN ('Pendente', 'Paga', 'Isentada')),
        CHECK (data_pagamento IS NULL OR data_pagamento >= data_multa)
    )
    """
}

# Índices para melhorar desempenho
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_reservas_carro_id ON reservas(carro_id)",
    "CREATE INDEX IF NOT EXISTS idx_reservas_cliente_id ON reservas(cliente_id)",
    "CREATE INDEX IF NOT EXISTS idx_reservas_data_inicio ON reservas(data_inicio)",
    "CREATE INDEX IF NOT EXISTS idx_reservas_data_fim ON reservas(data_fim)",
    "CREATE INDEX IF NOT EXISTS idx_carros_status ON carros(status)",
    "CREATE INDEX IF NOT EXISTS idx_clientes_cpf ON clientes(cpf)",
    "CREATE INDEX IF NOT EXISTS idx_multas_reserva_id ON multas(reserva_id)",
    "CREATE INDEX IF NOT EXISTS idx_multas_status ON multas(status)",
    "CREATE INDEX IF NOT EXISTS idx_multas_data_multa ON multas(data_multa)"
]

def init_db_production() -> bool:
    """
    Inicializa o banco de dados criando as tabelas necessárias
    
    Returns:
        bool: True se a inicialização for bem-sucedida, False caso contrário
    """
    logger.info("Iniciando inicialização do banco de dados...")
    logger.debug(f"Configurações do banco: { {k: '***' if 'pass' in k.lower() else v for k, v in DB_CONFIG.items()} }")
    
    # Verifica se o diretório de logs existe
    os.makedirs('logs', exist_ok=True)
    
    try:
        st.info("🔄 Verificando estrutura do banco de dados...")
        logger.info("Verificando estrutura do banco de dados...")
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verificar se todas as tabelas existem
            all_tables_exist = all(table_exists(conn, table) for table in TABLES.keys())
            
            if all_tables_exist:
                msg = "Estrutura do banco verificada com sucesso!"
                logger.info(msg)
                st.success(f"✅ {msg}")
                
                # Atualiza o esquema se necessário
                update_database_schema(conn)
                return True
                
            msg = "Criando tabelas no banco de dados..."
            logger.info(msg)
            st.info(f"🔄 {msg}")
            
            # Criar extensão UUID se não existir
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
                logger.info("Extensão 'uuid-ossp' verificada/criada")
            except Exception as e:
                logger.warning(f"Não foi possível criar a extensão 'uuid-ossp': {e}")
            
            # Criar as tabelas
            for table_name, create_table_sql in TABLES.items():
                try:
                    cursor.execute(create_table_sql)
                    msg = f"Tabela '{table_name}' criada/verificada"
                    logger.info(msg)
                    st.success(f"✅ {msg}")
                except Exception as e:
                    logger.error(f"Erro ao criar tabela {table_name}: {e}")
                    raise
            
            # Criar índices
            for index_sql in INDEXES:
                try:
                    cursor.execute(index_sql)
                    logger.debug(f"Índice criado: {index_sql[:100]}...")
                except Exception as e:
                    logger.warning(f"Erro ao criar índice: {e}")
            
            # Criar função para atualizar o timestamp
            try:
                cursor.execute("""
                    CREATE OR REPLACE FUNCTION update_updated_at_column()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = NOW();
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """)
                logger.info("Função update_updated_at_column criada/atualizada")
            except Exception as e:
                logger.error(f"Erro ao criar função update_updated_at_column: {e}")
                raise
            
            # Criar triggers para atualizar o campo updated_at
            for table in TABLES.keys():
                try:
                    cursor.execute(f"""
                        DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};
                        CREATE TRIGGER update_{table}_updated_at
                        BEFORE UPDATE ON {table}
                        FOR EACH ROW
                        EXECUTE FUNCTION update_updated_at_column();
                    """)
                    logger.debug(f"Trigger para atualização de {table} criada")
                except Exception as e:
                    logger.error(f"Erro ao criar trigger para {table}: {e}")
                    raise
            
            conn.commit()
            msg = "Banco de dados inicializado com sucesso!"
            logger.info(msg)
            st.success(f"✅ {msg}")
            return True
            
        except Exception as e:
            logger.critical(f"Erro crítico durante a inicialização: {str(e)}", exc_info=True)
            if 'conn' in locals() and conn:
                conn.rollback()
            raise
            
        finally:
            if conn:
                try:
                    conn.close()
                    logger.info("Conexão com o banco de dados fechada")
                except Exception as e:
                    logger.error(f"Erro ao fechar conexão: {e}")
                
    except Exception as e:
        msg = f"❌ Erro na inicialização do banco: {str(e)}"
        logger.critical(msg, exc_info=True)
        st.error(msg)
        return False

def update_database_schema(conn) -> None:
    """
    Atualiza o esquema do banco de dados com novas colunas ou alterações necessárias
    
    Args:
        conn: Conexão com o banco de dados
    """
    logger.info("Iniciando verificação de atualizações do esquema do banco...")
    
    # Definição das atualizações de esquema
    SCHEMA_UPDATES = {
        'carros': {
            'km_troca_oleo': 'INTEGER DEFAULT 10000',
            'data_prox_manutencao': 'DATE',
            'observacoes': 'TEXT',
            'ativo': 'BOOLEAN DEFAULT true'
        },
        'clientes': {
            'data_nascimento': 'DATE',
            'email': 'TEXT',
            'endereco_completo': 'TEXT',
            'ativo': 'BOOLEAN DEFAULT true'
        },
        'reservas': {
            'valor_total': 'DECIMAL(10,2)',
            'status_pagamento': 'TEXT DEFAULT \'Pendente\'',
            'observacoes': 'TEXT',
            'km_inicial': 'INTEGER',
            'km_final': 'INTEGER',
            'combustivel_inicial': 'INTEGER',
            'combustivel_final': 'INTEGER'
        }
    }
    
    try:
        cursor = conn.cursor()
        updates_applied = False
        
        # Verificar e adicionar colunas ausentes
        for table, columns in SCHEMA_UPDATES.items():
            if not table_exists(conn, table):
                logger.warning(f"Tabela {table} não encontrada. Pulando atualizações...")
                continue
                
            for column, column_type in columns.items():
                try:
                    if not column_exists(conn, table, column):
                        sql = f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"
                        logger.info(f"Aplicando alteração: {sql}")
                        cursor.execute(sql)
                        
                        msg = f"Coluna '{column}' adicionada à tabela '{table}'"
                        logger.info(msg)
                        st.success(f"✅ {msg}")
                        updates_applied = True
                except Exception as e:
                    logger.error(f"Erro ao adicionar coluna {column} na tabela {table}: {e}")
                    raise
        
        if not updates_applied:
            logger.info("Nenhuma atualização de esquema necessária")
            st.success("✅ Esquema do banco de dados está atualizado")
        add_column_if_not_exists('reservas', 'pagamento_parcial_entrega', 'DECIMAL(10,2) DEFAULT 0.0')
        add_column_if_not_exists('reservas', 'valor_restante', 'DECIMAL(10,2) DEFAULT 0.0')
        add_column_if_not_exists('reservas', 'created_at', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()')
        add_column_if_not_exists('reservas', 'updated_at', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()')
        
        # Criar tabela de multas se não existir
        if not table_exists('multas'):
            cursor.execute(TABLES['multas'])
            st.success("✅ Tabela 'multas' criada com sucesso!")
            
            # Criar índices para a tabela de multas
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_multas_reserva_id ON multas(reserva_id);
                CREATE INDEX IF NOT EXISTS idx_multas_status ON multas(status);
                CREATE INDEX IF NOT EXISTS idx_multas_data_multa ON multas(data_multa);
            """)
        else:
            # Adicionar coluna local_infracao se não existir
            add_column_if_not_exists('multas', 'local_infracao', 'TEXT')
        
        # Criar índices se não existirem
        for index_sql in INDEXES:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                st.warning(f"⚠️ Não foi possível criar o índice: {e}")
        
        conn.commit()
        st.success("✅ Esquema do banco de dados atualizado com sucesso!")
        
    except Exception as e:
        st.error(f"❌ Erro ao atualizar o esquema do banco: {e}")
        raise

def check_db_health() -> Dict[str, Any]:
    """
    Verifica a saúde do banco de dados e retorna estatísticas
    
    Returns:
        Dict com informações sobre a saúde do banco
    """
    try:
        from db_utils import check_db_connection
        health = check_db_connection()
        
        if not health.get('healthy', False):
            return health
            
        # Adicionar verificações adicionais de saúde
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Verificar tabelas faltantes
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = ANY(%s)
            """, (list(TABLES.keys()),))
            
            existing_tables = {row[0] for row in cursor.fetchall()}
            missing_tables = set(TABLES.keys()) - existing_tables
            
            health['missing_tables'] = list(missing_tables)
            health['table_count'] = {}
            
            # Contar registros em cada tabela
            for table in existing_tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                health['table_count'][table] = cursor.fetchone()[0]
                
            return health
            
        finally:
            if conn:
                conn.close()
                
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e)
        }

