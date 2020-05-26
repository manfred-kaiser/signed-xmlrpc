# -*- coding: utf-8 -*-

import base64
from xml.dom.minidom import parseString, Document
from xmlrpc.client import Transport
from ecdsa import SigningKey, VerifyingKey
from signed_xmlrpc.exceptions import MissingPublicKey


class SigningTransport(Transport):

    def __init__(self, private_key, public_key=None, src_ip=None, use_datetime=False, use_builtin_types=False):
        super().__init__(use_datetime, use_builtin_types)
        self.private_key = private_key
        self.public_key = public_key
        self.src_ip = src_ip

    def sign(self, data):
        """
        signiert die übergebenen Daten und gibt diese zurück.
        Sollte kein private Key angegeben worden sein, wird ein Fehler geworfen.
        """
        signature = self.private_key.sign(data)
        return base64.b64encode(signature)

    def verify(self, data, signature):
        """
        verifiziert die Daten mithilfe der übergebenen Signatur
        """
        if not self.public_key:
            raise MissingPublicKey()
        verifykey = VerifyingKey.from_string(self.public_key)
        return verifykey.verify(base64.b64decode(signature), data)

    # hilfsmethode nicht aktiv verwendet
    @classmethod
    def create_keys(cls):
        """
        Erstellt Keys für die signierte Übertragung.
        Diese Werden in dem Format (private,public ) zurückgegeben
        """
        private_key = SigningKey.generate()
        public_key = private_key.get_verifying_key()
        return private_key, public_key

    def request(self, host, handler, request_body, verbose=False):
        """
        ist für den Aufruf der Methoden auf dem Server zuständig.
        Die XML-Nachrichten werden manuell zusammengebaut und dann zu dem Host gesendet.
        """
        doc = parseString(request_body)

        connectionelement = doc.createElement("connection")
        if self.src_ip:
            connectionelement.setAttribute("srcip", self.src_ip)
        connectionelement.setAttribute("dstip", host)

        ps = doc.getElementsByTagName('methodCall')[0]
        ps.insertBefore(connectionelement, ps.firstChild)

        xmldata = base64.b64encode(bytes(doc.toxml(), 'UTF-8'))

        message = Document()
        msgnode = message.createElement('message')
        message.appendChild(msgnode)
        xmlnode = message.createElement('xmldata')
        xmlnode.appendChild(message.createTextNode(xmldata.decode("utf-8")))
        msgnode.appendChild(xmlnode)

        signaturenode = message.createElement('signature')
        signaturenode.appendChild(message.createTextNode(self.sign(xmldata).decode("utf-8")))
        msgnode.appendChild(signaturenode)

        return super().request(host, handler, bytes(message.toxml(), 'UTF-8'), verbose)
