
# STDLib
from time import time
from itertools import cycle
from datetime import date, timedelta
from typing import Literal, Tuple, List, Dict, Union

# PIP
from pydantic.dataclasses import dataclass, Field


# CONSTANTS
#######################################################################################################################


DC = Literal['debito', 'credito']


# UTILS
#######################################################################################################################


def validate_cnpj(cnpj: str) -> bool:
    if not cnpj.isdigit(): raise TypeError('ONLY CNPJ NUMERALS ARE ALLOWED')
    if len(cnpj) != 14: return False  # All CNPJ codes must have 14 numerals
    if len(set(cnpj)) == 1: return False  # 14 repetitions not allowed

    cnpj_r = cnpj[::-1]
    for i in range(2, 0, -1):
        cnpj_enum = zip(cycle(range(2, 10)), cnpj_r[i:])
        dv = sum(map(lambda x: int(x[1]) * x[0], cnpj_enum)) * 10 % 11
        if cnpj_r[i - 1:i] != str(dv % 10):
            return False

    return True


def validate_positive(key:str, value:float):
    assert value >= 0, f'{key} VALUE {value} SHOULD NOT BE NEGATIVE'


def validate_equal(key_a:str, value_a:float, key_b:str, value_b:float):
    assert value_a == value_b, f'{key_a} VALUE {value_a} SHOULD EQUAL {key_b} VALUE {value_b}'


def to_float(val:str, empty_string_equals=0.0) -> float:
    if val == '': return empty_string_equals
    return float(val.strip().replace('.', '').replace(',', '.'))


def to_DC(val:str, default='') -> str: return {'D': 'debito', 'C': 'credito'}.get(val.strip().upper(), default)


def printreal(_valor:float) -> str:
    valor = str(round(_valor,2))
    if '.' in valor:
        reais, centavos = valor.split('.')
        while len(centavos) < 2: centavos += '0'
    else:
        reais = valor
        centavos = '00'
    result = ','+centavos
    while len(reais) > 0:
        result = '.'+reais[-3:]+result
        reais = reais[:-3]
    return result[1:]


# DATA CLASSES (TYPES)
#######################################################################################################################


@dataclass
class Corretora():
    nome: str
    cnpj: str
    estado: Literal['BA', 'DF', 'MG', 'PE', 'RJ', 'RS', 'SP']

    def __repr__(self) -> str: return self.nome
    def __str__(self) -> str: return self.__repr__()

    def __post_init__(self):
        assert validate_cnpj(self.cnpj), f'INVALID CNPJ: {self.cnpj}'


@dataclass
class Operacao():
    _nota_numero: int
    _nota_data_pregao: date
    _nota_corretora_cnpj: str

    titulo: str
    preco_ajuste: float
    quantidade: float
    valor_operacao_ajuste: float
    compra_venda: Literal['compra', 'venda', 'desdobramento']
    debito_credito: DC
    tipo_mercado: Literal['vista', 'fracionario', 'prazo']
    negociacao: Literal['bovespa', 'bovespa 1']
    especificacao_titulo: Tuple[str,str,str]
    observacao: str

    @property
    def chave_titulo(self) -> str:
        tm = self.tipo_mercado
        if tm == 'fracionario': tm = 'vista'
        return f'{self.titulo}:{tm}'
        #chave = ' '.join([
        #    esp.strip()
        #    for esp in list(op.especificacao_titulo) + [self.observacao]
        #    if len(esp.strip()) > 0
        #])
        #return f'{self.titulo}:{chave}:{self.tipo_mercado}'

    @property
    def chave(self) -> str:
        return f'{self._nota_data_pregao}:{self._nota_corretora_cnpj}:{self._nota_numero}:{self.chave_titulo}:{self.compra_venda}:{self.quantidade}:{self.preco_ajuste}'


