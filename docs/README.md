# Documentação Tecnica

Indice central da documentacao modular do projeto.

## Modulos de extracao

- [Câmara](./camara/README_CAMARA.md)
- [Senado](./senado/README_SENADO.md)
- [SIOP](./siop/README_SIOP.md)
- [Portal da Transparencia](./portal_transparencia/README_PORTAL_TRANSPARENCIA.md)
- [PNCP](./pncp/README_PNCP.md)
- [Transferegov](./transferegov/README_TRANSFEREGOV.md)
- [ObrasGov](./obrasgov/README_OBRASGOV.md)
- [Siconfi](./siconfi/README_SICONFI.md)
- [IBGE](./ibge/README_IBGE.md)
- [ANP](./anp/README_ANP.md)

## Infraestrutura compartilhada

- [Base de APIs Publicas](./publica/README_PUBLICA.md)
- [Arquitetura](./ARCHITECTURE.md)
- [Endpoints e Relevancia](./README_ENDPOINTS_RELEVANCIA.md)

## Camada de entrada

- `main.py` e apenas o ponto de entrada publico da CLI
- `cli/__init__.py` concentra parser, handlers e bootstrap da interface de linha de comando
- `utils/csv/__init__.py` concentra a orquestracao da camada analitica normalizada em CSV
- `utils/grafo/__init__.py` concentra a orquestracao da camada de grafos analiticos
- `etl-config.toml` e a fonte de verdade da configuracao operacional do ETL
- `rodar-pipeline-completo` resolve parametros com precedencia `CLI -> [pipelines.completo]` em [etl-config.toml](../etl-config.toml)
- `rodar-pipeline` e `rodar-paralelo` também delegam seus defaults operacionais ao `etl-config.toml`, em vez de embutirem anos, fontes ou janelas de datas no codigo
- o preflight desse comando apenas valida a configuracao final antes da execucao

## Camada analitica

- `gerar-csv` produz apenas a camada final de analise em `data/csv/`
- a orquestracao da geracao fica em `utils/csv/__init__.py`
- `gerar-grafo` deriva redes analiticas a partir de `data/csv/` e publica em `data/grafo/`
- a pipeline da Camara nao consolida CSV no meio da extracao; essa etapa ficou isolada no comando dedicado
- os arquivos finais ficam em uma pasta unica, sem subpastas artificiais por fonte
- a camada final prioriza 3FN minima: dimensoes pequenas, fatos sem colunas operacionais e separacao entre competencia e data do documento quando o dado oficial exige isso

## Convencoes gerais

- As extracoes novas persistem preferencialmente em JSON Lines.
- A estrategia de retomada do projeto e baseada em arquivos:
  `arquivo final + .tmp + .state.json + .empty`, conforme a natureza do endpoint.
- A persistencia de checkpoints usa apenas arquivos `.state.json`; nao ha camada paralela em SQLite.
- Nos conectores mais recentes, cada linha tende a seguir o envelope:

```json
{
  "_meta": {
    "orgao_origem": "origem_logica",
    "nome_endpoint": "dataset_logico",
    "endpoint": "/rota/oficial"
  },
  "payload": {}
}
```

- Os módulos antigos da Câmara, Senado e SIOP continuam salvando registros achatados, mas agora com mais chaves derivadas para facilitar carga futura em banco.
