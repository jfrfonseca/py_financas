

# STDLib
import re
from datetime import datetime
from typing import Dict, List, Union, Tuple, Set

# PIP
import pdfplumber
import pandas as pd
from numpy import nan

# This package
from py_financas.sinacor.types import to_DC, to_float, \
    NotaCorretagem, Operacao, Corretora, Impostos, Custos, Totais


# CONSTANTS
#######################################################################################################################


date = '[0-9]{2}/[0-9]{2}/20[0-9]{2}'
cnpj = '[0-9]{2}\.[0-9]{3}\.[0-9]{3}/0001-[0-9]{2}'
text = '[a-zçáãâéêíóôõúA-ZÇÁÃÂÉÊÍÓÕÔÚ /,\.]'
ignore_line = '[^\n]+\n'
num = '[0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?'
Q = '(?:([^\s]+)\s+)?'
NEGOCIACAO = '((?:1-)?BOVESPA(?: 1)?)'
CV = '\s+(C|V)'
TIPO_MERCADO = '\s+(VISTA|FRACIONARIO)'
PRAZO = '(?:\s+([^\s]+))?'
TITULO = '\s+(.*)'
TIPO_TITULO = '\s+(CI|ON|PN)(?:[\s\t]*(E[D]?[JR]?))?(?:[\s\t]*(ER|ES|ON|NM|N[0-9]))?'
OBS = '(?:\s+([^\s]+))?'
QUANTIDADE = f'\s+({num})'
PRECO_AJUSTE = f'\s+({num})'
VALOR_OPERACAO_AJUSTE = f'\s+({num})'
DC = '\s+(D|C)'

rgx_header = re.compile(
    '^NOTA DE CORRETAGEM\n'
    +ignore_line
    +f'([0-9]+) ([0-9]+) ({date})\n'  # Numero Nota, Numero Folha, Data Pregao
    +f'({text}+)\n'  # Nome Corretora
    +ignore_line
    +'Tel'+ignore_line
    +'Internet'+ignore_line
    +f'[CNPJ\.:\s\t]+({cnpj})[^\n]+\n'  # CNPJ Corretora
    +'Ouvidoria'+ignore_line
    +'Cliente'+ignore_line
    +'([^\n]+)\n'  # Cliente
)

rgx_body = re.compile(
    'Negócios realizados\n'
    +'Q'+ignore_line
    +'((.*\n)+)'
    +'Resumo dos'+ignore_line
)

rgx_op = re.compile(
    f'^{Q}{NEGOCIACAO}{CV}{TIPO_MERCADO}{TITULO}{TIPO_TITULO}{OBS}{QUANTIDADE}{PRECO_AJUSTE}{VALOR_OPERACAO_AJUSTE}{DC}$'
)

rgx_footer = re.compile(
    f'Resumo dos Neg.*\n'
    f'Debêntures ({num}) Clearing\n'
    f'Vendas à vista ({num}) Valor líquido das operações ({num}){DC}\n'
    f'Compras à vista ({num}) Taxa de liquidação ({num}){DC}\n'
    f'Opções - compras ({num}) Taxa de Registro ({num}){DC}\n'
    f'Opções - vendas ({num}) Total CBLC ({num}){DC}\n'
    f'Operações à termo ({num}) Bolsa\n'
    f'Valor [^\n]+ títulos [^\n]+ ({num}) Taxa de [^\n]+ ({num}){DC}\n'
    f'Valor das operações ({num}) Taxa [^\n]+ ({num}){DC}\n'
    f'Emolumentos ({num}){DC}\n'
    f'Total Bovespa [^\n]+ ({num}){DC}\n'
    f'Especific[^\n]+\n'
    f'Clearing ({num}){DC}\n'
    f'A coluna Q indica [^\n]+ ({num}){DC}\n'
    f'(?:Esta nota substitui a nota nº ([0-9]+) )?Execução casa ({num}){DC}\n'
    f'ISS \(\s*(RIO DE JANEIRO|SÃO PAULO)\s*\) ({num})(?:{DC})?\n'
    f'(?:I\.R\.R\.F\. s. operações, base .. ({num}) ({num})(?:{DC})?\n)?'
    f'Outras ({num}){DC}\n'
    f'Total corretagem / Despesas ({num}){DC}\n'
    f'\(\*\) - Observações: A - Posição Futuro T - Liquidação pelo Bruto Líquido para ({date}) ({num}){DC}\n'
)


