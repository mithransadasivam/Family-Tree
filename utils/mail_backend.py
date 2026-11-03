"""SMTP backend that connects over IPv4 only (Railway has no outbound IPv6, so Gmail's IPv6 address is unreachable)."""
import smtplib
import socket

from django.core.mail.backends.smtp import EmailBackend


class IPv4SMTP(smtplib.SMTP):
    def _get_socket(self, host, port, timeout):
        ip = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)[0][4][0]
        return socket.create_connection((ip, port), timeout, self.source_address)


class IPv4EmailBackend(EmailBackend):
    @property
    def connection_class(self):
        return IPv4SMTP

    @connection_class.setter
    def connection_class(self, value):
        pass
