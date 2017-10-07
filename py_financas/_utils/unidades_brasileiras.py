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
"""Operacoes de conversao de unidades e notacoes brasileiras em notacao cientifica/estado-unidense"""


"""
# IMPORT
"""


import datetime


"""
# UTIL
"""


# FORMATACAO DE DADOS ==================================================================================================


def normaliza_cnpj(string_nao_normalizada):
    return string_nao_normalizada.replace(".", "").replace("-", "").replace("/", "").zfill(14)


def normaliza_numerico(string_nao_normalizada):
    return string_nao_normalizada.replace(",", ".")


# DATAS ================================================================================================================


def ultimo_dia_util(data_inicial=datetime.datetime.today()):

    # Verificamos se a data passada e um dia util. Se nao, subtraimos um dia ate que seja
    while not e_dia_util(data_inicial):
        data_inicial -= datetime.timedelta(days=1)

    return data_inicial


def e_dia_util(data=datetime.datetime.today()):
    return data.weekday() < 5
