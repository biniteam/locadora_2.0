# 🚗 Locadora de Veículos 2.0

Sistema de gerenciamento de locadora de veículos desenvolvido em **Streamlit** com suporte a **Supabase** como banco de dados em nuvem.

> **Nota:** Esta é a versão 2.0 do sistema, com suporte nativo ao Supabase. A versão anterior com SQLite está disponível no repositório original.

## 🚀 Funcionalidades

### 🔐 Autenticação Simplificada
- **Login seguro** integrado com Supabase Auth
- **Níveis de usuário**: Administrador, Gerente, Funcionário, Visualizador
- **Controle de permissões** baseado em papéis
- **Sessões gerenciadas** via Supabase

### 📊 Gestão da Locadora
- **Dashboard**: Painel com métricas gerais e agenda do dia
- **Gestão de Clientes**: Cadastro e histórico completo
- **Frota**: Controle de veículos e disponibilidade
- **Reservas**: Sistema completo de agendamento
- **Contratos**: Geração automática de documentos

## 🛠️ Tecnologias Utilizadas

- **Python 3.10+**
- **Streamlit 1.32+**
- **Supabase**: Autenticação e banco de dados
- **Pandas**: Manipulação de dados
- **SQLAlchemy**: ORM para PostgreSQL

## 🌐 Implantação no Streamlit Cloud

### 1. Pré-requisitos

- Conta no [Streamlit Community Cloud](https://streamlit.io/cloud)
- Repositório no GitHub
- Conta no [Supabase](https://supabase.com/)

### 2. Configuração do Supabase

1. Crie um novo projeto no [Supabase](https://supabase.com/)
2. No painel do Supabase, vá para "Authentication" e crie um novo usuário
3. Anote as seguintes informações:
   - URL da API (encontrada em Project Settings > API)
   - Chave anônima (public anon key)
   - String de conexão do banco de dados

### 3. Configuração do Streamlit Cloud

1. Faça login no [Streamlit Community Cloud](https://share.streamlit.io/)
2. Clique em "New app"
3. Selecione seu repositório e branch
4. No campo "Main file path", insira `app.py`
5. Em "Advanced settings", adicione as variáveis de ambiente:
   - `SUPABASE_URL`: Sua URL da API do Supabase
   - `SUPABASE_KEY`: Sua chave anônima do Supabase
   - `DATABASE_URL`: String de conexão com o banco de dados

### 4. Primeiro Acesso

1. Após o deploy, acesse a URL fornecida
2. Use as credenciais do usuário criado no Supabase
3. O primeiro usuário será configurado como administrador

## 🔒 Segurança

### Configurações Recomendadas

1. **Supabase**
   - Habilite confirmação de email
   - Configure políticas de senha fortes
   - Ative proteção contra força bruta

2. **Streamlit Cloud**
   - Nunca faça commit do `secrets.toml`
   - Use variáveis de ambiente para credenciais
   - Ative logs de auditoria

3. **Backup**
   - Configure backups automáticos
   - Exporte dados regularmente

## 📚 Recursos Adicionais

- [Documentação do Supabase](https://supabase.com/docs)
- [Documentação do Streamlit](https://docs.streamlit.io/)
- [Guia de Autenticação](https://supabase.com/docs/guides/auth)
- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)

## 🤝 Suporte

Para suporte, verifique a documentação ou abra uma issue no repositório do projeto.
