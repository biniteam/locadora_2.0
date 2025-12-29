# Migração para PostgreSQL (Supabase) - Sistema de Locadora

Este documento descreve como migrar e configurar o sistema de locadora de veículos para usar PostgreSQL ao invés de SQLite.

## 📋 Visão Geral da Migração

O projeto foi migrado de SQLite para PostgreSQL/Supabase, mantendo toda a lógica de negócio intacta. As principais mudanças incluem:

- ✅ **Substituído sqlite3 por psycopg2-binary**
- ✅ **AUTOINCREMENT → SERIAL**
- ✅ **PRAGMA table_info → information_schema**
- ✅ **Variáveis de ambiente para credenciais**
- ✅ **Módulo db_utils.py para conexões centralizadas**

## 🚀 Configuração Inicial

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

O arquivo `requirements.txt` agora inclui:
- `psycopg2-binary==2.9.9` (para PostgreSQL)
- Todas as outras dependências mantidas

### 2. Testar Conexão Local

Para desenvolvimento local, execute o script de teste:

```bash
python3 test_connection.py
```

Este script irá:
- ✅ Detectar automaticamente o tipo de banco (SQLite por padrão)
- ✅ Verificar conectividade
- ✅ Listar tabelas existentes
- ✅ Mostrar estatísticas básicas

**Saída esperada para desenvolvimento local:**
```
🔍 Testando conexão com o banco de dados...
📊 Tipo de banco: sqlite
✅ Conexão estabelecida com sucesso!
📋 Tipo: sqlite
📊 Tabelas encontradas: 7
🏷️  Tabelas: audit_logs, carros, clientes, reservas, sessions, sqlite_sequence, users
```

### 2. Configurar Supabase

