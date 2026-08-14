from typing import Optional, List
from sqlmodel import Field, SQLModel
from pydantic import validator, EmailStr, HttpUrl
from dundie.security import HashedPassword
from pydantic import BaseModel, root_validator, ConfigDict


# Modelo de dados User usando SQLModel
# SQLModel combina SQLAlchemy (modelos de banco) com Pydantic (validação)
class User(SQLModel, table=True):
    # id é opcional ao criar (será gerado pelo banco). Não use min_length em int.
    id: Optional[int] = Field(default=None, primary_key=True, index=True)

    # Email usa validação de formato via EmailStr do Pydantic
    email: EmailStr = Field(unique=True, nullable=False)

    # username único, com tamanho mínimo/maximom tratados por validadores abaixo
    username: str = Field(unique=True, nullable=False)

    # avatar é opcional e, se fornecido, deve ser uma URL válida
    avatar: Optional[HttpUrl] = None

    # bio opcional, limitamos o tamanho via validador
    bio: Optional[str] = None

    # password e name obrigatórios
    password:  HashedPassword = Field(nullable=False)
    name: str = Field(nullable=False)

    # departemento/role do usuário. Podemos restringir a um conjunto conhecido
    dept: str = Field(nullable=False)

    # moeda preferida, por exemplo 'USD', 'EUR'... validação abaixo
    currency: str = Field(nullable=False)

    @property
    def superuser(self) -> bool:
        """Propriedade auxiliar: usuário é superuser se dept for 'manager'."""
        return self.dept.lower() == "manager"

    # ---------------------- Validadores (Pydantic) ----------------------
    # Os validators são executados antes de instanciar o modelo e garantem
    # regras de negócio (tamanhos, formatos, valores permitidos etc.).

    @validator("username")
    def username_length(cls, v: str) -> str:
        # garante tamanho entre 3 e 30 caracteres
        if not (3 <= len(v) <= 30):
            raise ValueError("username deve ter entre 3 e 30 caracteres")
        return v

    @validator("password")
    def password_strength(cls, v: str) -> str:
        # exemplo simples: mínimo 8 caracteres
        if len(v) < 8:
            raise ValueError("password deve ter pelo menos 8 caracteres")
        return v

    @validator("bio")
    def bio_max_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 512:
            raise ValueError("bio deve ter no máximo 512 caracteres")
        return v

    @validator("dept")
    def dept_allowed(cls, v: str) -> str:
        allowed: List[str] = ["engineering", "sales", "hr", "marketing", "manager"]
        if v.lower() not in allowed:
            raise ValueError(f"dept deve ser uma das seguintes: {allowed}")
        return v

    @validator("currency")
    def currency_format(cls, v: str) -> str:
        # espera código ISO de 3 letras
        if not (isinstance(v, str) and len(v) == 3 and v.isalpha()):
            raise ValueError("currency deve ser um código ISO de 3 letras, ex: 'USD'")
        return v.upper()

def generate_username(nome: str) -> str:
    #TODO: implementar lógica de geração de username a partir do nome
    #testar slugify depois, mas por enquanto vamos apenas normalizar o nome
    try:
        nome_normalizado = nome.lower().replace(" ", "-")
        return nome_normalizado  
    except Exception as e:
        raise ValueError(f"Erro ao gerar username {nome} : {e}")

class UserResponse(BaseModel):
    '''Searializar dadso de resposta'''
    
    name: str
    username: str
    dept: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    currency: str

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    ''''''    
    # Atributos na mesma ordem que a classe User
    email: str
    username: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    password: str
    name: str
    dept: str
    currency: str

    @root_validator(pre=True)
    def generate_username_if_not_set(cls, value):
        # Validador de raiz (root_validator) que processa todos os dados do modelo antes da validação individual
        # pre=True significa que este validador é executado ANTES dos validadores de campo específicos
        
        # Verifica se o campo 'username' não foi fornecido (é None ou não existe no dicionário)
        if value.get("username") is None:
            # Se username não foi fornecido, gera automaticamente um username a partir do campo 'name'
            # Chama a função generate_username que normaliza o nome (converte para minúsculas e substitui espaços por hífen)
            value["username"] = generate_username(value["name"])
        
        # Retorna o dicionário de valores atualizado (com username gerado, se necessário)
        # Este dicionário será usado para instanciar o objeto UserCreate
        return value