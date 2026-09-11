# dbt Fundamentals — Jaffle Shop (DuckDB edition)

Projeto do curso dbt Fundamentals, originalmente rodado no dbt Cloud com
Snowflake. Este repositório foi adaptado para rodar **localmente com DuckDB**,
então o setup precisa de alguns passos manuais antes do primeiro `dbt run`.

## Por que migrei de Snowflake para DuckDB

O curso original usa dbt Cloud + Snowflake, que dependem de um data warehouse
gerenciado na nuvem — bom para o contexto do curso, mas overkill para rodar
o projeto localmente só para estudo. Troquei para DuckDB para poder:

- Rodar o pipeline inteiro (dbt-core + banco) na minha máquina, sem depender
  de credenciais de nuvem ou de um trial que expira.
- Entender melhor o que o dbt Cloud fazia "por trás" — profile, adapter,
  conexão — configurando tudo isso manualmente.
- Ter um projeto reprodutível por qualquer pessoa com Python instalado,
  sem precisar de conta em nenhum data warehouse.

A troca não é só de connection string: exigiu trocar o adapter
(`dbt-snowflake` → `dbt-duckdb`), reconstruir a camada de dados brutos
(`load_raw.py`, já que não há mais um schema `RAW` pré-populado no
warehouse) e ajustar um mismatch de nome de tabela/source que só apareceu
depois da migração (`stripe.payments` → `stripe.payment`).

## Arquitetura

- `jaffle_shop.duckdb` — banco "dev" onde o dbt materializa as models
  (staging, marts). Gerado pelo próprio `dbt run`, não é versionado.
- `raw.duckdb` — banco com os dados brutos (`jaffle_shop.customers`,
  `jaffle_shop.orders`, `stripe.payment`), anexado ao dbt como o database
  `raw` via `profiles.yml`. Também não é versionado — é recriado pelo
  `load_raw.py`.

## Setup

### 1. Instalar as dependências

```bash
uv sync
source .venv/bin/activate
```

### 2. Configurar o `profiles.yml`

O dbt lê o profile em `~/.dbt/profiles.yml` (fora do repositório). Crie/edite
esse arquivo com:

```yaml
default:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: jaffle_shop.duckdb
      threads: 4
      attach:
        - path: raw.duckdb
          alias: raw
```

> O `path` de `jaffle_shop.duckdb` e `raw.duckdb` é relativo ao diretório de
> onde você roda o dbt — rode os comandos sempre a partir da raiz do projeto.

### 3. Carregar os dados brutos

Os dados fonte (customers, orders, payments) não vêm com o repositório.
Rode o script abaixo para baixá-los e popular o `raw.duckdb`:

```bash
python load_raw.py
```

Isso cria `raw.duckdb` com os schemas `jaffle_shop` e `stripe` esperados
pelos sources em `models/staging/*/`.

### 4. Rodar o dbt

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
