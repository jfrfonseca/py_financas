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
"""Operacoes de recuperacao de cadastros de fundos da CVM"""


"""
# IMPORTS
"""


# Biblioteca padrao
import logging

# Dependencias PIP
import requests
import xmltodict
import numpy as np
import pandas as pd

# Dependencias locais
from py_financas import _utils


"""
# PAYLOAD
"""


def recupera_cadastros(usuario_cvm, senha_cvm,
                       data_busca=_utils.unidades_brasileiras.ultimo_dia_util(),
                       justificativa='Obtencao de cadastros de cvm'):

    # Inicializamos o objeto de log
    log = logging.getLogger('py_financas:cvm')

    # Inicializamos um cliente com a CVM
    cliente_wsdl_cvm = _utils.inicializa_cliente_wsdl_cvm(usuario_cvm, senha_cvm)

    # Solicitamos uma URL para download do documento de cadastros dos cvm
    url_documento = cliente_wsdl_cvm.service.solicAutorizDownloadCadastro(data_busca.strftime("%Y-%m-%d"), justificativa)

    log.debug("Obtida a URL de download de cadastros de cvm ({}) para o dia {}".format(url_documento, data_busca))

    # Recuperamos o documento da URL
    documento_fundos_raw = requests.get(url_documento).content

    log.debug("Recuperado o documento de cadastros de cvm de {}".format(data_busca))

    # Extraimos o conteudo do documento (Zipado) para uma string XML
    documento_fundos = _utils.le_arquivo_zip_de_string(documento_fundos_raw)

    # Convertemos o documento XML para um dicionario Python
    dict_fundos = xmltodict.parse(documento_fundos)

    # Convertemos o dicionario para um objeto PANDAS
    cadastros_fundos = pd.DataFrame().from_dict(dict_fundos['ROOT']['PARTICIPANTES']['CADASTRO'])

    log.debug("Obtidos os cadastros de {} cvm".format(len(cadastros_fundos.index)))

    # Normalizamos os valores booleanos dos cadastros
    cadastros_fundos = cadastros_fundos.replace(u'Sim', True)
    cadastros_fundos = cadastros_fundos.replace(u'Não', False)

    # Inicializamos buffers para a taxa de performance e seus detalhes
    lista_taxa_performance = []
    lista_detalhes_taxa_performance = []

    # Para cada elemento da coluna da taxa de performance
    for tp in cadastros_fundos['TAXA_PERFORMANCE'].fillna('0.0'):

        # Dividimos o elemento e capturamos sua primeira parte (numerica)
        divisao = tp.split(' ', 1)
        tp_numerica = divisao[0]

        # Se houver, capturamos a segunda parte (textual)
        if len(divisao) > 1:
            detalhe = divisao[1]
        else:
            # Se nao houver, a parte textual e um np.NaN
            detalhe = np.NaN

        # Inserimos as duas partes normalizadas nos buffers
        lista_taxa_performance.append(float(tp_numerica.replace(',', '.')))
        lista_detalhes_taxa_performance.append(detalhe)

    # Aplicamos normalizações no dataframe por coluna
    cadastros_fundos = cadastros_fundos.assign(

        # Parseamos as colunas de data como objetos DATETIME (naive)
        DT_INICIO = pd.to_datetime(cadastros_fundos['DT_INICIO']),
        DT_CONSTITUICAO = pd.to_datetime(cadastros_fundos['DT_CONSTITUICAO']),
        DT_INICIO_CLASSE = pd.to_datetime(cadastros_fundos['DT_INICIO_CLASSE']),

        # Normalizamos os campos CNPJ como strings de 14 digitos numericos, inserindo zeros a esquerda
        CNPJ = cadastros_fundos['CNPJ'].apply(_utils.normaliza_cnpj),
        CNPJ_ADMINISTRADOR = cadastros_fundos['CNPJ_ADMINISTRADOR'].apply(_utils.normaliza_cnpj),

        # Normalizamos a taxa de performance como valores numericos, inserindo taxa 0 nos valores numericos
        TAXA_PERFORMANCE = lista_taxa_performance,

        # Normalizamos o texto detahado da taxa de performance, inserindo strings vazias nas posicoes faltantes
        DETALHE_TAXA_PERFORMANCE = lista_detalhes_taxa_performance
    )

    # Retornamos o dataframe, com sorte sem problemas de normalização
    return cadastros_fundos