@dataclass
class Totais():
    liquido: float
    liquido_DC: DC
    vendas_vista: float
    compras_vista: float
    opcoes_compras: float
    opcoes_vendas: float
    debentures: float
    operacoes: float
    operacoes_termo_bolsa: float
    operacoes_titulos_publicos: float
    valor_liquido_operacoes: float
    valor_liquido_operacoes_DC: DC
    cblc: float
    cblc_DC: DC
    bovespa_soma: float
    bovespa_soma_DC: DC
    corretagem_despesas: float
    corretagem_despesas_DC: DC

    def __post_init__(self):
        validate_positive('COMPRAS VISTA', self.compras_vista)
        validate_positive('VENDAS VISTA', self.vendas_vista)
        validate_positive('OPCOES COMPRAS', self.opcoes_compras)
        validate_positive('OPCOES VENDAS', self.opcoes_vendas)
        validate_positive('DEBENTURES', self.debentures)
        validate_positive('OPERACOES', self.operacoes)
        validate_positive('OPERACOES TERMO BOLSA', self.operacoes_termo_bolsa)
        validate_positive('OPERACOES TITULOS PUBLICOS', self.operacoes_titulos_publicos)


@dataclass
class Custos():
    taxa_liquidacao: float
    taxa_liquidacao_DC: DC
    taxa_registro: float
    taxa_registro_DC: DC
    taxa_termo_opcoes: float
    taxa_termo_opcoes_DC: DC
    taxa_ana: float
    taxa_ana_DC: DC
    emolumentos: float
    emolumentos_DC: DC
    clearing: float
    clearing_DC: DC
    execucao: float
    execucao_DC: DC
    execucao_casa: float
    execucao_casa_DC: DC
    outras: float
    outras_DC: DC

    @staticmethod
    def null() -> 'Custos': return Custos(0,'debito',0,'debito',0,'debito',
                                          0,'debito',0,'debito',0,'debito',
                                          0,'debito',0,'debito',0,'debito')


@dataclass
class Impostos():
    iss: float
    iss_DC: DC
    irrf: float
    irrf_DC: DC
    irrf_base: float

    def __post_init__(self):
        validate_positive('IRRF BASE', self.irrf_base)

    @staticmethod
    def null() -> 'Impostos': return Impostos(0,'debito',0,'debito',0)


@dataclass
class NotaCorretagem():
    _raw_content: str

    numero : int
    numero_nota_substitutiva: int
    data_pregao: date
    data_liquidacao: date
    corretora: Corretora
    cliente: str
    quantidade_folhas: int

    operacoes: List[List[Operacao]]

    totais: Totais
    custos: Custos
    impostos: Impostos

    def __post_init__(self):
        assert self.data_pregao <= self.data_liquidacao, f'DATA DO PREGAO {self.data_pregao} NAO PODE SER MAIOR QUE DATA DA LIQUIDACAO {self.data_liquidacao}'
        assert (self.data_liquidacao - self.data_pregao) <= timedelta(days=7), f'DATA DO PREGAO {self.data_pregao} MUITO ANTERIOR A DATA DA LIQUIDACAO {self.data_liquidacao}'
        assert self.quantidade_folhas == len(self.operacoes), f'QUANTIDADE DE FOLHAS INCONSISTENTE COM A QUANTIDADE DE CONJUNTOS DE OPERACOES'

    def __len__(self) -> int:
        return sum([len(pg) for pg in self.operacoes])

    @property
    def key(self) -> str:
        return self.data_pregao.strftime(f'%Y-%m-%d {self.corretora} {self.numero}')

    def __repr__(self) -> str:
        return f'<NC {self.key} [{len(self)}] ${self.totais.liquido} {self.totais.liquido_DC}>'

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, other) -> bool: return self.key == other.key
    def __lt__(self, other) -> bool: return self.key < other.key

    @staticmethod
    def manual(
        data_pregao:date, corretora:Corretora, cliente:str,
        operacoes:List[Operacao], totais:Totais,
        impostos:Impostos=None, custos:Custos=None,  #type:ignore
        data_liquidacao=None,
        numero=None, numero_nota_substitutiva=None,
        quantidade_folhas=1,
        _raw_content='Nota de corretagem inserida manualmente',
    ) -> 'NotaCorretagem':
        if numero is None: numero = int(time())
        if data_liquidacao is None: data_liquidacao = data_pregao
        if numero_nota_substitutiva is None: numero_nota_substitutiva = numero
        if impostos is None: impostos = Impostos.null()
        if custos is None: custos = Custos.null()
        if totais is None: totais = Totais.null()  #type:ignore
        return NotaCorretagem(
            _raw_content=_raw_content, numero=numero,
            data_pregao=data_pregao, data_liquidacao=data_liquidacao,
            numero_nota_substitutiva=numero_nota_substitutiva,
            corretora=corretora, cliente=cliente,
            quantidade_folhas=quantidade_folhas,
            operacoes=operacoes, impostos=impostos, custos=custos, totais=totais  #type:ignore
        )


