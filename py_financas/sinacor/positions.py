

# STDLib
from typing import List, Dict, Tuple

# PIP
from pandas import read_excel, to_datetime

# This package
from py_financas.sinacor.parser import parse_notas_corretagem
from py_financas.sinacor.types import Operacao, Posicao, NotaCorretagem


def parse_operacoes_manuais(arquivo_excel_operacoes_manuais:str) -> Dict[Tuple[str,str],Operacao]:

    # Read and normalize the data
    df_operacoes_manuais = read_excel(arquivo_excel_operacoes_manuais)
    df_operacoes_manuais['data'] = to_datetime(df_operacoes_manuais['data']).dt.date
    df_operacoes_manuais = df_operacoes_manuais.sort_values('data').reset_index(drop=True).copy(deep=True)
    df_operacoes_manuais['quantidade'] = df_operacoes_manuais['quantidade'].astype(float)
    df_operacoes_manuais['valor_unitario'] = df_operacoes_manuais['valor_unitario'].astype(float)
    df_operacoes_manuais['valor_total'] = df_operacoes_manuais['valor_unitario'] * df_operacoes_manuais['quantidade']
    df_operacoes_manuais['cnpj_corretora'] = df_operacoes_manuais['cnpj_corretora'].astype(str).str.split().str[0].astype(str)

    # Parse each operation
    operacoes_manuais = {}
    for idx, linha in df_operacoes_manuais.dropna().iterrows():
        data = linha['data']
        cnpj = str(linha['cnpj_corretora']).split('.')[0]
        op = Operacao(
            _nota_numero=int(idx),
            _nota_data_pregao=data,
            _nota_corretora_cnpj=cnpj,

            titulo=linha['titulo'],
            preco_ajuste=linha['valor_unitario'],
            quantidade=linha['quantidade'],
            valor_operacao_ajuste=linha['valor_total'],
            compra_venda=linha['compra_ou_venda'],
            debito_credito='debito' if (linha['compra_ou_venda'] == 'compra') else 'credito',
            tipo_mercado=linha['tipo_mercado'],
            negociacao='bovespa',
            especificacao_titulo=('','',''),
            observacao=linha['observacoes']
        )
        key = (cnpj, op.chave_titulo)
        if key not in operacoes_manuais: operacoes_manuais[key] = []
        operacoes_manuais[key].append(op)

    return operacoes_manuais


def parse_posicoes_de_operacoes(todas_as_operacoes:Dict[Tuple[str,str],List[Operacao]]) -> List[Posicao]:

    # Parse the positions
    posicoes: Dict[Tuple[str,str],List[Posicao]] = {}
    for chave, operacoes in todas_as_operacoes.items():
        cnpj, titulo = chave
        cnpj = str(cnpj).split('.')[0]
        operacoes = sorted(operacoes, key=lambda op: op._nota_data_pregao)

        # Criando a posição inicial
        if chave not in posicoes:
            op = operacoes[0]
            posicoes[chave] = [
                Posicao(
                    corretora=str(cnpj).split('.')[0],
                    chave_operacao_abertura=op.chave,
                    titulo=op.titulo,
                    especificacao_titulo=op.especificacao_titulo,
                    observacao_titulo=op.observacao,
                    tipo_mercado=op.tipo_mercado,

                    data_abertura=op._nota_data_pregao,
                    data_fechamento=None,

                    quantidade=op.quantidade,
                    valor_unitario=op.preco_ajuste
                )
            ]
            operacoes = operacoes[1:]  # Evitamos inserir a primeira OP novamente

        # Atualizando a posição a partir das operações
        for op in operacoes:
            if posicoes[chave][-1].aberta:
                posicoes[chave][-1].atualizar(op)
                continue

            # Criacao de nova posicao do titulo, após fechamento
            else:
                posicoes[chave].append(
                    Posicao(
                        corretora=cnpj,
                        chave_operacao_abertura=op.chave,
                        titulo=op.titulo,
                        especificacao_titulo=op.especificacao_titulo,
                        observacao_titulo=op.observacao,
                        tipo_mercado=op.tipo_mercado,

                        data_abertura=op._nota_data_pregao,
                        data_fechamento=None,

                        quantidade=op.quantidade,
                        valor_unitario=op.preco_ajuste
                    )
                )

    return sorted(sum(posicoes.values(), []))


def parse_posicoes_de_notas_de_corretagem(obj_notas_corretagem:List[NotaCorretagem]) -> List[Posicao]:

    # Extract the operations from the automatic files
    operacoes_automaticas = {}
    for nota in sorted(obj_notas_corretagem):
        for folha in nota.operacoes:
            for op in folha:
                chave = (str(nota.corretora.cnpj).split('.')[0],op.chave_titulo)
                if chave in operacoes_automaticas:
                    operacoes_automaticas[chave].append(op)
                else: operacoes_automaticas[chave] = [op]

    return parse_posicoes_de_operacoes(operacoes_automaticas)


def parse_posicoes(arquivos_pdf_notas_corretagem:List[str],
                   arquivos_excel_operacoes_manuais:List[str]) -> List[Posicao]:

    # Parse all the Notas de Corretagem as NotaCorretagem objects
    obj_notas_corretagem = parse_notas_corretagem(arquivos_pdf_notas_corretagem)

    # Extract the operations from the automatic files
    operacoes_automaticas = {}
    for nota in sorted(obj_notas_corretagem):
        for folha in nota.operacoes:
            for op in folha:
                chave = (str(nota.corretora.cnpj).split('.')[0],op.chave_titulo)
                if chave in operacoes_automaticas:
                    operacoes_automaticas[chave].append(op)
                else: operacoes_automaticas[chave] = [op]

    # Extract the operations from the manual files
    operacoes_manuais = {}
    for arq in arquivos_excel_operacoes_manuais:
        for k,v in parse_operacoes_manuais(arq).items():
            if k in operacoes_manuais:
                operacoes_manuais[k].extend(v)
            else: operacoes_manuais[k] = v

    # Merge all operations
    todas_as_operacoes = {}
    todas_as_operacoes.update(operacoes_manuais)
    for k,v in operacoes_automaticas.items():
        todas_as_operacoes[k] = todas_as_operacoes.get(k, []) + v
    todas_as_operacoes = {k:sorted(v, key=lambda op: op._nota_data_pregao)
                          for k,v in todas_as_operacoes.items()}

    return parse_posicoes_de_operacoes(todas_as_operacoes)
