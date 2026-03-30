# Arquitetura

## Visão geral

O projeto segue uma arquitetura em camadas:

1. CLI e orquestração
2. Extratores por domínio
3. Infraestrutura compartilhada
4. Utilitários de transformação e persistência
5. Documentação e testes

## Camadas

### CLI

Arquivos principais:

- `main.py`
- `cli/__init__.py`
- `cli/comun.py`
- `cli/menu.py`
- `pipeline/__init__.py`
- `pipeline/config.py`
- `pipeline/tarefas.py`

Responsabilidades:

- expor comandos ao usuario
- validar argumentos
- concentrar parser, wiring e handlers publicos em um unico ponto
- disparar pipelines ou extratores independentes

Observação:

- `main.py` e apenas um ponto de entrada enxuto
- `cli/__init__.py` e a fachada unica da CLI

Pipeline completo:

- o comando publico e `rodar-pipeline-completo`
- a CLI apenas coleta overrides explicitos, como `--ano-inicio`, `--ano-fim` e `--max-workers`
- a configuracao base vem da secao `[pipelines.completo]` em [etl-config.toml](../etl-config.toml)
- a precedencia e sempre `CLI -> etl-config.toml`
- o preflight do pipeline completo valida a configuracao resolvida; ele não cria defaults nem altera parametros

Pipelines locais:

- `rodar-pipeline` busca anos a partir de `[config.pipelines.camara]` quando a CLI não informa `--ano-inicio/--ano-fim`
- `rodar-paralelo` busca anos, janela do PNCP, `max_workers` e fontes a partir de `[config.pipelines.paralelo]`
- em `rodar-paralelo`, flags como `--siop/--sem-siop` e `--pncp/--sem-pncp` são tri-state: se omitidas, o valor continua vindo do arquivo; se informadas, sobrescrevem só a execucao atual

Exemplo de resolucao:

- `uv run python main.py rodar-pipeline-completo` usa os anos versionados em `[pipelines.completo]`
- `uv run python main.py rodar-pipeline-completo --ano-inicio 2020 --ano-fim 2024` usa os anos da CLI apenas nessa execucao

### Extratores

Cada fonte vive em `extracao/<fonte>/`.

Responsabilidades:

- modelar a unidade de trabalho
- respeitar limites da API
- persistir resultados e checkpoints
- enriquecer registros com chaves úteis para joins futuros

### Infraestrutura compartilhada

Local:

- `infra/http/`
- `infra/estado/`
- `infra/concorrencia.py`
- `configuracao/__init__.py`
- `configuracao/acesso.py`
- `configuracao/carregador.py`

Responsabilidades:

- sessão HTTP
- retry e rate limiting
- persistência uniforme de estado
- carregamento centralizado do `etl-config.toml`
- carregamento centralizado de endpoints
- concorrencia limitada com backpressure local
- contadores thread-safe de execucao

### Utilitários

Local:

- `utils/`

Responsabilidades:

- JSON Lines
- filtros e slugs
- normalização de documentos
- geração da camada analítica em CSV normalizado
- geração de grafos analíticos derivados da camada CSV
- paginação e parâmetros

## Estratégia de retomada

O padrão do projeto é:

- arquivo final reaproveitável
- `.tmp` durante a escrita
- `.state.json` para checkpoint
- `.empty` para sinalizar consulta vazia até a próxima revalidação automática, sendo removido depois dela

Isso permite:

- retomar sem recomeçar a execução inteira
- evitar duplicação de saída
- reaproveitar artefatos íntegros já produzidos na estrutura atual

## Estratégia de crawler

Padrões usados ao longo do projeto:

- unidades pequenas de trabalho
- baixo uso de RAM
- paginação determinística sempre que possível
- sessões HTTP reutilizáveis
- sessão por thread nas bases concorrentes mais novas
- limites explícitos por fonte ou endpoint
- preferência por persistência incremental
- reuso de infraestrutura compartilhada antes de criar lógica nova por crawler

## Orquestracao do pipeline completo

O `rodar-pipeline-completo` segue uma ordem fixa em duas fases:

1. preflight
2. fontes independentes ou com orquestracao própria
3. enriquecimentos dependentes

Detalhe:

- o preflight valida `ano_inicio`, `ano_fim`, `max_workers` e dependencias externas obrigatorias, como a chave do Portal
- a fase paralela executa a espinha dorsal do projeto
- a fase dependente roda depois, porque consome artefatos gerados anteriormente, como fornecedores derivados e identificadores do ObrasGov

## Modelo de dados

O projeto ainda persiste majoritariamente em staging JSONL, mas a camada final em CSV já segue separação analítica explícita:

- dimensões: tempo, competência, tipos de despesa, tipos de documento, legislaturas, localidades, entes e fornecedores
- fatos: despesas, documentos de despesa, execuções, transferências e demais eventos numéricos
- híbridos: contratos, atas, PCA, alguns cadastros mestres

Na camada final em CSV:

- `utils/csv/__init__.py` coordena toda a geração
- a saída pública fica concentrada em `data/csv/`
- a consolidação não acontece dentro das pipelines de extração
- campos operacionais como `uri`, `endpoint` e metadados internos ficam no staging e não sobem para os arquivos analíticos
- competência mensal e data do documento permanecem separadas quando a fonte oficial trata esses conceitos como eventos distintos

Na camada de grafos:

- `utils/grafo/__init__.py` coordena toda a geração
- a saída pública fica concentrada em `data/grafo/`
- o formato alvo atual é compatível com `cytoscape.js`

## Evolução recomendada

Para novas contribuições:

- mantenha contratos estáveis de arquivo
- não introduza bancos ou serviços externos sem necessidade clara
- preserve compatibilidade com reruns
- priorize chaves de join e rastreabilidade
