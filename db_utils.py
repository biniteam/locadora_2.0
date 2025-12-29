"""
Módulo de utilitários para conexão com PostgreSQL
Centraliza todas as operações de banco de dados para facilitar manutenção
Utiliza exclusivamente PostgreSQL (produção e desenvolvimento)
"""
import psycopg2
import psycopg2.extras
import os
import streamlit as st
from typing import Optional, Any, Dict, List
import pandas as pd
import numpy as np


def get_db_connection():
    """
    Retorna uma conexão com o PostgreSQL
    Utiliza configuração do Streamlit secrets ou variáveis de ambiente
    """
    try:
        # Tentar obter configuração do Streamlit secrets
        if hasattr(st, 'secrets') and 'database' in st.secrets:
            db_config = st.secrets.database

            # Se tiver database_url, usar ela
            if 'database_url' in db_config:
                conn = psycopg2.connect(db_config['database_url'])
            else:
                # Usar configurações separadas
                conn = psycopg2.connect(
                    host=db_config.get('host'),
                    port=db_config.get('port', 5432),
                    database=db_config.get('database', 'postgres'),
                    user=db_config.get('user'),
                    password=db_config.get('password'),
                    sslmode=db_config.get('sslmode', 'require')
                )
        else:
            # Fallback para variáveis de ambiente (desenvolvimento)
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 5432)),
                database=os.getenv('DB_NAME', 'locadora_strealit'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', ''),
                sslmode=os.getenv('DB_SSLMODE', 'prefer')
            )

        return conn

    except Exception as e:
        st.error(f"Erro ao conectar ao PostgreSQL: {e}")
        raise


def run_query(query: str, params: tuple = (), fetch: bool = False) -> Any:
    """
    Executa uma query no PostgreSQL
    Args:
        query: Query SQL a ser executada
        params: Parâmetros para a query (prevenção de SQL injection)
        fetch: Se True, retorna os resultados como DataFrame
    Returns:
        DataFrame se fetch=True, lastrowid se INSERT, None se sucesso, str se erro
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Converter numpy types para tipos Python nativos
        params_converted = tuple(
            int(p) if hasattr(p, 'item') and isinstance(p.item(), (int, np.integer)) else
            float(p) if hasattr(p, 'item') and isinstance(p.item(), (float, np.floating)) else
            p
            for p in params
        )
        
        cursor.execute(query, params_converted)

        if fetch:
            records = cursor.fetchall()
            if records:
                # Converter para DataFrame
                data = [dict(record) for record in records]
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame()
            return df

        # Para INSERT/UPDATE/DELETE, fazer commit
        conn.commit()

        # Se for INSERT, retornar o ID gerado
        if query.strip().upper().startswith("INSERT"):
            # PostgreSQL usa RETURNING para obter ID
            if "RETURNING" in query.upper():
                result = cursor.fetchone()
                if result:
                    # RealDictCursor retorna dict, pega o primeiro valor
                    if isinstance(result, dict):
                        return list(result.values())[0]
                    else:
                        return result[0]
                return None
            else:
                return None

        return None

    except Exception as e:
        if conn:
            conn.rollback()
        return str(e)

    finally:
        if conn:
            conn.close()


def run_query_dataframe(query: str, params: tuple = ()) -> pd.DataFrame:
    """
    Executa uma query SELECT e retorna um DataFrame
    Retorna DataFrame vazio em caso de erro
    """
    try:
        result = run_query(query, params, fetch=True)
        if isinstance(result, pd.DataFrame):
            return result
        else:
            st.error(f"Consulta não retornou DataFrame: {result}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao executar consulta: {e}")
        return pd.DataFrame()


def table_exists(table_name: str) -> bool:
    """
    Verifica se uma tabela existe no banco
    """
    query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = %s
        );
    """
    result = run_query(query, (table_name,), fetch=True)
    return bool(result.iloc[0, 0]) if not result.empty else False


def column_exists(table_name: str, column_name: str) -> bool:
    """
    Verifica se uma coluna existe em uma tabela
    """
    query = """
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = %s
            AND column_name = %s
        );
    """
    result = run_query(query, (table_name, column_name), fetch=True)
    return bool(result.iloc[0, 0]) if not result.empty else False


def add_column_if_not_exists(table_name: str, column_name: str, column_definition: str):
    """
    Adiciona uma coluna a uma tabela se ela não existir
    """
    if not column_exists(table_name, column_name):
        query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition};"
        result = run_query(query)
        if isinstance(result, str):  # Se run_query retornar uma string, é uma mensagem de erro
            st.error(f"Erro ao adicionar coluna {column_name}: {result}")
            return False
        return True  # Se chegou aqui, a coluna foi adicionada com sucesso
    return True  # Se a coluna já existia, retorna True


def get_table_columns(table_name: str) -> List[str]:
    """
    Retorna lista de colunas de uma tabela
    """
    query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = %s
        ORDER BY ordinal_position;
    """
    result = run_query(query, (table_name,), fetch=True)
    return result['column_name'].tolist() if not result.empty else []


def check_db_connection() -> Dict[str, Any]:
    """
    Verifica a saúde da conexão com o banco de dados
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Teste básico de conectividade
        cursor.execute("SELECT 1 as test;")
        result = cursor.fetchone()
        if not result:
            raise Exception("Falha no teste básico de conectividade")

        # Verificar tabelas existentes
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]

        # Estatísticas básicas
        stats = {}
        for table in ['carros', 'clientes', 'reservas', 'users', 'sessions', 'audit_logs']:
            try:
                if table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[table] = cursor.fetchone()[0]
                else:
                    stats[table] = 0
            except Exception:
                stats[table] = 0

        conn.close()

        return {
            'healthy': True,
            'db_type': 'postgresql',
            'tables': tables,
            'stats': stats
        }

    except Exception as e:
        return {
            'healthy': False,
            'db_type': 'postgresql',
            'error': str(e)
        }


def get_db_type() -> str:
    """
    Retorna o tipo de banco de dados sendo usado
    """
    return "postgresql"
