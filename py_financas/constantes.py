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
"""Constantes reutilizadas nos sub-pacotes"""


"""
# CONFIG
"""


# Enderecos das definicioes WSDL
wsdl_cvm = 'http://sistemas.cvm.gov.br/webservices/Sistemas/SCW/CDocs/WsDownloadInfs.asmx?WSDL'
wsdl_bcb = 'https://www3.bcb.gov.br/sgspub/JSP/sgsgeral/FachadaWSSGS.wsdl'

# Codigos do sistema CVM
codigo_informes_diarios_fundos = '209'

# Codigos do sistema BCB (lemos a tabela de forma transposta)
proximidade_nome_indice = 0.95
df_tabela_codigos_bcb = None
