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
"""Inicializacao do pacote, oferecendo multiplos alias para os sub-pacotes"""


"""
# IMPORTS
"""


__version__ = '1.0.2'
version = __version__
VERSION = __version__


# O sistema da Comissao de Valores Mobiliarios e tambem a unica fonte de informacoes sobre fundos
from py_financas import cvm
from py_financas import cvm as fundos
from py_financas import cvm as fundos_mutuos

# O sistema do Banco Central do Brasil - Sistema de Gestao de Series Temporais e tambem a unica fonte de indices
from py_financas import bcb_sgs
from py_financas import bcb_sgs as indices
from py_financas import bcb_sgs as indexadores  # Indices tambem sao chamados "indexadores"

# O SINACOR contém os modelos de dados utilizados em negociacoes
from py_financas import sinacor
from py_financas.sinacor.types import NotaCorretagem, Posicao, \
    MomentoPosicao, Operacao, Corretora, Totais, Impostos, Custos
