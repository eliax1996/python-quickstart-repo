from pydantic import BaseSettings


class SslSecurityProtocol(BaseSettings):
    security_protocol: str
    ssl_cafile: str
    ssl_certfile: str
    ssl_keyfile: str

    class Config:
        extra = "ignore"
