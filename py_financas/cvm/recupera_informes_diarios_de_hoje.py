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
"""Operacoes de recuperacao de dados diarios de fundos"""


"""
# IMPORTS
"""


# Biblioteca padrao
import json
import logging

# Dependencias PIP
import xmltodict
import requests
import pandas as pd

# Este pacote
from py_financas import _utils, constantes


"""
# PAYLOAD
"""


def recupera_informes_diarios_de_hoje(usuario_cvm, senha_cvm,
                                      justificativa='Obtencao de informes diarios de cvm'):

    # Inicializamos o objeto de log
    log = logging.getLogger('py_financas:cvm')

    # Testamos se o dia de hoje e um dia util
    if not _utils.unidades_brasileiras.e_dia_util():

        # Se nao, interrompemos a funcao imediatamente
        log.debug("Hoje nao e um dia util. Nao e possivel recuperar os informes diarios de cvm de hoje do sistema CVM")
        return pd.DataFrame()

    # Inicializamos um cliente com a CVM
    cliente_wsdl_cvm = _utils.inicializa_cliente_wsdl_cvm(usuario_cvm, senha_cvm)

    # Solicitamos uma URL para download do documento de informes diarios dos cvm
    url_documento = cliente_wsdl_cvm.service.solicAutorizDownloadArqEntrega(constantes.codigo_informes_diarios_fundos,
                                                                            justificativa)

    log.debug("Obtida a URL para download dos informes diarios de cvm: {}".format(url_documento))

    # Recuperamos o documento da URL
    documento_fundos_raw = requests.get(url_documento).content

    log.debug("Recuperado o documento de informes diarios de cvm do ultimo dia util")

    # Extraimos o conteudo do documento (Zipado) para uma string XML
    documento_fundos = _utils.le_arquivo_zip_de_string(documento_fundos_raw)

    # Convertemos o documento XML para um dicionario Python
    dict_fundos = xmltodict.parse(documento_fundos)

    # Obtemos o valor dos informes. Se um campo interno for nulo, retornamos um dataframe vazio
    valor = dict_fundos['ROOT']
    if valor is not None:
        valor = valor['INFORMES']
        if valor is not None:
            valor = valor['INFORME_DIARIO']
        else:
            return pd.DataFrame()
    else:
        return pd.DataFrame()

    # Se chegamos ate aqui, devemos continuar.
    # Normalizamos o tamanho minimo da lista
    if not isinstance(valor, list):
        valor = [valor]

    # Convertemos o dicionario para um objeto PANDAS
    dataframe_informes_fundos = pd.DataFrame().from_dict(valor)

    # Normalizamos varias colunas no dataframe
    dataframe_informes_fundos = dataframe_informes_fundos.assign(

        # Normalizamos as colunas numericas
        CAPTC_DIA = pd.to_numeric(dataframe_informes_fundos['CAPTC_DIA'].apply(_utils.normaliza_numerico)),
        NR_COTST = pd.to_numeric(dataframe_informes_fundos['NR_COTST'].apply(_utils.normaliza_numerico)),
        PATRIM_LIQ = pd.to_numeric(dataframe_informes_fundos['PATRIM_LIQ'].apply(_utils.normaliza_numerico)),
        RESG_DIA = pd.to_numeric(dataframe_informes_fundos['RESG_DIA'].apply(_utils.normaliza_numerico)),
        VL_QUOTA = pd.to_numeric(dataframe_informes_fundos['VL_QUOTA'].apply(_utils.normaliza_numerico)),
        VL_TOTAL = pd.to_numeric(dataframe_informes_fundos['VL_TOTAL'].apply(_utils.normaliza_numerico)),

        # Normalizamos as colunas de datas
        DT_COMPTC = pd.to_datetime(dataframe_informes_fundos['DT_COMPTC']),

        # Normalizamos a coluna de CNPJ
        CNPJ_FDO = dataframe_informes_fundos['CNPJ_FDO'].append(_utils.normaliza_cnpj)
    )

    # Retornamos o dataframe normalizado
    return dataframe_informes_fundos
