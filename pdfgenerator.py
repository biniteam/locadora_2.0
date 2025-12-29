"""
Módulo para geração de PDFs da Locadora
Contém funções para gerar contratos, recibos e gerenciar arquivos PDF
Baseado no contrato oficial da J.A. MARCELLO & CIA LTDA
"""

from fpdf import FPDF
from datetime import date, timedelta
import os


# --- CONSTANTES DE STATUS DO VEÍCULO ---
STATUS_CARRO = {
    'DISPONIVEL': 'Disponível',
    'LOCADO': 'Locado',
    'RESERVADO': 'Reservado',
    'INDISPONIVEL': 'Indisponível',
    'EXCLUIDO': 'Excluído'
}

# --- CONSTANTES DE STATUS DO CLIENTE ---
STATUS_CLIENTE = {
    'ATIVO': 'Ativo',
    'INATIVO': 'Inativo',
    'REMOVIDO': 'Removido'
}

# --- CONSTANTES DE STATUS DA RESERVA ---
STATUS_RESERVA = {
    'RESERVADA': 'Reservada',
    'LOCADA': 'Locada',
    'CANCELADA': 'Cancelada',
    'FINALIZADA': 'Finalizada'
}

def formatar_moeda(valor):
    """
    Formata um valor float para a moeda brasileira (R$ 0.000,00).

    Args:
        valor: Valor numérico a ser formatado

    Returns:
        String formatada no padrão brasileiro (R$ 1.234,56)
    """
    if valor is None:
        valor = 0.0
    # Garante que o separador decimal seja vírgula e o milhar seja ponto
    return f"R$ {valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def formatar_data_portugues(data):
    """
    Formata uma data no formato brasileiro com mês em português.

    Args:
        data: Objeto date a ser formatado

    Returns:
        String formatada no padrão brasileiro (dia de mês de ano)
    """
    # Mapeamento dos meses em inglês para português
    meses_portugues = {
        'January': 'janeiro',
        'February': 'fevereiro',
        'March': 'março',
        'April': 'abril',
        'May': 'maio',
        'June': 'junho',
        'July': 'julho',
        'August': 'agosto',
        'September': 'setembro',
        'October': 'outubro',
        'November': 'novembro',
        'December': 'dezembro'
    }

    # Formata a data primeiro em inglês
    data_ingles = data.strftime('%d de %B de %Y')

    # Substitui o nome do mês em inglês pelo português
    for mes_ingles, mes_portugues in meses_portugues.items():
        data_ingles = data_ingles.replace(mes_ingles, mes_portugues)

    return data_ingles


class PDF(FPDF):
    """Classe base para geração de PDFs com cabeçalho customizado"""
    
    def __init__(self, titulo="DOCUMENTO"):
        """
        Inicializa o PDF com um título específico
        
        Args:
            titulo: Título que aparecerá no cabeçalho do PDF
        """
        super().__init__()
        self.titulo_documento = titulo
    
    def header(self):
        """Define o cabeçalho padrão de todos os PDFs"""
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, self.titulo_documento, 0, 1, 'C')
        self.ln(5)


