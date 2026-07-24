from typing import Optional, List
from sqlmodel import Field, SQLModel
from pydantic import validator, EmailStr, HttpUrl


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
    password: str = Field(nullable=False)
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
