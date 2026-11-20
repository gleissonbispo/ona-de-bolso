# ONA de bolso: documento do projeto

Documento único do projeto: decisões, estado atual e próximos passos. O histórico está em [`historico.md`](historico.md).

- Status: v3 (Python) pronta, em revisão do Gleisson (20/11/2026). Repositório privado.
- Repositório: github.com/gleissonbispo/ona-de-bolso. A versão JavaScript está na tag `v1-javascript`.
- No site: fica como **projeto** (não no Laboratório). A demonstração interativa está no branch local `ona-demo` do `portfolio-gleisson`, em `/projetos/ona-de-bolso/demo`. O texto do projeto está em `~/hermes/site/projetos/ona-de-bolso.md` (`published: false`).

## Pergunta

Como o RH, com um questionário simples e duas planilhas, enxerga como a informação circula de verdade: quem conecta as áreas, onde há silo, se o gestor está no fluxo do time e o que acontece se uma pessoa-chave sair?

## Como funciona

```
questionário (Forms) -> ona-de-bolso converter-forms -> pessoas.csv + ligacoes.csv
                                                          |
                     ona_de_bolso.analisar() <------------+
                       |-> insights em português, regra de leitura
                       |-> relatório HTML (cli), CSV por pessoa (Power BI)
                       |-> notebook (análise passo a passo)
                       '-> app Streamlit (local ou no navegador com stlite)
```

| Arquivo | Papel |
|---|---|
| `ona_de_bolso/io.py` | Leitura de CSV e XLSX (leitor próprio, sem openpyxl), validação, modelos e conversor de Forms |
| `ona_de_bolso/metricas.py` | O método: duas redes, intermediação, Louvain estável, E-I com permutação, Gould e Fernandez, Burt, k-core, "e se sair", sensibilidade |
| `ona_de_bolso/insights.py` | Regra de leitura (70% e 85%) e textos dos insights |
| `ona_de_bolso/relatorio.py` | Relatório HTML num arquivo só, com o desenho da rede em SVG |
| `ona_de_bolso/cli.py` | `ona-de-bolso analisar`, `converter-forms`, `exemplo` |
| `app/app.py` | App Streamlit; o mesmo arquivo roda no navegador |
| `scripts/montar_demo.py` | Gera `demo/index.html` (stlite 1.12.2 + app + pacote + base de exemplo embutidos) |
| `scripts/montar_notebook.py` | Monta e executa `notebooks/analise-ona.ipynb` |
| `scripts/gerar_base.py` | Base sintética com estrutura plantada (semente 42) |
| `testes/` | pytest: algoritmos, base plantada, paridade com o JS, io, cli e app |

## Decisões de método

| Decisão | Por quê |
|---|---|
| Rede simetrizada para intermediação, comunidades, E-I, Burt e saída; dirigida para citações, reciprocidade e corretagem | Informação corre nos dois sentidos, e na rede dirigida quem não respondeu nunca vira ponte. A opção `rede="dirigida"` continua disponível em `analisar()` |
| Reciprocidade só entre pares em que os dois responderam | Quem não respondeu não teria como retribuir; contar esses pares puxava a reciprocidade para baixo |
| E-I comparado com 1.000 permutações das áreas | Toda área conversa mais para dentro do que o acaso. Silo = p < 0,01 e menos de 25% das ligações externas esperadas (`LIMIAR_SILO`) |
| Louvain 20 vezes, melhor modularidade, pedaços desconectados separados, estabilidade pelo Rand ajustado | Uma execução só depende da ordem de visita. O refinamento dá a garantia mínima do Leiden sem implementar o Leiden inteiro |
| Gould e Fernandez com fluxo de quem é citado para quem cita | As perguntas são do tipo "busco informação/ajuda com". O papel principal de cada pessoa usa: metade ou mais das entradas (porteiro) ou saídas (representante) da área; senão, o papel entre áreas mais frequente entre os 20% com mais corretagem |
| "E se sair" nas 10 maiores intermediações, com eficiência global | Eficiência continua definida quando a rede parte; distância média não (a página só mostra distância quando ninguém perde o caminho) |
| Sensibilidade: mais 10% de não resposta, 20 sorteios (10 acima de 300 pessoas, 5 acima de 1.000) | Mostra se pontes, isolados e silo aguentam menos dados |
| Regra de leitura | Abaixo de 70% de resposta: alerta e nenhum insight sobre pontes, isolados, Burt ou dependência. De 70% a 85%, ou pontes instáveis na simulação: "leia com cautela" |
| mulberry32 com semente 20261116 | Resultado reprodutível e igual ao do motor JS (mesma sequência de sorteios); teste compara com a sequência de referência |
| Grupo mínimo de 5 pessoas para resultado por área | Anonimato |
| Desenho até 499 pessoas | O layout de força denso do networkx vai até 499; acima, ele exige scipy, que pesa 14 MB no navegador |
| networkx onde ele resolve; Burt e eficiência reescritos | A restrição de Burt do networkx levava 10 s na base de exemplo. A fórmula é a mesma, conferida em teste |
| Rede desenhada com Altair | Já vem com o Streamlit, inclusive no stlite; plotly seriam mais 10 MB baixados na demo |
| networkx na demo pelo arquivo do Pyodide | Pelo nome, o Pyodide traria o matplotlib junto (7 MB a mais) |

