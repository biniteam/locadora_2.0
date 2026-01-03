"""
Sistema de Autenticação para Locadora Strealit
Autenticação com Supabase
"""
import os
import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Tuple, Any, List
from supabase import create_client, Client

# Configurações do Supabase
# Get Supabase URL and Key from Streamlit secrets
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

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

class SupabaseAuthManager:
    """Gerenciador de autenticação e controle de acesso com Supabase"""

    def __init__(self):
        self.supabase = self._init_supabase()
        self._init_auth_db()

    def _init_supabase(self) -> Client:
        """Inicializa o cliente do Supabase"""
        print(f"Iniciando conexão com o Supabase...")
        #print(f"URL: {SUPABASE_URL}")
        #print(f"Chave: {SUPABASE_KEY[:10]}...")  # Mostra apenas os primeiros caracteres da chave por segurança
        
        try:
            print("Criando cliente Supabase...")
            client = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("Cliente Supabase criado com sucesso!")
            return client
        except Exception as e:
            error_msg = f"Erro ao conectar ao Supabase: {str(e)}"
            print(error_msg)
            st.error("Erro de conexão com o servidor de autenticação. Por favor, tente novamente.")
            st.stop()
            raise Exception(error_msg)

    def _init_auth_db(self):
        """Inicializa tabelas adicionais no Supabase se necessário"""
        try:
            # Verifica se a tabela de perfis de usuário existe
            self.supabase.table('profiles').select('*').limit(1).execute()
        except Exception as e:
            st.error(f"Erro ao verificar tabelas de autenticação: {e}")
            # Cria a tabela de perfis se não existir
            self._create_profiles_table()

    def _create_profiles_table(self):
        """Cria a tabela de perfis se não existir"""
        try:
            self.supabase.rpc('''
                CREATE TABLE IF NOT EXISTS profiles (
                    id UUID REFERENCES auth.users ON DELETE CASCADE,
                    email TEXT NOT NULL,
                    full_name TEXT,
                    role TEXT DEFAULT 'viewer',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_login TIMESTAMP WITH TIME ZONE,
                    PRIMARY KEY (id)
                );
            ''')
        except Exception as e:
            st.error(f"Erro ao criar tabela de perfis: {e}")

    def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Busca perfil do usuário"""
        try:
            response = self.supabase.table('profiles').select('*').eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            st.error(f"Erro ao buscar perfil: {e}")
            return None

    def _update_user_profile(self, user_id: str, **updates) -> bool:
        """Atualiza perfil do usuário"""
        try:
            self.supabase.table('profiles').update(updates).eq('id', user_id).execute()
            return True
        except Exception as e:
            st.error(f"Erro ao atualizar perfil: {e}")
            return False

    def _log_action(self, user_id: str, action: str, resource: str, details: str):
        """Registra ação na tabela de logs de auditoria"""
        try:
            log_data = {
                'user_id': user_id,
                'action': action,
                'resource': resource,
                'details': details,
                'ip_address': st.experimental_get_forward_headers().get('X-Forwarded-For', '')
            }
            self.supabase.table('audit_logs').insert(log_data).execute()
        except Exception as e:
            st.error(f"Erro ao registrar ação de auditoria: {e}")

    def create_user(self, username: str, password: str, role: str = 'employee',
                   full_name: str = '', email: str = '') -> Tuple[bool, str]:
        """
        Cria um novo usuário e seu perfil no Supabase
        
        Args:
            username: Nome de usuário único
            password: Senha do usuário (mínimo 6 caracteres)
            role: Função do usuário (admin, manager, employee, viewer)
            full_name: Nome completo do usuário
            email: E-mail do usuário (deve ser único)
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        if not email or '@' not in email:
            return False, "E-mail inválido"
            
        if len(password) < 6:
            return False, "A senha deve ter pelo menos 6 caracteres"
            
        if role not in ['admin', 'manager', 'employee', 'viewer']:
            return False, "Função de usuário inválida"
            
        try:
            print(f"[DEBUG] Criando usuário: {username} ({email})")
            
            # 1. Criar usuário no Supabase Auth
            print("[DEBUG] Criando conta de autenticação...")
            auth_response = self.supabase.auth.sign_up({
                'email': email,
                'password': password,
                'options': {
                    'data': {
                        'username': username,
                        'full_name': full_name or username,
                        'role': role
                    }
                }
            })
            
            if not hasattr(auth_response, 'user') or not auth_response.user:
                return False, "Falha ao criar usuário: resposta inválida do servidor"
            
            user = auth_response.user
            user_id = str(user.id)  # Garantir que é uma string
            print(f"[DEBUG] Usuário criado com ID: {user_id}")
            
            # 2. Criar perfil na tabela profiles
            print("[DEBUG] Criando perfil do usuário...")
            
            # Verificar se o ID é um UUID válido
            import uuid
            try:
                uuid_obj = uuid.UUID(user_id, version=4)
                print(f"[DEBUG] UUID válido: {user_id}")
            except ValueError:
                error_msg = f"ID de usuário inválido (não é um UUID): {user_id}"
                print(f"[ERRO] {error_msg}")
                return False, error_msg
            
            # Preparar dados do perfil
            profile_data = {
                'id': user_id,  # Usar o ID diretamente como chave primária
                'email': email,
                'full_name': full_name or username,
                'role': role
            }
            
            print(f"[DEBUG] Dados do perfil: {profile_data}")
            
            try:
                # Usar insert com retorno explícito para debug
                result = (
                    self.supabase
                    .table('profiles')
                    .insert(profile_data)
                    .execute()
                )
                print(f"[DEBUG] Resultado da inserção: {result}")
                
                # Verifica se a inserção foi bem-sucedida
                if hasattr(result, 'data') and result.data:
                    print(f"[DEBUG] Perfil criado com sucesso: {result.data}")
                else:
                    error_msg = "Resposta inesperada ao criar perfil"
                    print(f"[ERRO] {error_msg}")
                    # Tenta remover o usuário de autenticação em caso de falha
                    try:
                        self.supabase.auth.admin.delete_user(user_id)
                    except Exception as delete_error:
                        print(f"[AVISO] Não foi possível limpar usuário após falha: {str(delete_error)}")
                    return False, error_msg
                    
            except Exception as e:
                error_msg = f"Erro ao criar perfil: {str(e)}"
                print(f"[ERRO] {error_msg}")
                # Tenta remover o usuário de autenticação em caso de falha
                try:
                    self.supabase.auth.admin.delete_user(user_id)
                except Exception as delete_error:
                    print(f"[AVISO] Não foi possível limpar usuário após falha: {str(delete_error)}")
                return False, error_msg
            
            print(f"[DEBUG] Perfil criado com sucesso para o usuário {user_id}")
            return True, f"Usuário {username} criado com sucesso!"
            
        except Exception as e:
            error_msg = str(e)
            print(f"[ERRO] Falha na criação do usuário: {error_msg}")
            
            # Tenta obter mais detalhes do erro
            if hasattr(e, 'args') and e.args and isinstance(e.args[0], dict):
                error_details = e.args[0]
                if 'message' in error_details:
                    error_msg = error_details['message']
                elif 'error' in error_details:
                    error_msg = error_details['error']
            
            return False, f"Erro ao criar usuário: {error_msg}"

    def sign_in(self, email: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """Autentica usuário usando Supabase Auth e retorna dados do perfil"""
        print(f"\n=== Tentando autenticar usuário: {email} ===")
        try:
            print("Iniciando autenticação no Supabase...")
            # Autentica no Supabase
            auth_response = self.supabase.auth.sign_in_with_password({
                'email': email,
                'password': password
            })
            print("Resposta da autenticação recebida")

            if not auth_response.user:
                print("Falha na autenticação: Nenhum usuário retornado")
                return False, {"error": "Credenciais inválidas"}

            print(f"Usuário autenticado: {auth_response.user.email}")
            print("Obtendo perfil do usuário...")
            
            # Obtém o perfil do usuário
            profile = self._get_user_profile(auth_response.user.id)
            if not profile:
                print("Erro: Perfil do usuário não encontrado")
                return False, {"error": "Perfil do usuário não encontrado"}

            print(f"Perfil obtido: {profile}")
            print("Atualizando último login...")
            
            # Atualiza último login
            self._update_user_profile(
                auth_response.user.id,
                last_login=datetime.now().isoformat()
            )

            # Retorna dados do usuário
            user_data = {
                'id': auth_response.user.id,
                'email': auth_response.user.email,
                'role': profile.get('role', 'viewer'),
                'full_name': profile.get('full_name', ''),
                'is_active': True,
                'session': auth_response.session.dict() if hasattr(auth_response, 'session') else None
            }

            print(f"Dados do usuário preparados: {user_data}")
            return True, user_data

        except Exception as e:
            error_msg = str(e)
            print(f"Erro durante a autenticação: {error_msg}")
            if 'Invalid login credentials' in error_msg:
                return False, {"error": "Email ou senha inválidos"}
            return False, {"error": f"Erro na autenticação: {error_msg}"}

    def get_current_user(self) -> Optional[Dict]:
        """Obtém usuário a partir da sessão atual do Supabase"""
        try:
            # Obtém a sessão atual
            session = self.supabase.auth.get_session()
            if not session:
                return None

            # Obtém o perfil do usuário
            profile = self._get_user_profile(session.user.id)
            if not profile:
                return None

            return {
                'id': session.user.id,
                'email': session.user.email,
                'role': profile.get('role', 'viewer'),
                'full_name': profile.get('full_name', ''),
                'is_active': True,
                'session': session.dict() if hasattr(session, 'dict') else None
            }
        except Exception as e:
            st.error(f"Erro ao obter usuário da sessão: {e}")
            return None

    def sign_out(self):
        """Encerra a sessão do usuário no Supabase"""
        try:
            self.supabase.auth.sign_out()
        except Exception as e:
            st.error(f"Erro ao fazer logout: {e}")

    def reset_password(self, email: str) -> Tuple[bool, str]:
        """Solicita redefinição de senha"""
        try:
            self.supabase.auth.reset_password_email(email)
            return True, "Email de redefinição de senha enviado com sucesso"
        except Exception as e:
            return False, f"Erro ao solicitar redefinição de senha: {str(e)}"

    def update_password(self, new_password: str) -> Tuple[bool, str]:
        """Atualiza a senha do usuário autenticado"""
        try:
            user = self.get_current_user()
            if not user:
                return False, "Nenhum usuário autenticado"

            self.supabase.auth.update_user({'password': new_password})
            return True, "Senha atualizada com sucesso"
        except Exception as e:
            return False, f"Erro ao atualizar senha: {str(e)}"

    def get_users(self) -> List[Dict]:
        """
        Retorna uma lista de todos os usuários cadastrados no sistema
        
        Returns:
            List[Dict]: Lista de dicionários contendo informações dos usuários
        """
        try:
            # Busca todos os perfis de usuário
            response = self.supabase.table('profiles').select('*').execute()
            
            if not response.data:
                return []
                
            # Formata os dados para retorno
            users_list = []
            for profile in response.data:
                users_list.append({
                    'id': str(profile.get('id', '')),
                    'email': profile.get('email', ''),
                    'role': profile.get('role', 'viewer'),
                    'full_name': profile.get('full_name', ''),
                    'created_at': profile.get('created_at'),
                    'last_login': profile.get('last_login')
                })
                
            return users_list
            
        except Exception as e:
            st.error(f"Erro ao listar usuários: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return []

    def has_permission(self, user: Dict, permission: str) -> bool:
        """Verifica se o usuário tem a permissão necessária"""
        if not user or 'role' not in user:
            return False
        
        role = user['role']
        if role not in ROLE_PERMISSIONS:
            return False
            
        return permission in ROLE_PERMISSIONS[role]

# Instância global do gerenciador de autenticação
auth_manager = SupabaseAuthManager()
