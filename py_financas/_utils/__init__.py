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
"""Arquivo de inicializacao do pacote, exibindo e curando operacoes expostas"""


"""
# IMPORTS
"""

from py_financas._utils.unidades_brasileiras import ultimo_dia_util, e_dia_util
from .autenticacao import inicializa_cliente_wsdl_cvm
from .arquivos_zip import le_arquivo_zip_de_string
from py_financas._utils.autenticacao import LoggingWebServicePlugin
from .unidades_brasileiras import normaliza_cnpj, normaliza_numerico