# UTILS
#######################################################################################################################


def read_pages(all_files:List[str]) -> List[str]:
    all_pages = []
    for filename in all_files:
        with pdfplumber.open(filename) as pdf:
            for page in pdf.pages:
                all_pages.append(page.extract_text())
    return all_pages


def validate_matches(valid_pages, matches):
  validation = [((not vp) or (m is not None))  # VP -> M (Modus Ponens)
                for vp,m in zip(valid_pages, matches)]
  if not all(validation):
      invalid = [i for i,val in enumerate(validation) if not val]
      raise AssertionError(f'SOME VALID PAGES WERE NOT PARSED! {invalid}')


def check_continuation(page):
    return 'C O N T I N U A . . .' in page


# PARSERS
#######################################################################################################################


def parse_header(all_pages:List[str], valid_pages:List[bool]) -> List[Dict[str,str]]:

    # Extract and validate the header sections in the pages
    header_sections = [
        m
        if ((m := rgx_header.findall(p)) is None)
        else (m[0] if (len(m) > 0) else None)
        for p in all_pages
    ]
    validate_matches(valid_pages, header_sections)

    # Parse the header objects
    headers = [
        {} if i is None else dict(zip([
            'nota_numero', 'nota_folha', 'nota_data',
            'corretora_nome', 'corretora_cnpj',
            'cliente'
        ], list(i)))
        for i in header_sections
    ]
    return headers


def parse_body(all_pages:List[str], valid_pages:List[bool]) -> List[List[Union[Dict[str,str], None]]]:

    # Extract and validate the body sections in the pages
    body_sections = [
        m
        if ((m := rgx_body.findall(p)) is None)
        else (m[0] if (len(m) > 0) else None)
        for p in all_pages
    ]
    body_sections = [b if (b is None) else b[0].splitlines() for b in body_sections]
    validate_matches(valid_pages, body_sections)

    # Extract and validate the operations sections in the body sections
    operation_sections = [
        i if (i is None) else [
            rgx_op.findall(j)
            for j in i
        ]
        for i in body_sections
    ]
    validate_matches(valid_pages, operation_sections)

    # Parse the body objects
    body_columns = [
        'q', 'negociacao', 'cv_compra_venda', 'tipo_mercado', # 'prazo',
        'especificacao_titulo_0',
        'especificacao_titulo_1',
        'especificacao_titulo_2',
        'especificacao_titulo_3',
        'observacao',
        'val_quantidade', 'val_preco_ajuste', 'val_valor_operacao_ajuste',
        'dc_debito_credito',
    ]
    body = [
        None if b is None else [dict(zip(body_columns, list(*l))) for l in b]
        for b in operation_sections
    ]
    validate_matches(valid_pages, body)

    # Validate the parsed operations in the body objects
    for page,b in enumerate(body):
        if b is None: continue
        for num_op,op in enumerate(b):
            assert len(op) == len(body_columns), f'Could not parse operation {num_op} in page {page} [\n\t{len(op)}\n\t{op}\n]'

    return body  #type:ignore


