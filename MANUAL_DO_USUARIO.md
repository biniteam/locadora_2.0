# Manual do Usuário - Sistema de Locação

## FAQ - Perguntas Frequentes

**Q: Como faço login no sistema?**
A: Use seu nome de usuário e senha cadastrados. O sistema aceita 3 níveis: admin, manager, viewer.

**Q: Posso excluir um cliente que tem reservas ativas?**
A: Não. O sistema impede a exclusão de clientes com reservas em andamento. Finalize a devolução primeiro.

**Q: Como calcular o valor total de uma locação?**
A: O sistema calcula automaticamente baseado em: diárias × valor diária + km excedidos × valor/km + taxas adicionais.

**Q: O que significa status "Disponível" vs "Excluído"?**
A: "Disponível" = carro pode ser locado. "Excluído" = carro removido da frota mas mantido no histórico.

**Q: Como gerar relatórios?**
A: Acesse a página "Relatórios" no menu lateral. Escolha o tipo e período desejados.

---

## Página 1: Login e Autenticação

### Acesso ao Sistema
- **URL**: Digite o endereço da aplicação no navegador
- **Credenciais**: Nome de usuário e senha
- **Níveis de Acesso**:
  - **Admin**: Controle total
  - **Manager**: Operações completas exceto gerenciar usuários
  - **Viewer**: Apenas visualização

### Primeiro Acesso
1. Contate o administrador para criar seu usuário
2. Receba nome de usuário e senha temporária
3. Faça login e altere sua senha

---

## Página 2: Dashboard Principal

### Visão Geral
- **Resumo de Reservas**: Ativas, concluídas, canceladas
- **Status da Frota**: Disponíveis, locados, em manutenção
- **Métricas do Mês**: Faturamento, ocupação, novos clientes

### Navegação
- **Menu Lateral**: Acesso rápido a todas as funcionalidades
- **Botão Sair**: Finaliza sessão com segurança

---

## Página 3: Gestão de Clientes

### Aba "Cadastrar Novo"
**Campos Obrigatórios:**
- Nome completo
- CPF (único no sistema)
- Telefone

**Campos Opcionais:**
- RG, CNH, validade da CNH
- Endereço completo
- E-mail, data de nascimento
- Observações

### Aba "Ver / Editar Clientes"
**Funcionalidades:**
- **Buscar**: Por nome ou CPF
- **Editar**: Modificar dados cadastrais
- **Status**: Ativo/Inativo/Removido
- **Histórico**: Visualizar reservas do cliente

**Regras de Negócio:**
- Clientes com reservas ativas não podem ser removidos
- CPF duplicado é bloqueado automaticamente

---

## Página 4: Gestão da Frota (Carros)

### Aba "Cadastrar Veículo"
**Informações Básicas:**
- Marca, modelo, placa (única)
- Cor, ano do veículo
- Diária, preço por km

**Manutenção:**
- KM atual, KM para troca de óleo
- Data próxima manutenção
- Número chassi/RENAVAM

### Aba "Ver / Editar / Status"
**Status Possíveis:**
- **Disponível**: Pronto para locação
- **Locado**: Em uso
- **Manutenção**: Indisponível temporariamente
- **Excluído**: Removido da frota

**Operações:**
- Editar dados do veículo
- Alterar status
- Visualizar histórico de locações

---

## Página 5: Reservas e Locações

### Criar Nova Reserva
**Passo 1: Selecionar Veículo**
- Escolha carro disponível
- Verifique informações do veículo

**Passo 2: Dados do Cliente**
- Selecione cliente cadastrado
- Ou cadastre novo cliente

**Passo 3: Período da Locação**
- Data início e fim
- Horário de entrega
- Cálculo automático de diárias

**Passo 4: Valores e Pagamento**
- Diárias calculadas automaticamente
- Adiantamento (opcional)
- Taxas adicionais

### Gerenciar Reservas
**Status da Reserva:**
- **Reservada**: Confirmada mas não entregue
- **Locada**: Veículo entregue
- **Concluída**: Devolvida
- **Cancelada**: Cancelada sem multa

**Operações:**
- Editar dados da reserva
- Registrar entrega/devolução
- Calcular valores finais
- Imprimir contrato/recibo

---

## Página 6: Gestão de Multas

### Registrar Multa
**Informações Necessárias:**
- Reserva associada
- Tipo da infração
- Valor da multa
- Data e local
- Comprovante (opcional)

**Status:**
- **Pendente**: Aguardando pagamento
- **Paga**: Quitada
- **Isentada**: Cancelada

### Controle de Pagamentos
- Registrar data de pagamento
- Anexar comprovantes
- Gerar relatórios de multas

---

## Página 7: Relatórios

### Tipos de Relatórios
**Faturamento:**
- Por período
- Por veículo
- Por cliente

**Ocupação:**
- Taxa de ocupação da frota
- Dias por mês
- Comparativos

**Clientes:**
- Novos cadastros
- Clientes ativos
- Histórico de locações

**Multas:**
- Multas por período
- Por tipo de infração
- Status de pagamento

### Exportação
- **PDF**: Relatórios formatados
- **Excel**: Dados brutos para análise
- **Filtros**: Personalizar período e critérios

---

## Página 8: Administração (Apenas Admin)

### Gestão de Usuários
**Criar Usuário:**
- Nome de usuário (único)
- Senha temporária
- Nível de acesso
- Dados pessoais

**Gerenciar Usuários:**
- Ativar/desativar contas
- Redefinir senhas
- Alterar nível de acesso
- Histórico de acessos

### Backup e Manutenção
- **Backup Automático**: Diário
- **Backup Manual**: Sob demanda
- **Restauração**: Apenas admin

---

## Dicas e Boas Práticas

### Segurança
- Altere senhas periodicamente
- Não compartilhe credenciais
- Faça logout após uso

### Operações
- Verifique disponibilidade antes de reservar
- Confirme dados do cliente
- Registre KM na entrega/devolução

### Manutenção
- Mantenha dados atualizados
- Faça backups regulares
- Monitore relatórios de ocupação

---

## Suporte Técnico

**Contatos:**
- Administrador do sistema: [email/telefone]
- Suporte técnico: [email/telefone]

**Horário de Atendimento:**
- Segunda a Sexta: 8h-18h
- Sábado: 8h-12h
- Emergências: 24h

---

## Atualizações do Sistema

O sistema é atualizado regularmente com:
- Novas funcionalidades
- Melhorias de segurança
- Correções de bugs

Mantenha-se atualizado através dos comunicados internos.
