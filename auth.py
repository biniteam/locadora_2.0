"""
Sistema de Autenticação para Locadora Strealit
Inclui hash de senha, controle de sessão e níveis de usuário
"""
import streamlit as st
import bcrypt
import hashlib
import psycopg2 
from datetime import datetime, timedelta
import secrets
from typing import Optional, Dict, Tuple
from db_utils import get_db_connection, run_query, run_query_dataframe


# Constantes de nível de usuário
USER_ROLES = {
    'admin': 'Administrador',
    'manager': 'Gerente',
    'employee': 'Funcionário',
    'viewer': 'Visualizador'
}

# Permissões por nível
ROLE_PERMISSIONS = {
    'admin': ['read', 'write', 'delete', 'manage_users', 'view_reports', 'backup'],
    'manager': ['read', 'write', 'delete', 'view_reports', 'backup'],
    'employee': ['read', 'write', 'view_reports'],
    'viewer': ['read']
}

class AuthManager:
    """Gerenciador de autenticação e controle de acesso"""

    def __init__(self):
        self._init_auth_db()

    def _init_auth_db(self):
        """Inicializa tabelas de autenticação no banco PostgreSQL"""
        try:
            # Tabela de usuários
            run_query('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'employee',
                    full_name TEXT,
                    email TEXT,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP
                )
            ''')

            # Tabela de sessões
            run_query('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')

            # Tabela de logs de auditoria
            run_query('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    action TEXT,
                    resource TEXT,
                    details TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            
            # Tabela de perfis de usuário
            run_query('''
                CREATE TABLE IF NOT EXISTS profiles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL,
                    full_name TEXT,
                    email TEXT,
                    role TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')

            # Criar usuário admin padrão se não existir
            if not self._user_exists('admin'):
                self.create_user('admin', 'admin123', 'admin', 'Administrador do Sistema', 'admin@locadora.com')

        except Exception as e:
            st.error(f"Erro ao inicializar tabelas de autenticação: {e}")

    def _user_exists(self, username: str) -> bool:
        """Verifica se usuário existe"""
        result = run_query("SELECT id FROM users WHERE username = %s", (username,), fetch=True)
        return not (isinstance(result, str) or result.empty)

    def _hash_password(self, password: str) -> str:
        """Gera hash da senha usando bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verifica senha contra hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        
    def get_current_user(self):
        """Retorna o usuário atualmente logado"""
        return st.session_state.get('user')

    def _generate_session_id(self) -> str:
        """Gera ID único para sessão"""
        return secrets.token_urlsafe(32)

    def _is_account_locked(self, user_id: int) -> bool:
        """Verifica se conta está bloqueada"""
        result = run_query("SELECT locked_until FROM users WHERE id = %s", (user_id,), fetch=True)
        if isinstance(result, str):
            return False
        if not result.empty and result.iloc[0]['locked_until']:
            locked_until = result.iloc[0]['locked_until']
            return locked_until > datetime.now()
        return False

    def _increment_login_attempts(self, user_id: int):
        """Incrementa tentativas de login"""
        result = run_query("SELECT login_attempts FROM users WHERE id = %s", (user_id,), fetch=True)
        if isinstance(result, str):
            return
        attempts = result.iloc[0]['login_attempts'] or 0 if not result.empty else 0
        attempts += 1

        # Bloquear conta após 5 tentativas
        locked_until = None
        if attempts >= 5:
            locked_until = datetime.now() + timedelta(minutes=30)

        run_query("""
            UPDATE users
            SET login_attempts = %s, locked_until = %s
            WHERE id = %s
        """, (attempts, locked_until, user_id))

    def _reset_login_attempts(self, user_id: int):
        """Reseta tentativas de login após login bem-sucedido"""
        run_query("""
            UPDATE users
            SET login_attempts = 0, locked_until = NULL, last_login = %s
            WHERE id = %s
        """, (datetime.now(), user_id))

    def _get_table_schema(self, conn, table_name):
        """Obtém o esquema de uma tabela"""
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name, data_type, column_default, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position;
                """, (table_name,))
                return cursor.fetchall()
        except Exception as e:
            print(f"[ERRO] Falha ao obter esquema da tabela {table_name}: {e}")
            return []

    def create_user(self, username: str, password: str, role: str = 'employee',
                   full_name: str = '', email: str = '') -> Tuple[bool, str]:
        """Cria novo usuário e seu perfil"""
        if role not in USER_ROLES:
            return False, f"Nível de usuário inválido: {role}"

        if len(password) < 6:
            return False, "A senha deve ter pelo menos 6 caracteres"

        conn = None
        try:
            print(f"[DEBUG] Iniciando criação do usuário: {username}")
            conn = get_db_connection()
            if not conn:
                return False, "Erro ao conectar ao banco de dados"
            
            # Log do esquema das tabelas
            print("\n[DEBUG] Esquema da tabela 'users':")
            users_schema = self._get_table_schema(conn, 'users')
            for col in users_schema:
                print(f"  - {col[0]}: {col[1]} (Default: {col[2]}, Nullable: {col[3]})")
                
            print("\n[DEBUG] Esquema da tabela 'profiles':")
            profiles_schema = self._get_table_schema(conn, 'profiles')
            for col in profiles_schema:
                print(f"  - {col[0]}: {col[1]} (Default: {col[2]}, Nullable: {col[3]})")
                
            with conn.cursor() as cursor:
                # Verificar se o usuário já existe
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    return False, f"O nome de usuário '{username}' já está em uso"
                
                # Inserir usuário
                hashed_password = self._hash_password(password)
                print(f"[DEBUG] Inserindo usuário no banco de dados")
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role, full_name, email, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (username, hashed_password, role, full_name, email, True))
                
                result = cursor.fetchone()
                if not result:
                    raise Exception("Falha ao obter o ID do usuário após a inserção")
                    
                user_id = result[0]
                print(f"[DEBUG] Usuário criado com ID: {user_id}")
                
                # Criar perfil do usuário
                print(f"[DEBUG] Criando perfil para o usuário ID: {user_id}")
                cursor.execute("""
                    INSERT INTO profiles (user_id, full_name, email, role)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, full_name or username, email or f"{username}@locadora.com", role))
                
                conn.commit()
                print(f"[DEBUG] Commit realizado com sucesso")
                
                # Log de auditoria
                self._log_action(user_id, 'user_created', 'users', f'Usuário {username} criado')
                
                return True, f"Usuário {username} criado com sucesso com ID {user_id}"

        except Exception as e:
            error_msg = f"Erro ao criar usuário: {str(e)}"
            print(f"[ERRO] {error_msg}")
            if conn:
                conn.rollback()
            return False, error_msg
            
        finally:
            if conn:
                conn.close()

    def authenticate(self, username: str, password: str, ip_address: str = '',
                    user_agent: str = '') -> Tuple[bool, Optional[Dict]]:
        """Autentica usuário e retorna dados se válido"""
        result = run_query("""
            SELECT id, password_hash, role, full_name, email, is_active, locked_until
            FROM users WHERE username = %s
        """, (username,), fetch=True)

        # Verificar se houve erro na query
        if isinstance(result, str):
            return False, {"error": f"Erro no banco de dados: {result}"}

        if result.empty:
            return False, None

        user = result.iloc[0]
        user_id, password_hash, role, full_name, email, is_active, locked_until = (
            user['id'], user['password_hash'], user['role'], user['full_name'],
            user['email'], user['is_active'], user['locked_until']
        )

        # Verificar se conta está ativa
        if not is_active:
            return False, None

        # Verificar se conta está bloqueada
        if locked_until and locked_until > datetime.now():
            minutes_left = int((locked_until - datetime.now()).total_seconds() / 60)
            return False, {"error": f"Conta bloqueada. Tente novamente em {minutes_left} minutos."}

        # Verificar senha
        if not self._verify_password(password, password_hash):
            self._increment_login_attempts(user_id)
            return False, {"error": "Usuário ou senha incorretos"}

        # Login bem-sucedido - resetar tentativas
        self._reset_login_attempts(user_id)

        # Criar sessão
        session_id = self._generate_session_id()
        expires_at = datetime.now() + timedelta(hours=8)  # Sessão válida por 8 horas

        # Garantir que user_id seja um int Python (não numpy.int64)
        user_id_int = int(user_id)

        session_result = run_query("""
            INSERT INTO sessions (session_id, user_id, expires_at, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s)
        """, (session_id, user_id_int, expires_at, ip_address, user_agent))

        # Verificar se a sessão foi criada com sucesso
        if isinstance(session_result, str):
            return False, {"error": f"Erro ao criar sessão: {session_result}"}

        # Log de auditoria
        self._log_action(user_id, 'login', 'auth', f'Login bem-sucedido para {username}')

        user_data = {
            'id': user_id,
            'username': username,
            'role': role,
            'full_name': full_name,
            'email': email,
            'session_id': session_id,
            'permissions': ROLE_PERMISSIONS.get(role, [])
        }

        return True, user_data

    def validate_session(self, session_id: str) -> Optional[Dict]:
        """Valida sessão ativa"""
        result = run_query("""
            SELECT s.user_id, u.username, u.role, u.full_name, u.email, s.expires_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_id = %s AND u.is_active = true
        """, (session_id,), fetch=True)

        if isinstance(result, str) or result.empty:
            return None

        row = result.iloc[0]
        user_id, username, role, full_name, email, expires_at = (
            row['user_id'], row['username'], row['role'], row['full_name'],
            row['email'], row['expires_at']
        )

        # Verificar se sessão expirou
        if expires_at < datetime.now():
            self.logout(session_id)
            return None

        return {
            'id': user_id,
            'username': username,
            'role': role,
            'full_name': full_name,
            'email': email,
            'session_id': session_id,
            'permissions': ROLE_PERMISSIONS.get(role, [])
        }

    def logout(self, session_id: str):
        """Encerra sessão"""
        run_query("DELETE FROM sessions WHERE session_id = %s", (session_id,))

    def _log_action(self, user_id: int, action: str, resource: str, details: str, ip_address: str = ''):
        """Registra ação no log de auditoria"""
        try:
            run_query("""
                INSERT INTO audit_logs (user_id, action, resource, details, ip_address)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, action, resource, details, ip_address))
        except Exception as e:
            logging.error(f"Failed to log action: {e}")  # Não falhar se log não funcionar

    def get_users(self) -> list:
        """Retorna lista de usuários"""
        result = run_query("""
            SELECT id, username, role, full_name, email, is_active, created_at, last_login
            FROM users ORDER BY username
        """, fetch=True)

        if result.empty:
            return []

        return result.to_dict('records')

    def update_user(self, user_id: int, updates: Dict) -> Tuple[bool, str]:
        """Atualiza dados do usuário"""
        try:
            update_fields = []
            values = []

            if 'password' in updates:
                if len(updates['password']) < 6:
                    return False, "A senha deve ter pelo menos 6 caracteres"
                update_fields.append("password_hash = %s")
                values.append(self._hash_password(updates['password']))

            if 'role' in updates:
                if updates['role'] not in USER_ROLES:
                    return False, f"Nível de usuário inválido: {updates['role']}"
                update_fields.append("role = %s")
                values.append(updates['role'])

            if 'full_name' in updates:
                update_fields.append("full_name = %s")
                values.append(updates['full_name'])

            if 'email' in updates:
                update_fields.append("email = %s")
                values.append(updates['email'])

            if 'is_active' in updates:
                update_fields.append("is_active = %s")
                values.append(updates['is_active'])

            if not update_fields:
                return False, "Nenhum campo para atualizar"

            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
            values.append(user_id)

            result = run_query(query, tuple(values))
            if result:
                return False, f"Erro ao atualizar usuário: {result}"

            return True, "Usuário atualizado com sucesso"

        except Exception as e:
            return False, f"Erro ao atualizar usuário: {str(e)}"

    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        """Remove usuário (desativa)"""
        try:
            # Verificar se é o último admin
            result = run_query("SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = true AND id != %s", (user_id,), fetch=True)
            if isinstance(result, str):
                return False, f"Erro ao verificar administradores: {result}"
            admin_count = result.iloc[0, 0] if not result.empty else 0

            if admin_count == 0:
                return False, "Não é possível remover o último administrador"

            # Desativar usuário ao invés de deletar
            result = run_query("UPDATE users SET is_active = false WHERE id = %s", (user_id,))
            if result:
                return False, f"Erro ao desativar usuário: {result}"

            return True, "Usuário desativado com sucesso"

        except Exception as e:
            return False, f"Erro ao remover usuário: {str(e)}"

    def get_audit_logs(self, limit: int = 100) -> list:
        """Retorna logs de auditoria"""
        result = run_query("""
            SELECT a.timestamp, u.username, a.action, a.resource, a.details, a.ip_address
            FROM audit_logs a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.timestamp DESC LIMIT %s
        """, (limit,), fetch=True)

        if isinstance(result, str) or result.empty:
            return []

        return result.to_dict('records')

    def check_permission(self, user_permissions: list, required_permission: str) -> bool:
        """Verifica se usuário tem permissão"""
        return required_permission in user_permissions

