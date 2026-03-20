# Senado Federal

Documentação técnica do módulo de extracao do Senado.

Arquivos principais:

- `extracao/senado/__init__.py`
- `extracao/senado/config.py`
- `extracao/senado/arquivos.py`
- `extracao/senado/dados.py`
- `extracao/senado/persistencia.py`
- `extracao/senado/tarefas.py`

## Objetivo

Extrair o CEAPS do Senado por exercício, com persistência em JSON Lines e escrita atomica.

## Comando

```bash
uv run python main.py extrair-senado --endpoint ceaps
```

## Saída

- `data/senadores/ceaps_<ano>.json`

## Saída analítica via `gerar-csv`

- `data/csv/dim_tempo.csv`
- `data/csv/dim_competencia_mensal.csv`
- `data/csv/dim_tipos_documento_fiscal.csv`
- `data/csv/dim_tipos_despesa.csv`
- `data/csv/dim_senadores.csv`
- `data/csv/tb_documentos_despesas_senadores.csv`
- `data/csv/tb_despesas_senadores.csv`

## Estratégia do crawler

- processamento do ano mais recente para o mais antigo
- pulos automáticos quando o arquivo final já existe no esquema novo
- escrita em arquivo temporário `.tmp`
- arquivo de estado `.state.json` por ano
- marcador `.empty` para anos sem dados
- promocao atomica para o arquivo final

## Organização

- `extracao.senado` expõe a orquestração pública `DadosSenado`
- `config.py` resolve endpoint e intervalo anual
- `arquivos.py` deriva artefatos anuais e valida saída reaproveitável
- `dados.py` normaliza o payload e enriquece registros
- `persistencia.py` isola a serialização anual
- `tarefas.py` concentra helpers puros de ordem e contagem

## Campos importantes no staging JSONL

- `id`
- `codSenador`
- `nomeSenador`
- `fornecedor`
- `cpfCnpj`
- `documento_fornecedor_normalizado`
- `tipo_documento_fornecedor`
- `cnpj_base_fornecedor`
- `documento`
- `data`
- `tipoDespesa`
- `valorReembolsado`
- `ano`
- `ano_arquivo`
- `orgao_origem`
- `endpoint_origem`

## Contrato analítico final

Em `tb_despesas_senadores.csv`, a granularidade passou a ser uma despesa reembolsada.
Por isso:

- `tb_documentos_despesas_senadores.csv` concentra fornecedor, tipo, data, número e detalhamento do documento;
- `ano`, `mes` e `data` não ficam duplicados no fato; o join temporal é feito por `id_competencia` e `id_documento_despesa`;
- metadados operacionais como `orgao_origem` e `endpoint_origem` permanecem só no staging;
- fornecedor entra por `id_fornecedor`, reaproveitando a dimensão consolidada local.

## Join sugerido

- fornecedor: `documento_fornecedor_normalizado`
- comparacao temporal: `id_competencia` e `id_documento_despesa`
- ator politico: `codSenador`