def gerar_contrato_pdf(cliente, carro, data_inicio, data_fim, horario_entrega=None):
    """
    Gera o PDF do contrato de locação no formato oficial.
    
    Args:
        cliente: Dicionário com dados do cliente (nome, cpf, cnh, telefone, endereco)
        carro: Dicionário com dados do carro (modelo, placa, cor, km_atual, diaria, preco_km)
        data_inicio: Data de início da locação (date object)
        data_fim: Data prevista de devolução (date object)
        horario_entrega: Horário da entrega (time object, opcional)
        
    Returns:
        Bytes do PDF gerado em formato latin-1
    """
    pdf = PDF(titulo='CONTRATO DE LOCACAO DE VEICULO')
    pdf.add_page()
    pdf.set_font("Arial", size=12)


    # Calcula o prazo em dias
    prazo_dias = (data_fim - data_inicio).days
    if prazo_dias==0:
        prazo_dias = 1
        

    # Formatação de valores monetários
    diaria_formatada = formatar_moeda(carro['diaria'])
    preco_km_formatado = formatar_moeda(carro['preco_km'])

    # Monta o texto do contrato baseado no template oficial
    texto = f"""
J.A. MARCELLO & CIA LTDA, ora denominado empresa Brasileira, sediada na Avenida 
Independencia, 1950, Sao Cristovao, em Capanema - PR, inscrita CNPJ no 10.454.344/0001-24.

{cliente['nome'].upper()}, ora denominado brasileiro, sediado em {cliente.get('endereco', 'NAO INFORMADO')},
inscrito CPF: {cliente['cpf']} TELEFONE: {cliente.get('telefone', 'NAO INFORMADO')}

As partes acima identificadas tem, entre si, justo e acertado o presente Contrato de Locacao 
de Automovel por Prazo Determinado, que se regera pelas clausulas seguintes e pelas condicoes 
descritas no presente.

DO OBJETO DO CONTRATO

Clausula 1a. O presente contrato tem como OBJETO a locacao do AUTOMOVEL {carro['modelo'].upper()},
COR PREDOMINANTE {carro.get('cor', 'NAO INFORMADA').upper()}, PLACA {carro['placa'].upper()},
RENAVAM {carro.get('numero_renavam', 'NAO INFORMADO')}, CHASSI {carro.get('numero_chassi', 'NAO INFORMADO')},
ANO VEICULO: {carro.get('ano_veiculo', 'NAO INFORMADO')},
KM INICIAL: {carro.get('km_atual', 0)}.

Clausula 2a. O LOCADOR declara ser o legitimo possuidor e/ou proprietario do veiculo descrito
acima, o qual encontra-se em perfeitas condicoes mecanicas de uso, conservacao e funcionamento
e que resolveu da-lo em locacao ao LOCATARIO, pelo prazo e condicoes determinados no presente
instrumento.

DO USO

Clausula 3a. O automovel, objeto deste contrato, sera utilizado exclusivamente pelo LOCATARIO
para uso pessoal, nao sendo permitido, em nenhuma hipotese, o seu uso por terceiros ou para
fins diversos sob pena de rescisao contratual e o pagamento da multa conforme previsto neste
contrato.

Clausula 4a. O LOCATARIO compromete-se a utilizar o veiculo alugado sempre de acordo com os
regulamentos estabelecidos pelo Conselho Nacional de Transito e pelo Departamento Estadual de
Transito, bem como, pela guarda e uso correto do veiculo.

Clausula 5a. O veiculo locado apenas podera ser dirigido pelo LOCATARIO, portador da CNH no
{cliente.get('cnh', 'NAO INFORMADA')}.

DO USO INDEVIDO DO VEICULO

Clausula 6a. Configurar-se-a o uso indevido do veiculo e infracao contratual, ocasionando sua
rescisao com a imputacao de multa, quando:

6.1. em caso de acidente, furto, roubo ou colisao, tiver procedido com manifesto dolo ou culpa
(imprudencia, impericia ou negligencia), e/ou utilizado o veiculo para fins diversos da
destinacao especifica constante no Certificado de Registro e Licenciamento de Veiculo e/ou
especificacoes do fabricante.

6.2. entregar a direcao do veiculo a pessoa nao indicada neste contrato e que venha a sofrer
acidente, mesmo que este nao tenha sido provocado pelo condutor.

6.3. trafegar por vias publicas, rodovias ou caminhos sem condicoes de trafego e, em
consequencia, ocasionar dano ao veiculo ou acidente com terceiro.

6.4. infringir qualquer dispositivo do Codigo Nacional de Transito e, em decorrencia disso,
provocar acidente com terceiro ou dano ao veiculo, principalmente no caso de velocidade
imprimida acima do permitido para o local.

6.5. Outras modalidades de uso do veiculo que possam se configurar como mau uso comprovado
esse atraves de laudo de oficina mecanica ou funilaria especializada, testemunhas ou outros
meios legais.

Clausula 7a. Configurando-se qualquer das hipoteses da presente clausula, o LOCATARIO arcara
com todos os prejuizos a que causar ao LOCADOR, bem como, a terceiros prejudicados, inclusive
danos pessoais dos passageiros do carro alugado e/ou terceiros, sem prejuizo das coberturas
previstas no DPVAT. Ainda, o LOCADOR, a titulo de lucro cessante, 70% (setenta por cento),
do valor da diaria contratada, pelo periodo que permanecer em conserto, ate o limite de 30
(trinta) diarias.

Clausula 8a. No caso em que a reparacao do veiculo atingir 30% (trinta por cento), de seu
valor comercial, considerar-se-a tabela fipe, com o pagamento arcado exclusivamente pelo
LOCATARIO.

DO PRAZO

Clausula 9a. A presente locacao tera o inicio a partir de {formatar_data_portugues(data_inicio)}
e tera a duracao de {prazo_dias} ({_numero_por_extenso(prazo_dias)}) DIAS. Findo o prazo
estipulado, o contrato podera ser renovado por vontade das partes atraves de aditivo ou outro
instrumento contratual, ou ainda, o veiculo devera ser devolvido ao LOCADOR nas mesmas condicoes
em que estava quando o recebeu (Higienizado e em perfeitas condicoes de uso), ou seja, em
perfeitas condicoes de uso, respondendo por prejuizos ou danos causados.

Clausula 10a. Se o LOCATARIO nao restituir o automovel na data estipulada, devera pagar,
enquanto detiver em seu poder, o aluguel que o LOCADOR arbitrar, e respondera pelo dano que o
automovel venha a sofrer mesmo se proveniente de caso fortuito.

DO PAGAMENTO

Clausula 11a. Pagamento sera no valor de {diaria_formatada} a diaria + {preco_km_formatado}
o quilometro rodado.

Clausula 12a. O LOCATARIO reconhece que o valor apurado neste instrumento como divida liquida,
certa e exigivel, legitimando a cobranca via Acao de Execucao, nos termos do Codigo de
Processo Civil.

DA DEVOLUCAO

Clausula 13a. O LOCATARIO devera devolver o automovel ao LOCADOR o veiculo objeto deste
contrato nas mesmas condicoes em que estava quando o recebeu (Higienizado e limpo), ou seja,
em perfeitas condicoes de uso, respondendo pelos danos ou prejuizos causados.

DA RESCISAO

Clausula 14a. O descumprimento de qualquer das clausulas, bem como, o inadimplemento
contratual por quaisquer das partes, justifica a rescisao do presente instrumento, dispensado
o prazo de comunicacao, e o devido pagamento de multa, pela parte inadimplente no valor de
20% (vinte por cento) do valor contratual.

DA MULTA, IMPOSTOS E ENCARGOS INCIDENTES SOB O VEICULO

Clausula 15a. Fica o LOCATARIO responsavel pelas multas de transito que eventualmente cometer,
incluindo a transferencia de pontuacao e pagamento dos valores, devendo para tal disponibilizar
a documentacao requerida e no prazo indicado pelo Departamento de Transito do estado de Parana.

Clausula 16a. Os impostos e encargos incidentes sobre o veiculo, IPVA, seguro DPVAT,
Licenciamento anual serao suportados exclusivamente pelo LOCADOR.

Clausula 17a. Os valores a titulo seguro contra furto, roubo e acidentes contratado para o
veiculo serao suportados pelo LOCADOR.

Paragrafo unico. Em caso de sinistro ocasionado por culpa ou dolo do LOCATARIO, este ficara
responsavel pelo pagamento da franquia de seguro.

Clausula 18a. Em decorrencia deste contrato, o LOCATARIO isenta desde ja o LOCADOR de
responsabilidades civis a qualquer titulo, bem como de figurar como parte passiva de qualquer
demanda oriunda de eventos que envolvam o carro alugado atraves deste contrato, onus que o
LOCATARIO assumira per si e exclusivamente. Ademais, na hipotese de o LOCADOR ser acionado,
isolado ou solidariamente, ficara autorizado a chamar o LOCATARIO ao processo, a fim de assumir
a demanda, ou ainda, para preservar o direito de regresso.

DISPOSICOES GERAIS

Clausula 19a. Devera manter o veiculo em perfeito estado de conservacao, de ordem mecanica,
tapeçaria e funilaria, devendo entregar, com o termino do contrato, o veiculo e sua documentacao
ao LOCADOR nas mesmas condicoes em que recebeu.

DO FORO

Clausula 20a. Para dirimir quaisquer controversias oriundas do CONTRATO, as partes elegem o
foro da comarca de Capanema - PR.

Por estarem assim justos e contratados, firmam o presente instrumento, em duas vias de igual
teor e forma, juntamente com 2 (duas) testemunhas.

Capanema, {formatar_data_portugues(date.today())}.


____________________________________
{cliente['nome'].upper()}


DADOS E CARACTERISTICAS DO VEICULO LOCADO:

Marca/Modelo: {carro['modelo'].upper()}
Placa: {carro['placa'].upper()}
Chassi: {carro.get('chassi', 'NAO INFORMADO')}
Renavam: {carro.get('renavam', 'NAO INFORMADO')}
Prazo de locacao: {prazo_dias} DIAS
Km do hodometro: {carro.get('km_atual', 0)}

DATA DE ENTREGA DO VEICULO AO CLIENTE: {data_inicio.strftime('%d/%m/%Y')}{f' as {horario_entrega.strftime("%H:%M")}h' if horario_entrega else ''}

Declaro que conferi o estado do veiculo ora entregue para locacao, recebendo-o por este termo
conforme contrato de locacao de veiculos firmado.


____________________________________
{cliente['nome'].upper()}

DATA DE DEVOLUCAO DO VEICULO: {data_fim.strftime('%d/%m/%Y')}
"""
    
    # Adiciona o texto ao PDF (usa latin-1 para compatibilidade com acentos)
    pdf.multi_cell(0, 5, texto.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest="S")