# Instância global do gerenciador de autenticação
auth_manager = AuthManager()

def login_page():
    """Página de login"""
    # Estilos CSS personalizados
    st.markdown("""
        <style>
            .login-container {
                max-width: 500px;
                padding: 2rem;
                margin: 0 auto;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                background-color: #ffffff;
            }
            .stTextInput>div>div>input {
                padding: 0.5rem;
            }
            .stButton>button {
                width: 100%;
                padding: 0.5rem;
                font-weight: 600;
            }
            .header {
                text-align: center;
                margin-bottom: 2rem;
            }
            .header h1 {
                color: #1E88E5;
                margin-bottom: 0.5rem;
            }
            .header p {
                color: #666;
                margin-top: 0;
            }
            .footer {
                text-align: center;
                margin-top: 2rem;
                color: #666;
                font-size: 0.9rem;
            }
        </style>
    """, unsafe_allow_html=True)

    # Verificar se já está logado
    if 'user' in st.session_state and st.session_state.user:
        user = auth_manager.validate_session(st.session_state.user['session_id'])
        if user:
            st.success(f"✅ Bem-vindo de volta, {user['full_name']}!")
            st.rerun()
            return

    # Container principal do login
    with st.container():
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col2:
            st.markdown("""
                <div class="login-container">
                    <div class="header">
                        <h1>🔐 Locadora Strealit</h1>
                        <p>Faça login para continuar</p>
                    </div>
            """, unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("👤 Nome de usuário", key="login_username", 
                                       placeholder="Digite seu usuário")
                password = st.text_input("🔑 Senha", type="password", key="login_password",
                                       placeholder="Digite sua senha")
                
                col_btn = st.columns([1, 2, 1])
                with col_btn[1]:
                    submitted = st.form_submit_button("Entrar", type="primary", width='stretch')
                
                if submitted:
                    if not username or not password:
                        st.error("❌ Por favor, preencha todos os campos")
                        st.stop()
                    
                    # Obter IP (simulado para desenvolvimento)
                    ip_address = "127.0.0.1"  # Em produção, use request.remote_addr
                    
                    success, result = auth_manager.authenticate(username, password, ip_address)
                    
                    if success:
                        st.session_state.user = result
                        st.success(f"✅ Login realizado com sucesso!")
                        st.balloons()
                        st.rerun()
                    else:
                        error_msg = result.get('error', 'Usuário ou senha incorretos') if isinstance(result, dict) else 'Usuário ou senha incorretos'
                        st.error(f"❌ {error_msg}")
            
            st.markdown("""
                <div class="footer">
                    <p>Problemas para acessar? Entre em contato com o suporte</p>
                </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Apenas em desenvolvimento
            if st.secrets.get("ENVIRONMENT") == "development":
                st.info("Modo Desenvolvimento Ativo")
                st.markdown("**Usuário padrão:** admin / admin123")

def logout():
    """Faz logout do usuário"""
    try:
        if 'user' in st.session_state and st.session_state.user and 'session_id' in st.session_state.user:
            auth_manager.logout(st.session_state.user['session_id'])
        st.session_state.user = None
        st.success("✅ Logout realizado com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao fazer logout: {str(e)}")

def require_login():
    """Verifica se usuário está logado e redireciona se necessário"""
    # Check if using Supabase auth
    if 'authenticated' in st.session_state and st.session_state.authenticated:
        return True
        
    # Fall back to session-based auth
    if 'user' not in st.session_state or not st.session_state.user:
        login_page()
        return False

    # Check if using Supabase-style user object (no session_id)
    if 'id' in st.session_state.user and 'session_id' not in st.session_state.user:
        return True

    # For session-based auth, check session_id
    if 'session_id' not in st.session_state.user:
        st.session_state.user = None
        login_page()
        return False

    # Validate session for session-based auth
    user = auth_manager.validate_session(st.session_state.user['session_id'])
    if not user:
        st.session_state.user = None
        login_page()
        return False

    # Update session data
    st.session_state.user = user
    return True

def check_permission(required_permission: str) -> bool:
    """Verifica permissão do usuário atual"""
    user = auth_manager.get_current_user()
    if not user:
        return False
    # Verifica se o usuário é admin (acesso total)
    if user.get('role') == 'admin':
        return True
    # Adicione outras verificações de permissão conforme necessário
    return False
