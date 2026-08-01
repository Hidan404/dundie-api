'''Database connetion'''

#create_engine  cria um factory de conexao para gerar conexao com o bd para gerar executar no bs
from sqlmodel import create_engine
from .config import settings

engine = create_engine(
    settings.db.uri,
    echo=settings.db.echo,
    connect_args=settings.db.connect_args
)