1. **Criar conta no Supabase**: [supabase.com](https://supabase.com)
2. **Criar novo projeto** no painel do Supabase
3. **Anotar as credenciais**:
   - URL de conexão
   - Senha do banco
   - Nome do projeto

### 3. Configurar Credenciais

#### Desenvolvimento Local (SQLite - Recomendado para testes)

Para desenvolvimento local, o sistema **automaticamente usa SQLite**. Basta deixar o arquivo `.streamlit/secrets.toml` vazio ou com configuração mínima:

```toml
[database]
# Para forçar uso de SQLite (opcional, já é padrão)
use_sqlite = true

# Configurações adicionais para desenvolvimento
debug_mode = true
log_level = "INFO"
```

**Vantagens do SQLite para desenvolvimento:**
- 🔄 **Setup automático** - não precisa configurar banco externo
- ⚡ **Performance** - ideal para desenvolvimento rápido
- 💾 **Arquivo local** - dados persistidos em `locadora_v2.db`
- 🔄 **Hot reload** - tabelas criadas automaticamente na primeira execução

#### Produção (PostgreSQL/Supabase - Recomendado para produção)

Edite o arquivo `.streamlit/secrets.toml`:

```toml
[database]
# URL completa de conexão do Supabase
database_url = "postgresql://postgres:[SUA_SENHA]@db.[SEU_PROJETO].supabase.co:5432/postgres"

# Ou configure separadamente:
# host = "db.[SEU_PROJETO].supabase.co"
# port = 5432
# database = "postgres"
# user = "postgres"
# password = "[SUA_SENHA]"
# sslmode = "require"
```

#### Opção B: Variáveis de Ambiente (Desenvolvimento)

```bash
export DB_HOST="db.[SEU_PROJETO].supabase.co"
export DB_PORT=5432
export DB_NAME="postgres"
export DB_USER="postgres"
export DB_PASSWORD="[SUA_SENHA]"
export DB_SSLMODE="require"
```

### 4. Executar a Aplicação

```bash
streamlit run app8.py
```

A aplicação irá:
1. ✅ **Detectar automaticamente** SQLite (desenvolvimento) ou PostgreSQL (produção)
2. ✅ **Verificar conexão** com o banco configurado
3. ✅ **Criar tabelas** automaticamente se não existirem
4. ✅ **Criar usuário admin** padrão (admin/admin123)
5. ✅ **Iniciar** normalmente

### 5. Verificar Funcionamento (Opcional)

Execute o script de diagnóstico para verificar a saúde da conexão:

```bash
python3 test_connection.py
```

**Exemplo de saída para desenvolvimento local:**
```
🔍 Testando conexão com o banco de dados...
📊 Tipo de banco: sqlite
✅ Conexão estabelecida com sucesso!
📋 Tipo: sqlite
📊 Tabelas encontradas: 7
🏷️  Tabelas: audit_logs, carros, clientes, reservas, sessions, users
```

## 📊 Estrutura do Banco PostgreSQL

### Tabelas Criadas

```sql
-- Veículos
CREATE TABLE carros (
    id SERIAL PRIMARY KEY,
    modelo TEXT,
    placa TEXT UNIQUE,
    cor TEXT,
    diaria REAL,
    preco_km REAL,
    km_atual INTEGER,
    status TEXT DEFAULT 'Disponível',
    numero_chassi TEXT,
    numero_renavam TEXT,
    ano_veiculo INTEGER,
    km_troca_oleo INTEGER DEFAULT 10000
);

-- Clientes
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nome TEXT,
    cpf TEXT UNIQUE,
    cnh TEXT,
    validade_cnh DATE,
    telefone TEXT,
    endereco TEXT,
    observacoes TEXT,
    status TEXT DEFAULT 'Ativo'
);

-- Reservas/Locações
CREATE TABLE reservas (
    id SERIAL PRIMARY KEY,
    carro_id INTEGER REFERENCES carros(id),
    cliente_id INTEGER REFERENCES clientes(id),
    data_inicio DATE,
    data_fim DATE,
    reserva_status TEXT DEFAULT 'Reservada',
    status TEXT,
    custo_lavagem REAL DEFAULT 0,
    valor_total REAL DEFAULT 0,
    km_saida INTEGER,
    km_volta INTEGER,
    km_franquia INTEGER DEFAULT 300,
    adiantamento REAL DEFAULT 0.0,
    valor_multas REAL DEFAULT 0.0,
    valor_danos REAL DEFAULT 0.0,
    valor_outros REAL DEFAULT 0.0
);

-- Usuários (Autenticação)
CREATE TABLE users (
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
);

-- Sessões
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT
);

-- Logs de Auditoria
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action TEXT,
    resource TEXT,
    details TEXT,
    ip_address TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 Arquitetura da Migração

### Módulos Modificados

#### `db_utils.py` (Novo)
- **Função centralizada** de conexão PostgreSQL
- **Funções utilitárias** para queries e verificações
- **Tratamento de erros** padronizado
- **Compatibilidade** com secrets.toml e variáveis de ambiente

#### `init_db.py`
- **Migrado** para PostgreSQL
- **SERIAL** ao invés de AUTOINCREMENT
- **information_schema** para verificação de tabelas/colunas
- **Criação automática** de tabelas e colunas faltantes

#### `auth.py`
- **Queries convertidas** para PostgreSQL
- **Placeholders %s** ao invés de ?
- **BOOLEAN** ao invés de INTEGER para campos booleanos
- **Manutenção** de toda lógica de autenticação

#### `app8.py`
- **Imports atualizados** (db_utils ao invés de sqlite3)
- **Queries convertidas** (placeholders, funções de data)
- **Sintaxe PostgreSQL** (strftime → TO_CHAR, date() → ::date)

### Principais Diferenças SQLite → PostgreSQL

| SQLite | PostgreSQL | Exemplo |
|--------|------------|---------|
| `AUTOINCREMENT` | `SERIAL` | `id SERIAL PRIMARY KEY` |
| `PRAGMA table_info` | `information_schema.columns` | Verificação de colunas |
| `?` placeholders | `%s` placeholders | `WHERE id = %s` |
| `strftime('%Y-%m', date)` | `TO_CHAR(date, 'YYYY-MM')` | Formatação de datas |
| `date(column)` | `column::date` | Cast para date |

## 🔒 Segurança

### Credenciais Seguras
- ✅ **Nunca commite** `secrets.toml` no Git
- ✅ **Use variáveis de ambiente** em produção
- ✅ **SSL obrigatório** para Supabase
- ✅ **Hash de senha** mantido (bcrypt)

### Usuário Admin Padrão
- **Username**: `admin`
- **Senha**: `admin123`
- **⚠️ ALTERE** a senha após primeiro login!

## 🧪 Testes e Validação

### Verificar Conexão
```python
from db_utils import check_db_connection
health = check_db_connection()
print("Status:", "OK" if health['healthy'] else "ERRO")
```

### Executar Testes
```bash
python -m pytest test_app.py  # Se existir
```

### Verificar Logs
- **Supabase Dashboard**: Monitor de queries
- **Aplicação**: Logs de auditoria mantidos
- **Console**: Mensagens de debug

## 🚀 Deploy no Streamlit Cloud

### 1. Configurar Secrets
No painel do Streamlit Cloud, adicionar secrets:

```
[database]
database_url = "postgresql://..."
```

### 2. Deploy Normal
```bash
git add .
git commit -m "Migração para PostgreSQL"
git push origin main
```

### 3. Verificar
- ✅ **Aplicação inicia** sem erros
- ✅ **Banco conecta** automaticamente
- ✅ **Tabelas criadas** na primeira execução

## 🆘 Troubleshooting

### Erro de Conexão
```
psycopg2.OperationalError: connection failed
```
**Soluções**:
- ✅ Verificar credenciais no `secrets.toml`
- ✅ Confirmar URL do Supabase
- ✅ Verificar firewall/rede

### Tabelas Não Criadas
```
relation "carros" does not exist
```
**Soluções**:
- ✅ Verificar permissões do usuário no Supabase
- ✅ Executar aplicação uma vez para criar tabelas
- ✅ Verificar logs de erro

### Queries Lentas
- ✅ **Habilitar índices** no Supabase se necessário
- ✅ **Monitorar** queries no painel do Supabase
- ✅ **Otimizar** queries complexas

## 📈 Benefícios da Migração

### Vantagens PostgreSQL/Supabase
- ✅ **Multi-usuário** simultâneo
- ✅ **Dados persistentes** (não perde a cada 12h)
- ✅ **Backup automático** pelo Supabase
- ✅ **Escalabilidade** horizontal
- ✅ **Segurança** avançada
- ✅ **Monitoramento** em tempo real

### Performance Melhorada
- ✅ **Conexões persistentes**
- ✅ **Queries otimizadas**
- ✅ **Índices automáticos**
- ✅ **Cache inteligente**

## 🎯 Próximos Passos

1. **Testar thoroughly** todas as funcionalidades
2. **Fazer backup** dos dados atuais (se houver)
3. **Migrar dados** do SQLite para PostgreSQL (se necessário)
4. **Configurar monitoring** no Supabase
5. **Documentar** procedures de backup

---

## 📞 Suporte

Para dúvidas sobre a migração:
1. Verificar logs da aplicação
2. Consultar documentação do Supabase
3. Revisar configurações de conexão

**A migração mantém 100% da funcionalidade original, apenas trocando o banco de dados!** 🎉