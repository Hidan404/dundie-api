"""Security utilities"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password) -> bool:
    """Verifies a hash against a password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password) -> str:
    """Generates a hash from plain text"""
    return pwd_context.hash(password)


class HashedPassword(str):
    """Takes a plain text password and hashes it.
    use this as a field in your SQLModel
    class User(SQLModel, table=True):
        username: str
        password: HashedPassword
    """

    @classmethod
    def __get_validators__(cls):
        # um ou mais validadores podem ser gerados, e serão chamados na
        # ordem para validar o input, cada validador receberá como entrada
        # o valor retornado pelo validador anterior
        yield cls.validate

    @classmethod
    def validate(cls, v):
        """Accepts a plain text password and returns a hashed password."""
        if not isinstance(v, str):
            raise TypeError("string required")

        hashed_password = get_password_hash(v)
        # você também poderia retornar uma string aqui, o que significaria que model.password
        # seria uma string, o pydantic não se importaria, mas você poderia acabar com alguma
        # confusão, já que o tipo do valor não corresponderia exatamente à anotação de tipo
        return cls(hashed_password)
