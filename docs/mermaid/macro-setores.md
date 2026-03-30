# Macro Setores da Rede de Transparencia

Visão agregada da taxonomia principal da rede. Use este arquivo para
entender a organização geral e os arquivos temáticos para manutenção local.

## Arquivos relacionados

- [03-politicas-sociais-e-direitos.md](./03-politicas-sociais-e-direitos.md)
- [04-setores-e-desenvolvimento.md](./04-setores-e-desenvolvimento.md)
- [05-gestao-e-infraestrutura.md](./05-gestao-e-infraestrutura.md)
- [06-orcamento-financas-e-economia.md](./06-orcamento-financas-e-economia.md)
- [07-controle-dados-e-acesso.md](./07-controle-dados-e-acesso.md)
- [08-poderes-entes-e-instituicoes.md](./08-poderes-entes-e-instituicoes.md)

## Diagrama

```mermaid
flowchart LR
    classDef root fill:#ECEFF1,stroke:#90A4AE,color:#263238;
    classDef soc fill:#E8F5E9,stroke:#81C784,color:#1B5E20;
    classDef set fill:#E3F2FD,stroke:#64B5F6,color:#0D47A1;
    classDef ges fill:#FFF8E1,stroke:#FFD54F,color:#8D6E00;
    classDef eco fill:#EDE7F6,stroke:#9575CD,color:#4527A0;
    classDef con fill:#FCE4EC,stroke:#F06292,color:#880E4F;
    classDef inst fill:#E0F2F1,stroke:#4DB6AC,color:#004D40;

    R["Transparencia publica"]:::root

    A["Politicas sociais e direitos"]:::soc
    B["Setores e desenvolvimento"]:::set
    C["Gestao e infraestrutura"]:::ges
    D["Orçamento, finanças e economia"]:::eco
    E["Controle, dados e acesso"]:::con
    F["Poderes, entes e instituições"]:::inst

    R --> A
    R --> B
    R --> C
    R --> D
    R --> E
    R --> F
```
