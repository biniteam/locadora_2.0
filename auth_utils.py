# auth_utils.py
import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List, Union
from supabase import create_client

# Configurações de log
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_supabase_client():
    """Initialize and return Supabase client"""
    try:
        # Get Supabase URL and key from secrets
        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["key"]
        
        # Log the connection attempt (without sensitive data)
        logger.info(f"Conectando ao Supabase em: {supabase_url}")
        
        # Initialize the client
        client = create_client(supabase_url, supabase_key)
        return client
    except KeyError as e:
        logger.error(f"Erro nas credenciais do Supabase: {str(e)}")
        st.error("Erro de configuração: Credenciais do Supabase não encontradas.")
        raise
    except Exception as e:
        logger.error(f"Erro ao conectar ao Supabase: {str(e)}")
        st.error("Não foi possível conectar ao serviço de autenticação.")
        raise

def verify_credentials(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Verify user credentials with Supabase Auth"""
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_in_with_password({
            "email": username,
            "password": password
        })
        
        if not response.user:
            return None

        profile = get_user_profile(response.user.id)
        if not profile:
            logger.warning(f"Perfil não encontrado para o usuário: {username}")
            return None

        user_data = {
            "id": response.user.id,
            "email": response.user.email,
            "role": profile.get("role", "viewer"),
            "full_name": profile.get("full_name", ""),
            "is_active": profile.get("is_active", True)
        }
        logger.info(f"Login bem-sucedido para o usuário: {username}")
        return user_data
            
    except Exception as e:
        logger.error(f"Erro ao autenticar usuário {username}: {str(e)}")
        st.error("Erro ao tentar fazer login. Tente novamente mais tarde.")
    
    return None

def logout():
    """Log out the current user"""
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()
        logger.info("Usuário deslogado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao fazer logout: {str(e)}")
    finally:
        # Clear session state
        st.session_state.pop('user', None)
        st.session_state.authenticated = False
        st.session_state.pop('password_correct', None)

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current user from session"""
    return st.session_state.get("user")

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False)

def require_auth():
    """Redirect to login if not authenticated"""
    if not is_authenticated():
        st.warning(" Por favor, faça login para acessar esta página.")
        st.stop()

def require_role(required_roles: Union[str, List[str]]):
    """Check if user has required role"""
    require_auth()
    user = get_current_user()
    
    # Convert single role to list for consistent handling
    if isinstance(required_roles, str):
        required_roles = [required_roles]
    
    if not user or user.get("role") not in required_roles:
        logger.warning(f"Acesso negado para o usuário {user.get('email')} - Papel necessário: {required_roles}")
        st.error(" Acesso negado. Permissão insuficiente.")
        st.stop()

def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user profile from database"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("profiles").select("*").eq("id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
            
    except Exception as e:
        logger.error(f"Erro ao buscar perfil do usuário {user_id}: {str(e)}")
    
    return None

def get_user_profile_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user profile by email."""
    if not email:
        return None
    try:
        supabase = get_supabase_client()
        response = supabase.table("profiles").select("*").eq("email", email).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        logger.error(f"Erro ao buscar perfil pelo e-mail {email}: {str(e)}")
    return None

def create_user(email: str, password: str, full_name: str, role: str = "viewer") -> Tuple[bool, str]:
    """Cria um novo usuário com perfil no Supabase Auth"""
    try:
        supabase = get_supabase_client()
        
        # Verifica se o e-mail já está em uso
        existing_user = supabase.auth.admin.list_users().filter('email', 'eq', email).execute()
        if existing_user and len(existing_user.data) > 0:
            return False, "Este e-mail já está em uso."
        
        # Cria o usuário no Auth
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if not auth_response.user:
            return False, "Falha ao criar usuário no sistema de autenticação"
        
        # Cria o perfil do usuário
        profile_data = {
            "id": auth_response.user.id,
            "email": email,
            "full_name": full_name,
            "role": role.lower(),
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        profile_response = supabase.table("profiles").insert(profile_data).execute()
        
        if not profile_response.data:
            # Se falhar ao criar o perfil, tenta remover o usuário do Auth
            try:
                supabase.auth.admin.delete_user(auth_response.user.id)
            except Exception as e:
                logger.error(f"Erro ao remover usuário do Auth após falha: {str(e)}")
            return False, "Falha ao criar perfil do usuário"
        
        logger.info(f"Novo usuário criado com sucesso: {email} (Função: {role})")
        return True, "Usuário criado com sucesso"
        
                
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[ERRO CRÍTICO] {str(e)}")
        print(f"Detalhes completos:\n{error_details}")
    
    return False

def sync_user_from_oidc() -> Optional[Dict[str, Any]]:
    """
    Synchronize the Streamlit authenticated user (via st.login) with the Supabase profile.
    """
    user_info = getattr(st, "user", None)
    if not user_info or not user_info.is_logged_in:
        return None

    profile = get_user_profile_by_email(user_info.email)
    if not profile:
        st.error("Usuário autenticado não possui perfil cadastrado. Contate o administrador.")
        st.stop()

    if not profile.get("is_active", True):
        st.error("Esta conta está desativada. Entre em contato com o administrador.")
        st.logout()
        st.stop()

    synced_user = {
        "id": profile["id"],
        "email": profile.get("email", user_info.email),
        "full_name": profile.get("full_name", user_info.name or user_info.email),
        "role": profile.get("role", "viewer"),
        "is_active": profile.get("is_active", True),
    }

    st.session_state["user"] = synced_user
    st.session_state["authenticated"] = True
    return synced_user