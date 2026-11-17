# ONA de bolso

Com um questionário simples e duas planilhas, enxergar como a informação circula de verdade na equipe: quem conecta as áreas, quem está fora do fluxo, onde estão os silos e se o organograma bate com a rede real.

> Em construção (v1). Validação até 19/11/2026.

## O que tem aqui
- `questionario/questionario-ona.md`: perguntas, cuidados de LGPD e o layout das duas tabelas (`pessoas.csv` e `ligacoes.csv`).
- `src/gerar_base.py`: gera uma organização fictícia de 114 pessoas com estrutura plantada (pontes, um silo, isolados, um gestor fora do fluxo, 20% sem resposta).
- `web/ona-motor.js`: o motor de métricas, sem dependências. Roda no navegador e no Node.
- `web/ona.html`: a página. Lê os dois CSVs no navegador, calcula tudo localmente e escreve o relatório.
- `dist/ona-de-bolso.html`: a página num arquivo só, com a base de exemplo embutida. Abre com duplo clique.
- `testes/teste_motor.js`: confere se o motor acha o que o gerador plantou.

## Métricas
Citações recebidas e feitas, intermediação (betweenness), isolados, comunidades (Louvain) e modularidade, índice E-I por área, reciprocidade, concentração das citações e ligação do gestor com o próprio time.

## Dados
Sintéticos, gerados por `src/gerar_base.py` com semente fixa. Nenhum dado de empregador.

## Como rodar
```bash
python3 src/gerar_base.py      # base de exemplo em dados/exemplo/
node testes/teste_motor.js     # confere o motor contra o gabarito
python3 src/montar_pagina.py   # gera dist/ona-de-bolso.html
```
Abra `dist/ona-de-bolso.html#exemplo` para ver a base de exemplo carregada.

## O que aprendi
(no fim do projeto)

## Origem
Ideia do Gleisson, 16/11/2026. Junta duas ideias do banco: ONA com métricas explicadas para RH e visual de Power BI.
