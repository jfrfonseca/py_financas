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
"""Operacoes de autenticacao utilizando sistemas WSDL com o pacote SUDS-JURKO"""


"""
# IMPORTS
"""


# Biblioteca padrão
import logging

# Dependencias PIP
from suds.client import Client
from suds.plugin import MessagePlugin

# Este pacote
from py_financas import constantes


"""
# UTIL
"""


class LoggingWebServicePlugin(MessagePlugin):
    """
    Classe de compatibilidade SUDS-JURKO
    Fonte: https://bitbucket.org/jurko/suds/issues/39/missing-last_sent-and-last_received
    """

    def __init__(self):
        self.last_sent_message = None
        self.last_received_reply = None

    def sending(self, context):
        if context.envelope:
            self.last_sent_message = context.envelope

    def parsed(self, context):
        if context.reply:
            self.last_received_reply = context.reply

    def last_sent(self):
        return self.last_sent_message

    def last_received(self):
        return self.last_received_reply


def inicializa_cliente_wsdl_cvm(usuario_cvm, senha_cvm):

    log = logging.getLogger('py_financas:cvm')

    try:

        # Inicializamos um objeto de compatibilidade SUDS
        logging_plugin = LoggingWebServicePlugin()

        # Iniciamos um objeto cliente SOAP SUDS-JURKO
        cliente = Client(constantes.wsdl_cvm, plugins=[logging_plugin])

        # Executamos o metodo de login da CVM
        cliente.service.Login(usuario_cvm, senha_cvm)

        # Setamos os headers de login na CVM
        cliente.set_options(soapheaders=logging_plugin.last_received().getChildren()[0][0][0])

        # Retornamos o cliente formado
        return cliente

    except Exception as exp:
        log.error("Excecao no login do sistema WSDL CVM! {}".format(exp))
        raise exp
