# Câmara dos Deputados

Documentação técnica do pacote de extração da Câmara.

Arquitetura:

- `extracao/camara/deputados_federais/__init__.py`: orquestração pública de `Legislatura`, `DeputadosLegislatura` e `Despesas`.
- `extracao/camara/deputados_federais/config.py`: configuração operacional e contratos mínimos de saída.
- `extracao/camara/deputados_federais/artefatos.py`: convenções de caminhos para `final/tmp/empty/state`.
- `extracao/camara/deputados_federais/dados.py`: leitura de JSONL, recorte temporal e enriquecimento de despesas.
- `extracao/camara/deputados_federais/paginado.py`: loop paginado com retomada e persistência incremental.
- `pipeline/__init__.py`: pipeline sequencial da Câmara e demais orquestrações públicas.

## Objetivo

Extrair a cadeia base da Câmara:

1. legislaturas
2. deputados por legislatura
3. despesas por deputado e por ano
4. consolidacao analitica em CSV

## Invariantes de manutenção

- toda a orquestração pública do pacote fica em `extracao/camara/deputados_federais/__init__.py`;
- `config.py`, `artefatos.py`, `dados.py` e `paginado.py` devem permanecer módulos auxiliares sem orquestração;
- os três fluxos usam o mesmo protocolo de retomada: arquivo final, `.tmp`, `.empty` e `.state.json`;
- o fluxo de despesas continua deduplicando por `(deputado, ano)` e priorizando legislaturas mais recentes;
- não há compatibilidade com os módulos antigos removidos do pacote.

## Fluxo

### 1. Legislaturas

Comando:

```bash
uv run python main.py baixar-legislaturas
```

Saída:

- `data/legislaturas.json`

### 2. Deputados por legislatura

Comando:

```bash
uv run python main.py extrair-legislaturas
```

Saída:

- `data/deputados_por_legislaturas/deputados_legislaturas_<id>.json`

### 3. Despesas por deputado

Comando:

```bash
uv run python main.py extrair-dependentes --endpoint deputados_despesas --ano-inicio 2023 --ano-fim 2026
```

Observacao:

- `ano-fim` e exclusivo

Saída:

- `data/despesas_deputados_federais/<ano>/despesas_<id>.json`

### 4. Consolidacao

Comando:

```bash
uv run python main.py gerar-csv
```

Saída:

- o comando agora só executa após as extrações base existirem
- no fluxo da Câmara, os arquivos analíticos finais ficam em `data/csv/`
- os principais artefatos da fonte são `data/csv/dim_legislaturas_dep_federais.csv`, `data/csv/dim_dep_federal.csv`, `data/csv/dim_deputados_federais_referencia.csv`, `data/csv/tb_documentos_despesas_deputados.csv` e `data/csv/tb_despesas_deputados.csv`

## Estratégia do crawler

- leitura progressiva de arquivos de deputados
- filtragem por janela temporal da legislatura
- priorizacao de anos mais recentes
- checkpoint por `(endpoint, deputado, ano)` em arquivos `.state.json`
- escrita incremental em JSON Lines com arquivo temporário `.tmp`
- marcador `.empty` para tarefas confirmadas como vazias
- reprocessamento automático quando o arquivo antigo não contém o esquema novo

## Campos importantes no staging JSONL

Nos arquivos de despesas:

- `id_deputado`
- `id_legislatura`
- `nome_deputado`
- `uri_deputado`
- `sigla_uf_deputado`
- `sigla_partido_deputado`
- `cnpjCpfFornecedor`
- `documento_fornecedor_normalizado`
- `tipo_documento_fornecedor`
- `cnpj_base_fornecedor`
- `codDocumento`
- `codLote`
- `numDocumento`
- `dataDocumento`
- `valorDocumento`
- `valorLiquido`
- `orgao_origem`
- `endpoint_origem`

## Contrato analítico final

Na camada `data/csv/`, a granularidade foi separada entre documento e despesa:

- `tb_documentos_despesas_deputados.csv` concentra o documento fiscal;
- `tb_despesas_deputados.csv` concentra o evento de despesa e reembolso;
- `dim_tempo.csv` representa a data do documento;
- `dim_competencia_mensal.csv` representa o mês de competência financeira informado pela Câmara.

Essa separação evita repetir `ano`, `mes` e `dataDocumento` no mesmo fato e remove
metadados operacionais como `uri_deputado` e `endpoint_origem` dos CSVs analíticos.

## Join sugerido

- fornecedor: `documento_fornecedor_normalizado` ou `cnpj_base_fornecedor`
- parlamentar: `id_deputado`
- recorte institucional: `id_legislatura`
- recorte temporal: `id_competencia` e `id_tempo_documento`

## Pipeline

```bash
uv run python main.py rodar-pipeline
```

Se `--ano-inicio` e `--ano-fim` forem omitidos, o comando usa
`[config.pipelines.camara]` em
[etl-config.toml](../../etl-config.toml).
