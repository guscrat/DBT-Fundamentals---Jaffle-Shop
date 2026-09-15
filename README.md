# dbt Fundamentals — Jaffle Shop (BigQuery edition)

Projeto do curso dbt Fundamentals, originalmente rodado no dbt Cloud com
Snowflake. Passou por duas migrações desde então: primeiro para **DuckDB
local** (só para estudo, sem depender de warehouse na nuvem) e agora para o
**sandbox do BigQuery**, então o setup precisa de alguns passos manuais antes
do primeiro `dbt run`.

## Histórico de migrações

### Snowflake → DuckDB

O curso original usa dbt Cloud + Snowflake, que dependem de um data warehouse
gerenciado na nuvem — bom para o contexto do curso, mas overkill para rodar
o projeto localmente só para estudo. Troquei para DuckDB para poder:

- Rodar o pipeline inteiro (dbt-core + banco) na minha máquina, sem depender
  de credenciais de nuvem ou de um trial que expira.
- Entender melhor o que o dbt Cloud fazia "por trás" — profile, adapter,
  conexão — configurando tudo isso manualmente.
- Ter um projeto reprodutível por qualquer pessoa com Python instalado,
  sem precisar de conta em nenhum data warehouse.

A troca não foi só de connection string: exigiu trocar o adapter
(`dbt-snowflake` → `dbt-duckdb`), reconstruir a camada de dados brutos
(`load_raw.py`, já que não há mais um schema `RAW` pré-populado no
warehouse) e ajustar um mismatch de nome de tabela/source que só apareceu
depois da migração (`stripe.payments` → `stripe.payment`).

### DuckDB → BigQuery

O DuckDB é ótimo pra estudar dbt sem fricção, mas roda tudo num arquivo
local — nenhuma das partes "de nuvem" de um projeto de dados real (auth,
projeto/dataset, load jobs, etc.) aparece na prática. Migrei para o
**sandbox do BigQuery** pra treinar com um warehouse de nuvem de verdade:

- Autenticação via `gcloud auth application-default login` em vez de um
  arquivo de banco local.
- Dados brutos carregados via *load jobs* do BigQuery (`load_raw.py` agora
  baixa os CSVs, monta DataFrames com pandas e sobe com
  `google-cloud-bigquery`), em vez de `read_csv_auto` direto no DuckDB.
- Datasets do BigQuery (`jaffle_shop`, `stripe`) no lugar dos schemas
  attachados por arquivo do DuckDB — não existe mais um database `raw`
  separado, então os `sources.yml` perderam o campo `database: raw`.
- Um ajuste de tipo que o BigQuery exige e o DuckDB deixava passar:
  `order_date` precisou de `cast(... as date)` explícito em
  `stg_jaffle_shop__orders.sql`.

O adapter trocou de `dbt-duckdb` para `dbt-bigquery`, e o profile passou a
se chamar `jaffle_shop` (antes `default`).

## Arquitetura

- **BigQuery (projeto sandbox)** — os dados brutos e as models materializadas
  vivem em um projeto do GCP (ex.: `jaffle-shop-bq`, região `US`), não mais
  em arquivos locais.
- Datasets `jaffle_shop` e `stripe` — contêm as tabelas brutas
  (`jaffle_shop.customers`, `jaffle_shop.orders`, `stripe.payment`),
  recriadas pelo `load_raw.py` via load job (`WRITE_TRUNCATE`).
- As models de staging/marts do dbt são materializadas no mesmo projeto,
  conforme o `dataset`/`schema` configurado no `profiles.yml`.

## Setup

### 1. Instalar as dependências

```bash
uv sync
source .venv/bin/activate
```

### 2. Autenticar no GCP

```bash
gcloud auth application-default login
```

Isso gera as credenciais OAuth que tanto o `load_raw.py` quanto o dbt
(via `profiles.yml`) usam para falar com o BigQuery — nenhuma chave de
service account é versionada no repositório.

### 3. Configurar o `profiles.yml`

O dbt lê o profile em `~/.dbt/profiles.yml` (fora do repositório). Crie/edite
esse arquivo com:

```yaml
jaffle_shop:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: oauth
      project: jaffle-shop-bq   # id do teu projeto sandbox no GCP
      dataset: jaffle_shop
      location: US
      threads: 4
```

> Ajuste `project` para o id do teu projeto sandbox — o mesmo valor usado na
> constante `PROJECT` de `load_raw.py`.

### 4. Carregar os dados brutos

Os dados fonte (customers, orders, payments) não vêm com o repositório.
Rode o script abaixo para baixá-los e populá-los no BigQuery:

```bash
python load_raw.py
```

Isso cria os datasets `jaffle_shop` e `stripe` no projeto configurado, com
as tabelas esperadas pelos sources em `models/staging/*/`.

### 5. Rodar o dbt

```bash
dbt debug   # confere se o adapter/profile foram encontrados
dbt run
dbt test
```

## Orquestração

Este projeto também é orquestrado via Airflow no repositório
[`airflow-lab`](https://github.com/guscrat/airflow-lab), que encadeia
`load_raw.py -> dbt run -> dbt test` como um DAG.

## Resources

- Learn more about dbt [in the docs](https://docs.getdbt.com/docs/introduction)
- Check out [Discourse](https://discourse.getdbt.com/) for commonly asked questions and answers
- Join the [dbt community](https://getdbt.com/community) to learn from other analytics engineers
- Find [dbt events](https://events.getdbt.com) near you
- Check out [the blog](https://blog.getdbt.com/) for the latest news on dbt's development and best practices