def _numero_por_extenso(numero):
    """
    Converte números de 1 a 365 por extenso (simplificado).
    
    Args:
        numero: Número inteiro a ser convertido
        
    Returns:
        String com o número por extenso em maiúsculas
    """
    # Dicionário básico para números comuns
    extensos = {
        1: "UM", 2: "DOIS", 3: "TRES", 4: "QUATRO", 5: "CINCO",
        6: "SEIS", 7: "SETE", 8: "OITO", 9: "NOVE", 10: "DEZ",
        11: "ONZE", 12: "DOZE", 13: "TREZE", 14: "QUATORZE", 15: "QUINZE",
        20: "VINTE", 30: "TRINTA", 40: "QUARENTA", 50: "CINQUENTA",
        60: "SESSENTA", 70: "SETENTA", 80: "OITENTA", 90: "NOVENTA"
    }
    
    if numero in extensos:
        return extensos[numero]
    elif numero < 20:
        return str(numero).upper()
    elif numero < 100:
        dezena = (numero // 10) * 10
        unidade = numero % 10
        if unidade == 0:
            return extensos[dezena]
        return f"{extensos[dezena]} E {extensos.get(unidade, str(unidade))}"
    else:
        return str(numero).upper()


def gerar_recibo_pdf(cliente, carro, reserva_dados):
    """
    Gera o PDF do recibo de devolução.
    
    Args:
        cliente: Dicionário com dados do cliente
        carro: Dicionário com dados do carro
        reserva_dados: Dicionário com dados da reserva incluindo:
            - data_inicio: Data de saída
            - data_fim: Data de devolução (hoje)
            - km_saida: KM de saída
            - km_volta: KM de volta
            - km_franquia: KM de franquia
            - dias_cobranca: Dias cobrados
            - custo_diarias: Valor das diárias
            - custo_km: Valor dos KMs rodados
            - valor_lavagem: Valor da lavagem (se houver)
            - valor_multas: Valor de multas
            - valor_danos: Valor de danos
            - valor_outros: Outros custos
            - adiantamento: Valor de adiantamento
            - total_final: Valor total final
            
    Returns:
        Bytes do PDF gerado em formato latin-1
    """
    pdf = PDF(titulo='RECIBO DE DEVOLUCAO')
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    # Calcula KM rodados
    km_rodados = reserva_dados['km_volta'] - reserva_dados['km_saida']
    km_a_cobrar = max(0, km_rodados - reserva_dados['km_franquia'])
    
    # Subtotal antes do adiantamento - convertendo todos os valores para Decimal
    from decimal import Decimal
    
    # Função auxiliar para converter para Decimal de forma segura
    def to_decimal(value, default='0.0'):
        if value is None:
            return Decimal(default)
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
    
    # Convertendo todos os valores para Decimal
    custo_diarias = to_decimal(reserva_dados.get('custo_diarias', 0.0))
    custo_km = to_decimal(reserva_dados.get('custo_km', 0.0))
    valor_lavagem = to_decimal(reserva_dados.get('valor_lavagem', 0.0))
    valor_multas = to_decimal(reserva_dados.get('valor_multas', 0.0))
    valor_danos = to_decimal(reserva_dados.get('valor_danos', 0.0))
    valor_outros = to_decimal(reserva_dados.get('valor_outros', 0.0))
    
    subtotal = (custo_diarias + custo_km + valor_lavagem + 
                valor_multas + valor_danos + valor_outros)
    
    # Verifica se há informações de pagamento
    valor_pago = to_decimal(reserva_dados.get('valor_pago', 0.0))
    valor_restante = to_decimal(reserva_dados.get('valor_restante', 0.0))
    total_final = to_decimal(reserva_dados.get('total_final', 0.0))
    
    # Define se é valor a pagar ou a receber
    if total_final >= Decimal('0'):
        if valor_pago > Decimal('0') and valor_restante <= Decimal('0'):
            label_total = "VALOR QUITADO"
        else:
            label_total = "VALOR A PAGAR"
        valor_final_display = formatar_moeda(float(total_final))
    else:
        label_total = "VALOR A DEVOLVER AO CLIENTE"
        valor_final_display = formatar_moeda(abs(reserva_dados['total_final']))

    texto = f"""
J.A. MARCELLO & CIA LTDA
Avenida Independencia, 1950, Sao Cristovao, Capanema - PR
CNPJ: 10.454.344/0001-24

DATA DE EMISSAO: {date.today().strftime('%d/%m/%Y')}

================================================================
RECIBO DE DEVOLUCAO DE VEICULO
================================================================

CLIENTE: {cliente['nome'].upper()}
CPF: {cliente['cpf']}
TELEFONE: {cliente.get('telefone', 'NAO INFORMADO')}

VEICULO: {carro['modelo'].upper()}
PLACA: {carro['placa'].upper()}
COR: {carro.get('cor', 'NAO INFORMADA').upper()}
CHASSI: {carro.get('chassi', 'NAO INFORMADO')}
RENAVAM: {carro.get('renavam', 'NAO INFORMADO')}

================================================================
PERIODO DA LOCACAO
================================================================

Data de Retirada: {reserva_dados['data_inicio'].strftime('%d/%m/%Y')}
Data de Devolucao: {reserva_dados['data_fim'].strftime('%d/%m/%Y')}
Total de Dias Locados: {reserva_dados['dias_cobranca']} dia(s)

================================================================
QUILOMETRAGEM
================================================================

KM de Saida: {reserva_dados['km_saida']} km
KM de Volta: {reserva_dados['km_volta']} km
KM Rodados (Total): {km_rodados} km
KM de Franquia Contratada: {reserva_dados['km_franquia']} km (gratuitos)
KM Excedente a Cobrar: {km_a_cobrar} km

================================================================
VALORES COBRADOS
================================================================

Diarias: {reserva_dados['dias_cobranca']} dia(s) x {formatar_moeda(carro['diaria'])}
    Subtotal Diarias: {formatar_moeda(reserva_dados['custo_diarias'])}

Quilometragem: {km_a_cobrar} km x {formatar_moeda(carro['preco_km'])}
    Subtotal KM: {formatar_moeda(reserva_dados['custo_km'])}
"""
    
    # Adiciona custos extras se houver
    if reserva_dados['valor_lavagem'] > 0:
        texto += f"\nLavagem do Veiculo: {formatar_moeda(reserva_dados['valor_lavagem'])}"
    
    if reserva_dados['valor_multas'] > 0:
        texto += f"\nMultas de Transito: {formatar_moeda(reserva_dados['valor_multas'])}"
    
    if reserva_dados['valor_danos'] > 0:
        texto += f"\nDanos ao Veiculo: {formatar_moeda(reserva_dados['valor_danos'])}"
    
    if reserva_dados['valor_outros'] > 0:
        texto += f"\nOutros Custos: {formatar_moeda(reserva_dados['valor_outros'])}"
    
    # Adiciona informações de pagamento ao recibo
    texto_pagamento = ""
    if valor_pago > 0:
        texto_pagamento = f"""
----------------------------------------------------------------
PAGAMENTO REALIZADO: {formatar_moeda(valor_pago)}"""
        
        if valor_restante > 0:
            texto_pagamento += f"""
SALDO RESTANTE: {formatar_moeda(valor_restante)}"""
        else:
            texto_pagamento += f"""
STATUS: QUITADO"""
    
    texto += f"""

----------------------------------------------------------------
SUBTOTAL DA LOCACAO: {formatar_moeda(subtotal)}
(-) Adiantamento ja Pago: {formatar_moeda(reserva_dados['adiantamento'])}
{texto_pagamento}
================================================================

{label_total}: {valor_final_display}

================================================================


Capanema, {date.today().strftime('%d/%m/%Y')}


____________________________________
{cliente['nome'].upper()}
LOCATARIO


____________________________________
J.A. MARCELLO & CIA LTDA
LOCADOR
"""
    
    pdf.multi_cell(0, 5, texto.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest="S")


def salvar_pdf_arquivo(pdf_bytes, id_reserva, tipo='contrato'):
    """
    Salva o PDF em arquivo no sistema de arquivos.
    
    Args:
        pdf_bytes: Bytes do PDF a ser salvo
        id_reserva: ID da reserva (usado no nome do arquivo)
        tipo: Tipo do documento ('contrato' ou 'recibo')
        
    Returns:
        String com o caminho relativo do arquivo salvo
        
    Raises:
        Exception: Se houver erro ao criar pasta ou salvar arquivo
    """
    try:
        # Cria a pasta 'contratos' se não existir
        pasta_contratos = 'contratos'
        if not os.path.exists(pasta_contratos):
            os.makedirs(pasta_contratos)
        
        # Define o nome do arquivo
        nome_arquivo = f"{tipo}_{id_reserva}.pdf"
        caminho_completo = os.path.join(pasta_contratos, nome_arquivo)
        
        # Salva o arquivo
        with open(caminho_completo, 'wb') as f:
            f.write(pdf_bytes)
        
        return caminho_completo
    
    except Exception as e:
        raise Exception(f"Erro ao salvar PDF: {str(e)}")


def carregar_pdf_arquivo(caminho):
    """
    Carrega um PDF do sistema de arquivos.
    
    Args:
        caminho: Caminho relativo do arquivo PDF
        
    Returns:
        Bytes do PDF carregado
        
    Raises:
        FileNotFoundError: Se o arquivo não existir
        Exception: Para outros erros de leitura
    """
    try:
        # Validação de segurança: garante que o caminho está dentro da pasta 'contratos'
        if not caminho.startswith('contratos/') and not caminho.startswith('contratos\\'):
            raise Exception("Caminho de arquivo invalido")
        
        # Verifica se o arquivo existe
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Arquivo nao encontrado: {caminho}")
        
        # Lê e retorna o conteúdo do arquivo
        with open(caminho, 'rb') as f:
            return f.read()
    
    except FileNotFoundError as e:
        raise e
    except Exception as e:
        raise Exception(f"Erro ao carregar PDF: {str(e)}")
