# Plano de Correção — Erro de conexão com o banco (`could not translate host name "db"`)

## 1. Sintoma

Ao executar o CLI dentro do container (`docker compose exec api dundie user-create ...`), o
comando falhava com:

```
OperationalError: (psycopg2.OperationalError) could not translate host name "db" to address:
Temporary failure in name resolution
```

O traceback apontava para `/home/app/api/dundie/cli.py:66` (dentro do container, onde o
repositório é montado em `.:/home/app/api`).

## 2. Diagnóstico

O erro **não era um bug de código** e sim um problema de infraestrutura Docker:

- A URI do banco usada é `postgresql://postgres:postgres@db:5432/dundie` (definida no
  `docker-compose.yaml` via variável `DUNDIE_DB__uri`). O hostname `db` só é resolvível pelo
  DNS embutido do Docker na rede compartilhada do compose.
- Verificação com `docker inspect` mostrou que o container `dundie-api-api-1` **não estava
  conectado a nenhuma rede Docker** (`NetworkSettings.Networks = {}`), enquanto o container
  `dundie-api-db-1` estava na rede `dundie-api_default` (IP `172.19.0.2`).
- Confirmação: `docker exec dundie-api-api-1 python -c "import socket; print(socket.gethostbyname('db'))"`
  falhava com `socket.gaierror`. O `/etc/resolv.conf` do container usava o resolver do host
  (`127.0.0.53`) em vez do DNS do Docker (`127.0.0.11`), indicando ausência de rede.

### Problemas adicionais encontrados no caminho

1. **Conflito de porta 8000**: o serviço `api` não conseguia iniciar pois a porta `8000` do
   host já estava alocada por outro projeto (`ygo_api` / `backend-api`).
2. **`DetachedInstanceError` no `cli.py`**: após corrigir a conexão, o comando falhava ao
   imprimir `user.username` **depois** de fechar a sessão (`with Session(...)`). Por padrão o
   SQLAlchemy expira os atributos após o `commit`, e o acesso fora da sessão dispara um
   refresh em uma instância destacada.

## 3. Correção aplicada

### 3.1 Rede Docker (causa raiz do erro reportado)

Recriar os containers e a rede de forma limpa (os dados no volume nomeado `dundie_pg_data`
foram preservados):

```bash
docker compose down
docker compose up -d --build
```

Resultado: `db` voltou a resolver de dentro do container `api`:

```
$ docker exec dundie-api-api-1 python -c "import socket; print(socket.gethostbyname('db'))"
db -> 172.19.0.2
```

### 3.2 `docker-compose.yaml` — porta do serviço `api`

A porta do host foi alterada de `8000` para `8001` porque `8000` estava permanentemente em
uso por outro projeto:

```yaml
ports:
  # Porta do host alterada de 8000 para 8001 (8000 estava em uso por outro projeto)
  - "8001:8000"
```

### 3.3 `dundie/cli.py` — erro secundário `DetachedInstanceError`

Capturar o `username` **antes** de fechar a sessão, para não acessar um atributo expirado
fora dela:

```diff
-    with Session(engine) as session:
-        session.add(user)
-        session.commit()
-    typer.echo(f"User created: {user.username}")
+    username = user.username
+    with Session(engine) as session:
+        session.add(user)
+        session.commit()
+    typer.echo(f"User created: {username}")
```

## 4. Verificação

```bash
# 1) Hostname db resolve dentro do container
docker exec dundie-api-api-1 python -c "import socket; print(socket.gethostbyname('db'))"

# 2) CLI de criação funciona de ponta a ponta (mesmo fluxo que falhava)
docker compose exec api dundie user-create "Michael Scott" michael@dundermifflin.com secret123 sales "Michael Scott" USD
# Saída: User created: Michael Scott

# 3) Registros persistidos no banco
docker compose exec db psql -U postgres -d dundie -c "SELECT username, email, dept FROM \"user\";"
```

Resultado da verificação (usuários criados durante o teste):

| username    | email                     | dept   |
|-------------|---------------------------|--------|
| Ronald sousa  | ronald@gmail.com        | manager |
| Michael Scott | michael@dundermifflin.com | sales  |

## 5. Como evitar recorrência

- Sempre subir o ambiente com `docker compose up -d` para garantir que `api` e `db` estejam
  na mesma rede (`dundie-api_default`). Se o container `api` ficar sem rede (ex.: reinício
  parcial), reconectar:
  ```bash
  docker network connect dundie-api_default dundie-api-api-1
  docker compose restart api
  ```
- **CLI no host** (fora do Docker): o hostname `db` nunca resolverá fora da rede. Nesse caso,
  usar a porta publicada:
  ```bash
  export DUNDIE_DB__uri="postgresql://postgres:postgres@localhost:5434/dundie"
  ```
- Não acessar atributos de um objeto ORM após o fechamento da sessão sem capturá-los antes ou
  usar `expire_on_commit=False`.

## 6. Fora de escopo (não alterado)

- Aviso `the attribute 'version' is obsolete` no `docker-compose.yaml` (remover `version: '3.9'`
  é uma melhoria, sem relação com o erro).
- Arquivos não commitados: `dundie/config.py`, `dundie/models/user.py`, `dundie/security.py`.
