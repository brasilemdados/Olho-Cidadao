# Grafo Analítico

Este diretório publica uma representação de rede derivada da camada
analítica em `data/csv/`.

## Formato escolhido

- framework-alvo: `cytoscape.js`
- wrapper React recomendado: `react-cytoscapejs`
- licença: open source (`MIT`)
- integração com Rust: o backend pode servir o JSON pronto via arquivo estático
  ou endpoint HTTP sem adaptação obrigatória de schema

O arquivo principal usa o formato `elements` do Cytoscape:

- `elements.nodes`
- `elements.edges`

Isso permite consumo direto no frontend React + Vite e também leitura simples
no backend Rust com `serde_json`.

## Arquivos

- `rede_despesas_publicas.cytoscape.json`: grafo agregado completo
- `resumo_rede_despesas_publicas.json`: resumo para inspeção rápida

## Modelo da rede

Nós:

- `parlamentar`: deputado ou senador
- `fornecedor`: CPF/CNPJ normalizado presente nas despesas
- `tipo_despesa`: categoria analítica da despesa

Arestas:

- `gasto_com_fornecedor`: parlamentar -> fornecedor
- `gastou_em_tipo_despesa`: parlamentar -> tipo_despesa

## Métricas nas arestas

- `quantidade_despesas`
- `valor_total`
- `primeira_competencia`
- `ultima_competencia`

## Como verificar os valores

Relação `gasto_com_fornecedor`:

- Câmara: `tb_despesas_deputados.csv` JOIN `tb_documentos_despesas_deputados.csv`
  por `id_documento_despesa`, agregando por `id_deputado + id_fornecedor`
- Senado: `tb_despesas_senadores.csv` JOIN `tb_documentos_despesas_senadores.csv`
  por `id_documento_despesa`, agregando por `id_senador + id_fornecedor`

Relação `gastou_em_tipo_despesa`:

- agregação direta de `tb_despesas_deputados.csv` e `tb_despesas_senadores.csv`
  por `parlamentar + id_tipo_despesa`

## Observação operacional

O grafo completo é válido para consumo pelo Cytoscape.js, mas para uso em
produção o ideal é o backend em Rust servir subgrafos filtrados por:

- parlamentar
- fornecedor
- tipo de despesa
- casa legislativa
- intervalo de competência

Assim o frontend React + Vite trabalha com ego networks ou comunidades
menores, sem tentar renderizar toda a rede de uma vez.