def parse_footer(all_pages:List[str], valid_pages:List[bool]) -> Tuple[List[Union[Dict[str,str],None]],List[bool]]:

    # Extract and validate the footer sections in the pages
    footer_sections = [
        m
        if ((m := rgx_footer.findall(p)) is None)
        else (m[0] if (len(m) > 0) else None)
        for p in all_pages
    ]
    footer_continuation = [check_continuation(p) for p in all_pages]
    footer_sections = [('' if cont else m) if (m is None) else m
                       for m,cont in zip(footer_sections, footer_continuation)]
    validate_matches(valid_pages, footer_sections)

    # Parse the footer objects
    footer = [
        None if i in {'', None} else dict(zip([
            'val_debentures',
            'val_vendas_vista', 'val_valor_liquido_operacoes', 'dc_valor_liquido_operacoes',
            'val_compras_vista', 'val_taxa_liquidacao', 'dc_taxa_liquidacao',
            'val_opcoes_compras', 'val_taxa_registro', 'dc_taxa_registro',
            'val_opcoes_vendas', 'val_total_cblc', 'dc_total_cblc',
            'val_operacoes_termo_bolsa',
            'val_operacoes_titulos_publicos', 'val_taxa_termo_opcoes', 'dc_taxa_termo_opcoes',
            'val_operacoes', 'val_taxa_ana', 'dc_taxa_ana',
            'val_emolumentos', 'dc_emolumentos',
            'val_total_bovespa_soma', 'dc_total_bovespa_soma',
            'val_clearing', 'dc_clearing',
            'val_execucao', 'dc_execucao',
            'nota_substituida', 'val_execucao_casa', 'dc_execucao_casa',
            'corretora_estado', 'val_iss', 'dc_iss',
            'val_base_irrf', 'val_irrf', 'dc_irrf',
            'val_outras', 'dc_outras',
            'val_total_corretagem_despesas', 'dc_total_corretagem_despesas',
            'nota_data_liquido', 'val_liquido', 'dc_liquido',
        ], list(i)))  #type:ignore
        for i in footer_sections
    ]
    validate_matches(valid_pages, footer)

    return footer, footer_continuation


def _base_parse_notas_corretagem(all_pages:List[str]) -> Tuple[List[Union[Dict[str,str],None]],
                                                               Set[str],Set[str],Set[str]]:

    # Prepare the buffers
    valid_pages = [(len(p.strip()) > 300) for p in all_pages]
    notas_corretagem = []
    header_columns = None
    body_columns = None
    footer_columns = None

    # Parse the sections
    header = parse_header(all_pages, valid_pages)
    body = parse_body(all_pages, valid_pages)
    footer, footer_continuation = parse_footer(all_pages, valid_pages)

    # Join as a single object
    pos = -1
    for h,b,f,cont,p in zip(header,body,footer,footer_continuation,all_pages):
        pos += 1

        # Skip invalid pages
        if len(h) == 0:
            assert b is None, 'OPERATIONS ON AN EMPTY HEADER'
            assert f is None, 'FOOTER ON AN EMPTY HEADER'
            notas_corretagem.append(None)
            continue

        # Assert column definition stability
        if header_columns is None:
            header_columns = set(h.keys())
        else: assert header_columns == set(h.keys())
        if body_columns is None:
            body_columns = set(b[0].keys())  #type:ignore
        else: assert body_columns == set(b[0].keys())  #type:ignore
        if not cont:
            if footer_columns is None:
                footer_columns = set(f.keys())  #type:ignore
            else: assert footer_columns == set(f.keys())  #type:ignore

        # Join the data
        if not cont:
            h.update(f)  #type:ignore
        assert not (cont and (f is not None)), 'IS CONTINUATION BUT HAS FOOTER'
        assert not ((not cont) and (f is None)), 'IS NOT CONTINUATION BUT HAS NO FOOTER'
        h.update({'dataset_page': pos, 'raw_page': p, 'has_continuation': cont, 'operations': b})  #type:ignore
        notas_corretagem.append(h)

    # Validate the entire dataset
    validate_matches(valid_pages, notas_corretagem)
    return notas_corretagem, header_columns, body_columns, footer_columns  #type:ignore


