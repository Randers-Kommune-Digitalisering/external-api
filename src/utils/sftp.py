import base64
import io
import logging
import paramiko
import pysftp
import warnings


class SFTPClient:
    def __init__(self, host, username, password=None, key_base64=None, key_pass=None):
        self.host = host
        self.username = username
        self.password = password

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None

        self.cnopts = cnopts

        if key_base64:
            self.key = self._make_key(key_base64, key_pass)
        else:
            self.key = None

        self.logger = logging.getLogger(__name__)

    def _make_key(self, key_base64, key_pass=None):
        decoded_key = base64.b64decode(key_base64).decode("utf-8")
        private_key_file = io.StringIO()
        private_key_file.write(decoded_key)
        private_key_file.seek(0)
        return paramiko.RSAKey.from_private_key(private_key_file, password=key_pass)

    def get_connection(self):
        try:
            # Supress warning about trusting all host keys - bad practice!
            warnings.filterwarnings('ignore', '.*Failed to load HostKeys.*')
            return pysftp.Connection(host=self.host, username=self.username, password=self.password, private_key=self.key, cnopts=self.cnopts)
        except Exception as e:
            self.logger.error(e)
            return None