Prioridade dos insights: dados insuficientes (1), qualidade dos dados quando pede cautela (2), ponto único de falha (2), silo (3), porteiro concentrado (4), gestor fora do fluxo (4,5), pontes (5), isolados (6,5), Burt (7), demais áreas (8), comunidades (8,5), reciprocidade e concentração (9,5).

## Base de exemplo (sintética)

114 pessoas em 5 áreas (Comercial 30, Operações 34, Tecnologia 22, Financeiro 16, Gente e Gestão 12). Plantados: pontes P036 e P069; Financeiro em silo, ligado ao resto só por P088, que é porteiro (busca fora, o time busca nele) e ponto único de falha; P105, ponte que não respondeu; gestor do Comercial (P001) fora do fluxo; isolados P030, P064 e P086; 23 não respondentes (20%). O gabarito fica em `ona_de_bolso/exemplo/gabarito.json`.

## Testes (20/11/2026)

68 testes no pytest, todos passando: algoritmos em redes conhecidas, base plantada, paridade com o motor JS, leitura de arquivos, CLI e o app (AppTest do Streamlit). A paridade com o JS é exata em tudo que não depende do Louvain; modularidade 0,5401 nas duas versões e estabilidade 0,90 (Python) contra 0,91 (JS).

Desempenho na base de exemplo: 1,6 s no Python do Raspberry Pi 5. Na demonstração no navegador (Chromium no Pi), o app abre em cerca de 25 s na primeira visita, baixando cerca de 30 MB, e a análise leva cerca de 9 s.

## Como rodar

```bash
uv sync
uv run pytest
uv run ona-de-bolso analisar ona_de_bolso/exemplo/pessoas.csv ona_de_bolso/exemplo/ligacoes.csv --saida relatorio.html
uv run streamlit run app/app.py
uv run python scripts/montar_notebook.py     # reexecuta o notebook
uv run python scripts/montar_demo.py         # regera demo/index.html (copiar para o site: public/demos/ona-de-bolso/index.html)
python testes/gerar_referencia_js.py         # regera a referência do JS (precisa de node e da tag v1-javascript)
```

## Decisões pendentes do Gleisson

1. Revisar a seção "O que aprendi" do README (rascunho).
2. Texto das perguntas do questionário (`questionario/questionario-ona.md`): conferir com o que já usou na prática.
3. Tornar o repositório público (o README aponta para a demo do site, que só existe depois do merge do branch `ona-demo`).
4. Publicar o projeto no site: merge do branch `ona-demo` e `publicar_projeto.py ~/hermes/site/projetos/ona-de-bolso.md`.
5. Limiar de silo (25%) e de resposta (70%): manter ou ajustar.

## Próximos passos

- Comparar duas rodadas do questionário (antes e depois de uma reorganização).
- Artigo da newsletter sobre ONA usando a base de exemplo e o notebook.
- Visual para Power BI (ficou para depois; o CSV por pessoa já atende a maior parte dos casos).