def parse_notas_corretagem(all_files:List[str]) -> List[NotaCorretagem]:

    # Read the files as strings
    all_pages = read_pages(all_files)

    # Base-parse and validate the file contents
    notas_corretagem, header_columns, body_columns, footer_columns = _base_parse_notas_corretagem(all_pages)

    # Format the individually-validated Notas de Corretagem as a dataframe
    df_notas_corretagem = pd.DataFrame([n for n in notas_corretagem if n is not None])

    # Group by Número da Nota and validate the many pages of the same Nota de Corretagem
    obj_notas_corretagem = []
    for nota_numero, sdf in df_notas_corretagem.groupby('nota_numero'):
        if len(sdf) == 1:
            lp_df = sdf

        # Validate this multi-page Nota de Corretagem\
        else:

            # Each page should appear just once
            assert len(sdf) == len(sdf['nota_folha'].unique()), f'REPEATED PAGES IN NOTA {nota_numero}'

            # All the values in each Header column must be equal
            for col in header_columns:
                if col == 'nota_folha': continue  # No need to validate the number of the page
                values = sdf[col].unique()
                assert len(values) == 1, f'DIFFERENT VALUES FOR HEADER COLUMN {col} OF NOTA {nota_numero}: {values}'

            # All pages must have operations
            for _, row in sdf.iterrows():
                nota_folha = row['nota_folha']
                assert len(row['operations']) > 0, f'NO OPERATIONS ON PAGE {nota_folha} OF NOTA {nota_numero}'

            # Only a single page (the last) should gave the footer
            last_page = sdf['nota_folha'].astype(int).max()
            assert last_page > 1, f'SINGLE PAGE IN NOTA {nota_numero}, THAT HAS {len(sdf)} ROWS!'
            null_df = sdf[sdf['nota_folha'] != str(last_page)][list(footer_columns)]
            lp_df = sdf[sdf['nota_folha'] == str(last_page)][list(footer_columns)]
            assert len(lp_df) == 1, f'MORE THAN ONE LAST PAGE {last_page} IN NOTA {nota_numero}'
            for col in footer_columns:
                null_values = set(null_df[col].unique())
                assert null_values == {nan}, f'NON-NULL VALUES IN FOOTER COLUMN {col} OF THE MIDDLE PAGES OF NOTA {nota_numero}: {null_values}'
                assert not lp_df[col].isnull().all(), f'NULL VALUE IN FOOTER COLUMN {col} OF THE LAST PAGE OF NOTA {nota_numero}'

        # This Nota de Corretagem has passed the group validations. Convert it to a NotaCorretagem object
        lr = lp_df.iloc[0]
        dataset_page = str(sdf.iloc[0]['dataset_page'])
        try:

            # Header
            _raw = sdf.iloc[0]['raw_page'].strip()
            nota_numero = int(sdf.iloc[0]['nota_numero'].strip())
            numero_nota_substitutiva = lp_df['nota_substituida'].fillna('').iloc[0].strip()
            if numero_nota_substitutiva == '': numero_nota_substitutiva = -1
            numero_nota_substitutiva = int(numero_nota_substitutiva)
            nota_data_pregao = datetime.strptime(sdf.iloc[0]['nota_data'].strip(), '%d/%m/%Y').date()
            nota_data_liquidacao = datetime.strptime(lr['nota_data_liquido'].strip(), '%d/%m/%Y').date()
            cliente = sdf.iloc[0]['cliente'].strip()
            cnpj = sdf.iloc[0]['corretora_cnpj'].strip()
            estado = lp_df['corretora_estado'].iloc[0].lower().strip()

            # Corretora
            corretora = Corretora(
                nome=sdf.iloc[0]['corretora_nome'].strip(),
                cnpj=str(''.join(i for i in cnpj if i.isdigit())).split('.')[0],
                estado={'são paulo': 'SP', 'rio de janeiro': 'RJ'}[estado]  #type:ignore
            )

            # Footer
            taxes = Impostos(
                iss=to_float(lr['val_iss']),
                iss_DC=to_DC(lr['dc_iss'], 'debito'),  #type:ignore
                irrf=to_float(lr['val_irrf']),
                irrf_base=to_float(lr['val_base_irrf']),
                irrf_DC=to_DC(lr['dc_irrf'], 'debito')  #type:ignore
            )
            costs = Custos(
                taxa_liquidacao=to_float(lr['val_taxa_liquidacao']),
                taxa_liquidacao_DC=to_DC(lr['dc_taxa_liquidacao'], 'debito'),  #type:ignore
                taxa_registro=to_float(lr['val_taxa_registro']),
                taxa_registro_DC=to_DC(lr['dc_taxa_registro'], 'debito'),  #type:ignore
                taxa_termo_opcoes=to_float(lr['val_taxa_termo_opcoes']),
                taxa_termo_opcoes_DC=to_DC(lr['dc_taxa_termo_opcoes'], 'debito'),  #type:ignore
                taxa_ana=to_float(lr['val_taxa_ana']),
                taxa_ana_DC=to_DC(lr['dc_taxa_ana'], 'debito'),  #type:ignore
                emolumentos=to_float(lr['val_emolumentos']),
                emolumentos_DC=to_DC(lr['dc_emolumentos'], 'debito'),  #type:ignore
                clearing=to_float(lr['val_clearing']),
                clearing_DC=to_DC(lr['dc_clearing'], 'debito'),  #type:ignore
                execucao=to_float(lr['val_execucao']),
                execucao_DC=to_DC(lr['dc_execucao'], 'debito'),  #type:ignore
                execucao_casa=to_float(lr['val_execucao_casa']),
                execucao_casa_DC=to_DC(lr['dc_execucao_casa'], 'debito'),  #type:ignore
                outras=to_float(lr['val_outras']),
                outras_DC=to_DC(lr['dc_outras'], 'debito'),  #type:ignore
            )
            totals = Totais(
                liquido=to_float(lr['val_liquido']),
                liquido_DC=to_DC(lr['dc_liquido'], 'credito'),  #type:ignore
                vendas_vista=to_float(lr['val_vendas_vista']),
                compras_vista=to_float(lr['val_compras_vista']),
                opcoes_compras=to_float(lr['val_opcoes_compras']),
                opcoes_vendas=to_float(lr['val_opcoes_vendas']),
                debentures=to_float(lr['val_debentures']),
                operacoes=to_float(lr['val_operacoes']),
                operacoes_termo_bolsa=to_float(lr['val_operacoes_termo_bolsa']),
                operacoes_titulos_publicos=to_float(lr['val_operacoes_titulos_publicos']),
                valor_liquido_operacoes=to_float(lr['val_valor_liquido_operacoes']),
                valor_liquido_operacoes_DC=to_DC(lr['dc_valor_liquido_operacoes'], 'credito'),  #type:ignore
                cblc=to_float(lr['val_total_cblc']),
                cblc_DC=to_DC(lr['dc_total_cblc'], 'credito'),  #type:ignore
                bovespa_soma=to_float(lr['val_total_bovespa_soma']),
                bovespa_soma_DC=to_DC(lr['dc_total_bovespa_soma'], 'credito'),  #type:ignore
                corretagem_despesas=to_float(lr['val_total_corretagem_despesas']),
                corretagem_despesas_DC=to_DC(lr['dc_total_corretagem_despesas'], 'credito'),  #type:ignore
            )

            # Operations
            operations = []
            for _, row in sdf.iterrows():
                operations.append([])
                for op in row['operations']:
                    operations[-1].append(Operacao(
                        _nota_numero=nota_numero, _nota_data_pregao=nota_data_pregao,
                        _nota_corretora_cnpj=str(corretora.cnpj).split('.')[0],
                        titulo=op['especificacao_titulo_0'].strip(),
                        preco_ajuste=to_float(op['val_preco_ajuste']),
                        quantidade=to_float(op['val_quantidade']),
                        valor_operacao_ajuste=to_float(op['val_valor_operacao_ajuste']),
                        compra_venda={'C': 'compra', 'V': 'venda'}[op['cv_compra_venda'].strip()],  #type:ignore
                        debito_credito=to_DC(op['dc_debito_credito']),  #type:ignore
                        tipo_mercado=op['tipo_mercado'].strip().lower(),
                        negociacao=op['negociacao'].strip().lower(),
                        especificacao_titulo=(
                            op['especificacao_titulo_1'].strip().upper(),
                            op['especificacao_titulo_2'].strip().upper(),
                            op['especificacao_titulo_3'].strip().upper()),
                        observacao=op['observacao'].strip()
                    ))

            # Nota de Corretagem
            obj_notas_corretagem.append(
                NotaCorretagem(
                    _raw_content=_raw, numero=nota_numero,
                    data_pregao=nota_data_pregao, data_liquidacao=nota_data_liquidacao,
                    numero_nota_substitutiva=numero_nota_substitutiva,
                    corretora=corretora, cliente=cliente, quantidade_folhas=len(sdf),
                    operacoes=operations, impostos=taxes, custos=costs, totais=totals
                )
            )

        except Exception as exp:
            raise Exception(f'On page {dataset_page}:\n\t{exp}')

    return obj_notas_corretagem