@dataclass
class MomentoPosicao():
    chave_operacao: str
    data: date
    quantidade: float
    valor_unitario: float
    rendimento: float

    @property
    def valor_total(self) -> float: return round(self.quantidade * self.valor_unitario, 2)


@dataclass
class Posicao():
    corretora: str
    titulo: str
    especificacao_titulo: Tuple[str, str, str]
    observacao_titulo: str
    tipo_mercado: str
    chave_operacao_abertura: str

    data_abertura: date
    data_fechamento: Union[date, None]

    quantidade: float
    valor_unitario: float

    historico: List[MomentoPosicao] = Field(default_factory=list)
    fechamentos: Dict[date,float] = Field(default_factory=dict)

    def __post_init__(self):
        self.historico.append(
            MomentoPosicao(
                self.chave_operacao_abertura,
                self.data_abertura,
                self.quantidade,
                self.valor_unitario,
                0.0
            )
        )

    @property
    def aberta(self) -> bool: return self.data_fechamento is None

    @property
    def valor_total(self) -> float: return round(self.valor_unitario * self.quantidade, 2)

    @property
    def rendimento(self) -> float: return round(self.historico[-1].rendimento, 2)

    @property
    def chave_titulo(self) -> str:
        return f'{self.titulo}:{self.tipo_mercado}'
        #chave = ' '.join([
        #    esp.strip()
        #    for esp in list(op.especificacao_titulo) + [self.observacao_titulo]
        #    if len(esp.strip()) > 0
        #])
        #return f'{self.titulo}:{chave}:{self.tipo_mercado}'

    @property
    def chave(self) -> str:
        return f'{self.corretora}:{self.chave_titulo}:{self.data_abertura}:{self.data_fechamento}'

    def __repr__(self) -> str:
        return f'<POS {self.chave} [{len(self.historico)}|{len(self.fechamentos)}] ${self.valor_total}={round(self.quantidade, 2)}x{round(self.valor_unitario, 2)} ({self.rendimento})>'

    def __str__(self) -> str: return self.__repr__()

    def __eq__(self, other) -> bool: return self.__repr__() == other.__repr__()
    def __lt__(self, other) -> bool:
        for attr in ['data_abertura',
                     'corretora', 'chave_titulo',
                     'data_fechamento',
                     'valor_total', 'rendimento']:
            ours = getattr(self, attr)
            theirs = getattr(other, attr)
            if ours != theirs:
                return ours < theirs
        return self.__repr__ < other.__repr__

    def atualizar(self, op:Operacao) -> bool:
        data_pregao = op._nota_data_pregao

        # Sanity checks
        assert op._nota_corretora_cnpj == self.corretora, f'TENTATIVA DE ATUALIZAR UMA POSIÇÃO DE OUTRA CORRETORA! {self.chave}'
        assert op.chave_titulo == self.chave_titulo, f'TENTATIVA DE ATUALIZAR POSIÇÃO COM OPERAÇÃO DE OUTRO TÍTULO! {self.chave}'
        assert self.aberta, f'TENTATIVA DE ATUALIZAR UMA POSICÃO FECHADA! {self.chave}'
        assert data_pregao >= self.data_abertura, f'TENTATIVA DE ATUALIZAR UMA POSIÇÃO COM UMA OPERAÇÃO MAIS ANTIGA! {self.chave}'

        # Se estamos numa COMPRA, atualizamos a quantidade e o valor unitário médio
        if op.compra_venda == 'compra':
            valor_agregado = abs(op.valor_operacao_ajuste)
            quantidade_agregada = abs(op.quantidade)

            valor_atual = self.valor_total
            quantidade_atual = self.quantidade

            novo_valor = valor_atual + valor_agregado
            nova_quantidade = self.quantidade + quantidade_agregada
            novo_valor_unitario = novo_valor / nova_quantidade

            rendimento_agregado = 0.0
            self.valor_unitario = novo_valor_unitario
            self.quantidade = nova_quantidade

        # Se estamos numa venda:
        #   - Atualizamos apenas a quantidade
        #   - Criamos um novo rendimento / fechamento parcial
        #   - Se a quantidade vai a 0, fechamos a posição
        elif op.compra_venda == 'venda':
            valor_unitario_recebido = abs(op.preco_ajuste)
            quantidade_removida = abs(op.quantidade)

            valor_unitario_atual = self.valor_unitario
            quantidade_atual = self.quantidade

            rendimento_agregado = (valor_unitario_recebido - valor_unitario_atual) * quantidade_removida
            nova_quantidade = self.quantidade - quantidade_removida

            self.quantidade = nova_quantidade
            self.fechamentos[data_pregao] = self.fechamentos.get(data_pregao, 0.0) + rendimento_agregado

            if self.quantidade == 0:
                self.data_fechamento = data_pregao

        # Se estamos num DESDOBRAMENTO, atualizamos a quantidade e o valor unitário médio
        elif op.compra_venda == 'desdobramento':
            quantidade_agregada = (
                int(self.quantidade * op.preco_ajuste)
                - self.quantidade
            )

            novo_valor = self.valor_total + 0.0
            nova_quantidade = self.quantidade + quantidade_agregada
            novo_valor_unitario = novo_valor / nova_quantidade

            rendimento_agregado = 0.0
            self.valor_unitario = novo_valor_unitario
            self.quantidade = nova_quantidade

        else: raise KeyError(f'Tipo desconhecido de operação: '+op.compra_venda)

        # Anotamos a nova situação no histórico
        self.historico.append(
            MomentoPosicao(
                op.chave,
                data_pregao,
                self.quantidade,
                self.valor_unitario,
                self.rendimento + rendimento_agregado
            )
        )

        # Retornamos se a posição atual está aberta
        return self.aberta

    def narrativa(self, _print=True) -> Union[None,str]:
        story = [
            f'Posição do título {self.titulo} na corretora {self.corretora}',
            f'\tAberta em {self.data_abertura}' + (
                ', e permanece aberta.'
                if self.aberta else
                f', e fechada em {self.data_fechamento}'
            )
        ]
        for mp in self.historico:
            _, cnpj, nota, _, _, tipo, quantidade, preco = mp.chave_operacao.split(':')
            story += [
                f'\t- {tipo.upper()} {quantidade} X R${printreal(float(preco))}',
                f'\t\tNota de Corretagem: {nota} de {mp.data}',
                f'\t\tSituação: {round(mp.quantidade,2)} X R${printreal(mp.valor_unitario)} = R${printreal(mp.valor_total)} (R${printreal(mp.rendimento)})'
            ]
        story = '\n'.join(story)
        if _print: print(story)
        else: return story

    def sumario(self, _print=True) -> Union[None,str]:
        story = [f'Posição do título {self.titulo} sob custódia da corretora CNPJ {self.corretora},',
                 f'aberta em {self.data_abertura},']
        if self.aberta:
            qtd = self.quantidade
            val = round(self.valor_unitario,2)
            story += [
                f'composta por {int(qtd)} unidades',
                f'de valor médio R${printreal(val)},',
                f'totalizando R${printreal(qtd*val)}.',
            ]
        else:
            story += [
                f'fechada em {self.data_fechamento},',
                f'com rendimento total de R${printreal(self.rendimento)}.'
            ]
        story = ' '.join(story)
        if _print: print(story)
        else: return story
