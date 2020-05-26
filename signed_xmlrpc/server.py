import base64
import logging
from xmlrpc.server import SimpleXMLRPCRequestHandler

from ecdsa import SigningKey, BadSignatureError

from xml.etree import ElementTree as ET
import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer

from signed_xmlrpc.exceptions import MissingPrivateKey


class SignedRequestHandler(SimpleXMLRPCRequestHandler):

    REQUIRE_SIGNATURE = True

    def verify(self, data, signature):
        """
        verifiziert die Daten mithilfe der übergebenen Signatur
        """
        return self.server.public_key.verify(base64.b64decode(signature), data)

    def sign(self, data):
        """
        signiert die gegebenen Daten und gibt diese zurück.
        Sollte keine private Key angegeben worden sein, wird ein Fehler geworfen.
        """
        if not self.server.private_key:
            raise MissingPrivateKey()
        signkey = SigningKey.from_string(self.server.private_key)
        signature = signkey.sign(data)
        return base64.b64encode(signature)

    def decode_request_content(self, data):
        dom = ET.fromstring(data)
        xmldata_element = dom.find('./xmldata')
        signature_element = dom.find('./signature')

        if xmldata_element is None or signature_element is None:
            if self.REQUIRE_SIGNATURE:
                return self.report_403()
            logging.warning("unsigned xml rpc allowed")
            return data

        xmldata = xmldata_element.text.encode('UTF-8')
        signature = signature_element.text.encode('UTF-8')

        try:
            self.verify(xmldata, signature)
        except BadSignatureError:
            return self.report_403()

        data = base64.b64decode(xmldata)

        conn_host = "{}:{}".format(self.connection.getsockname()[0], self.connection.getsockname()[1])
        xml_request = ET.fromstring(data)
        connection_tag = xml_request.find('./connection')

        if conn_host != connection_tag.attrib['dstip']:
            return self.report_403()

        if 'srcip' in connection_tag.attrib and self.client_address[0] != connection_tag.attrib['srcip']:
            return self.report_403()

        return super().decode_request_content(data)

    def report_403(self):
        # Report a 403 error
        self.send_response(403)
        response = b'Forbidden'
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)


class SignedXMLRPCServer(SimpleXMLRPCServer):
    """
    Der Server welche die Methoden zur Verfügung stellt.
    """
    allow_reuse_address = True
    """
    Erlaubt das Wiederverwenden von verherigen Adressen.
    """

    def __init__(self, public_key, *args, private_key=None, requesthandler=SignedRequestHandler, allow_none=True, **kw):

        SimpleXMLRPCServer.__init__(self, *args, requesthandler, allow_none, **kw)
        self.stopped = False
        self.public_key = public_key
        self.private_key = private_key
        self.register_function(lambda: 'pong', 'ping')

    def serve_forever(self, **kwargs):
        """
        lässt den Server weiterlaufen bis er manuell beendet wird.
        """
        while not self.stopped:
            try:
                self.handle_request()
            except ValueError:
                pass

    def force_stop(self):
        """
        Erzwingt den stop des servers.
        """
        self.server_close()
        self.stopped = True
        try:
            server = xmlrpc.client.ServerProxy('http://%s:%s' % self.server_address)
            server.ping()
        except ConnectionRefusedError:
            pass
