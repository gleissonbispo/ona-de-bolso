# ONA de bolso: documento do projeto

Documento único do projeto: decisões, estado atual e próximos passos. O histórico da v1 está em [`historico.md`](historico.md).

- Status: v2 pronta, em revisão do Gleisson (18/11/2026). Repositório privado.
- Repositório: github.com/gleissonbispo/ona-de-bolso
- Página no site (rascunho, branch local `ona-lab` do `portfolio-gleisson`): `/laboratorio/ona`

## Pergunta

Como o RH, com um questionário simples e duas planilhas, enxerga como a informação circula de verdade: quem conecta as áreas, onde há silo, se o gestor está no fluxo do time e o que acontece se uma pessoa-chave sair?

## Como funciona

```
questionário (Forms)  ->  converter_forms.py  ->  pessoas.csv + ligacoes.csv  ->  página (navegador)
                                                                                 ├─ visão geral e insights
                                                                                 ├─ rede com "e se sair"
                                                                                 ├─ áreas, papéis, sensibilidade
                                                                                 └─ CSV por pessoa (Power BI)
```

Arquivos principais:

| Arquivo | Papel |
|---|---|
| `web/ona-motor.js` | Motor de métricas, sem dependências (navegador e Node) |
| `web/ona-ui.js` | Interface; monta a página dentro de qualquer elemento (`OnaUI.montar(el, opções)`). Usa as variáveis de cor do site |
| `web/ona.html` | Página do repositório (claro, escuro e automático) |
| `src/montar_pagina.py` | Gera `web/exemplo.js` e `dist/ona-de-bolso.html`; com `--site <pasta>` copia motor, interface e exemplo para o site com nota de origem |
| `src/gerar_base.py` | Base sintética com estrutura plantada (semente 42) |
| `src/converter_forms.py` | Exportação do Google Forms ou Microsoft Forms (`.csv`/`.xlsx`) para `ligacoes.csv` |
| `testes/teste_motor.js`, `testes/teste_converter.py` | Testes (rodam no GitHub Actions) |

## Decisões de método

| Decisão | Por quê |
|---|---|
| Rede simetrizada para intermediação, comunidades, E-I, Burt e saída; dirigida para citações, reciprocidade e corretagem | Informação corre nos dois sentidos, e na rede dirigida quem não respondeu nunca vira ponte. A opção `rede: "dirigida"` continua disponível no motor |
| Reciprocidade só entre pares em que os dois responderam | Quem não respondeu não teria como retribuir; contar esses pares puxava a reciprocidade para baixo |
| E-I comparado com 1.000 permutações das áreas | Toda área conversa mais para dentro do que o acaso. Silo = p < 0,01 e menos de 25% das ligações externas esperadas (`LIMIAR_SILO`) |
| Louvain 20 vezes, melhor modularidade, pedaços desconectados separados, estabilidade pelo Rand ajustado | Uma execução só depende da ordem de visita. O refinamento dá a garantia mínima do Leiden sem implementar o Leiden inteiro |
| Gould e Fernandez com fluxo de quem é citado para quem cita | As perguntas são do tipo "busco informação/ajuda com". O papel principal de cada pessoa usa: metade ou mais das entradas (porteiro) ou saídas (representante) da área; senão, o papel entre áreas mais frequente entre os 20% com mais corretagem |
| "E se sair" nas 10 maiores intermediações, com eficiência global | Eficiência continua definida quando a rede parte; distância média não (a página só mostra distância quando ninguém perde o caminho) |
| Sensibilidade: mais 10% de não resposta, 20 sorteios (10 acima de 300 pessoas, 5 acima de 1.000) | Mostra se pontes, isolados e silo aguentam menos dados |
| Regra de leitura | Abaixo de 70% de resposta: alerta e nenhum insight sobre pontes, isolados, Burt ou dependência. De 70% a 85%, ou pontes instáveis na simulação: "leia com cautela" |
| mulberry32 com semente 20261116 | Resultado reprodutível; teste compara com a sequência de referência |
| Grupo mínimo de 5 pessoas para resultado por área | Anonimato |
| Desenho até 500 pessoas | Layout de força O(n²) no navegador |

Prioridade dos insights: dados insuficientes (1), qualidade dos dados quando pede cautela (2), ponto único de falha (2), silo (3), porteiro concentrado (4), gestor fora do fluxo (4,5), pontes (5), isolados (6,5), Burt (7), demais áreas (8), comunidades (8,5), reciprocidade e concentração (9,5).

## Base de exemplo (sintética)

114 pessoas em 5 áreas (Comercial 30, Operações 34, Tecnologia 22, Financeiro 16, Gente e Gestão 12). Plantados: pontes P036 e P069; Financeiro em silo, ligado ao resto só por P088, que é porteiro (busca fora, o time busca nele) e ponto único de falha; P105, ponte que não respondeu; gestor do Comercial (P001) fora do fluxo; isolados P030, P064 e P086; 23 não respondentes (20%). O gabarito fica em `dados/exemplo/gabarito.json` e o resultado do motor em `dados/exemplo/resultado-exemplo.json`.

## Testes (18/11/2026)

43 de 43 no motor (20 em redes pequenas com resposta conhecida, 23 na base plantada) e 1 no conversor. Os principais números estão no README.

## Como rodar

```bash
python3 src/gerar_base.py
node testes/teste_motor.js
python3 testes/teste_converter.py
python3 src/montar_pagina.py                       # dist/ona-de-bolso.html
python3 src/montar_pagina.py --site ../portfolio-gleisson/public/lab/ona   # atualiza a cópia do site
```

## Decisões pendentes do Gleisson

1. Texto das perguntas do questionário (`questionario/questionario-ona.md`): conferir com o que já usou na prática.
2. Revisar a seção "O que aprendi" do README (rascunho).
3. Tornar o repositório público.
4. Publicar a página `/laboratorio/ona` (branch local `ona-lab` no site) e o texto do projeto (`~/hermes/site/projetos/ona-de-bolso.md`).
5. Limiar de silo (25%) e de resposta (70%): manter ou ajustar.

## Próximos passos

- v3: visual para Power BI (`.pbiviz`, TypeScript + D3) reaproveitando o motor. Conferir se o toolkit `pbiviz` roda no Pi.
- Comparar duas rodadas do questionário (antes e depois de uma reorganização).
- Artigo da newsletter sobre ONA usando a base de exemplo.
