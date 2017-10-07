#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2017 jfrfonseca
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Recuperacao de dados de indices a partir do sistema BCB SGS"""


"""
# IMPORTS
"""


# Biblioteca padrão
import difflib

# Dependencias PIP
from suds.client import Client, WebFault  # Recuperacao de dados
import xmltodict  # Parsing dos dados
import numpy as np  # Parsing dos dados
import pandas as pd  # Parsing dos dados
from unidecode import unidecode  # Parsing dos dados

# Este pacote
from py_financas import constantes, _utils


"""
# UTIL
"""


def normaliza_xml(xml):

    # Parseamos o XML como um dicionario pyhton, e identificamos so os valores desejados
    resultado = xmltodict.parse(xml)['SERIES']['SERIE']['ITEM']

    # Normalizamos o tipo dos resultados desejados como lista e retornamos
    if not isinstance(resultado, list):
        return [resultado]
    else:
        return resultado


def _inicializa_tabela_bcb():

    # Inicializamos um dataframe com a tabela de codigos BCB
    df = pd.read_csv('../py_financas/bcb_sgs/tabela_de_codigos_sistemas_web_banco_central_do_brasil.csv',
                     sep=',', header=None, index_col=0).T

    # Montamos diversas variacoes da grafia das strings passadas no arquov CSV
    result = {}
    for coluna in df.columns:

        # Removemos a calitalizacao e os acentos, elementos duplicados e valores nulos, exportando como tipo lista
        result[coluna] = df[coluna].dropna().apply(lambda stri: unidecode(stri.lower())).drop_duplicates().tolist()

    # Salvamos o resultado num DataFrame do modulo de constantes, apos parsear o dicionario acima
    constantes.df_tabela_codigos_bcb = pd.DataFrame().from_dict(result, orient='index').T.fillna(value=np.NaN)


def normaliza_codigo_indice(nome_indice):

    # Inicializamos a tabela de codigos BCB, caso a mesma ainda nao exista
    if constantes.df_tabela_codigos_bcb is None:
        _inicializa_tabela_bcb()

    # Se o nome do indice for um dos codigos da tabela
    if nome_indice in constantes.df_tabela_codigos_bcb.columns:

        # Normalizamos o tipo do codigo indice como inteiro
        codigo_indice = int(nome_indice)

    else:
        # Formatamos o nome passado como uma string sem capitalizacao nem acentos
        nome_indice = unidecode(str(nome_indice).lower())
        try:
            # Identificamos a primeira coluna do dataframe que contenha o nome exato informado
            codigo_indice = int(next(coluna for coluna in constantes.df_tabela_codigos_bcb.columns
                                     if nome_indice in constantes.df_tabela_codigos_bcb[coluna]))
        except StopIteration:
            # No caso de termos um erro de fim de iteração, nenhuma das colunas do dataframe tem um match exato :(
            # Portanto, sera necessario fazer um match aproximado
            try:
                codigo_indice = int(next(
                    coluna for coluna in constantes.df_tabela_codigos_bcb.columns

                    # Recuperamos a primeira coluna que tenha algum elemento parecido o bastante com o nome requisitado
                    if len(difflib.get_close_matches(nome_indice,
                                                     constantes.df_tabela_codigos_bcb[coluna].dropna(),
                                                     n=1, cutoff=constantes.proximidade_nome_indice)) > 0
                ))
            except StopIteration:

                # Nao conseguimos encontrar o codigo do indice e nao temos mais alternativas :( Interrompemos a funcao
                raise KeyError("Nao foi possivel identificar o indice {}".format(nome_indice))
    return codigo_indice


"""
# PAYLOAD
"""


def recupera_indice(nome_indice, data_inicio, data_fim=_utils.ultimo_dia_util()):

    # Validamos a entrada
    assert data_inicio <= data_fim, "Data {} nao e anterior a data {}".format(data_inicio, data_fim)

    # Normalizamos o nome do indice recebido como uma lista
    if not isinstance(nome_indice, list):
        nome_indice = [nome_indice]

    # Traduzimos os codigos dos bcb_sgs buscados
    lista_codigos_indices = [normaliza_codigo_indice(indice) for indice in nome_indice]

    # Inicializamos um cliente SUDS WSDL apontado para o arquivo WSDL da plataforma BCB SGS
    server = Client(constantes.wsdl_bcb)

    # Inicializamos um buffer para os resultados
    buffer_series = []

    # Para cada codigo de indice a ser recuperado
    for codigo_indice, nome_recebido_indice in zip(lista_codigos_indices, nome_indice):
        try:
            string_xml = server.service.getValoresSeriesXML([int(codigo_indice)],
                                                            data_inicio.strftime('%d/%m/%Y'),
                                                            data_fim.strftime('%d/%m/%Y'))

            # Formatamos o resultado do codigo atual
            valores = normaliza_xml(string_xml)

            # Formatamos a lista de valores recuperada como uma Serie Pandas
            serie = pd.Series(pd.to_numeric([v['VALOR'] for v in valores]),
                              index=pd.to_datetime([v['DATA'] for v in valores], dayfirst=True),
                              name=nome_recebido_indice)
            buffer_series.append(serie)

        # No caso de nao termos recuperado nenhum dado para o indice atual, o ignoramos
        except WebFault as wbf_i:
            if 'Value(s) not found' in str(wbf_i):
                pass
            else:
                raise wbf_i

    # Apos o loop, unificamos as series como um dataframe que retornamos
    return pd.DataFrame(buffer_series).T
