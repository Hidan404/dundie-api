import typer
from rich.console import Console
from rich.table import Table
from sqlmodel import Session, select
from typing import Optional

from .config import settings
from .db import engine
from .models import User
from .models.user import generate_username
main = typer.Typer(name="dundie CLI", add_completion=False)


@main.command()
def shell():
    """Opens interactive shell"""
    _vars = {
        "settings": settings,
        "engine": engine,
        "select": select,
        "session": Session(engine),
        "User": User,
    }
    typer.echo(f"Auto imports: {list(_vars.keys())}")
    try:
        from IPython import start_ipython

        start_ipython(
            argv=["--ipython-dir=/tmp", "--no-banner"], user_ns=_vars
        )
    except ImportError:
        import code

        code.InteractiveConsole(_vars).interact()


@main.command()
def user_list():
    """Lists all users"""
    table = Table(title="dundie users")
    fields = ["name", "username", "dept", "email", "currency"]
    for header in fields:
        table.add_column(header, style="magenta")

    with Session(engine) as session:
        users = session.exec(select(User))
        for user in users:
            table.add_row(*[getattr(user, field) for field in fields])

    Console().print(table)

@main.command()
def user_create(name: str, email: str,password: str , dept: str, username: str, currency: str):
    """Creates a new user"""
    
    user = User(
        name=name,
        username=username or generate_username(name),
        email=email,
        password=password,
        dept=dept,
        currency=currency
    )
    username = user.username
    with Session(engine) as session:
        session.add(user)
        session.commit()
    typer.echo(f"User created: {username}")