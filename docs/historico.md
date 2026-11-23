# Histórico

Minhas notas de como o projeto começou e mudou. O estado atual está em [`projeto.md`](projeto.md) e no README.

## v1 (16/11/2026)

Começou como projeto de uma semana, juntando duas ideias que eu tinha anotado: ONA com as métricas explicadas para RH e um visual de Power BI.

Resultado da v1 na base sintética de então (114 pessoas, semente 42): 9 de 9 testes passando, intermediação dirigida apontando as duas pontes e a dupla que ligava o Financeiro ao resto, Financeiro com E-I de -0,94, modularidade 0,61 com 6 comunidades (uma execução do Louvain), 23 ms de cálculo no Pi. A página ainda não tinha sido aberta num navegador.

Limites que a v2 corrigiu:

- intermediação só na rede dirigida: quem não respondeu nunca aparecia como ponte;
- E-I sem linha de base: "silo" era só um corte fixo em -0,9;
- Louvain com uma semente, sem medida de estabilidade nem checagem de comunidades desconectadas;
- gerador pseudoaleatório linear congruente com perda de precisão (a multiplicação passava de 2^53);
- sem papéis de corretagem, restrição de Burt, simulação de saída nem análise de sensibilidade à não resposta.

O texto do projeto para o site fica fora do repositório.

---

## Plano original (PLANO.md da v1)

Início: 16/11/2026. Meta: primeira versão de pé até 19/11.

### A pergunta

Como o RH, com um questionário simples e uma planilha, enxerga como a informação circula de verdade na equipe: quem conecta as áreas, quem está isolado, onde estão os silos e se o organograma bate com a rede real?

### Dados

- **Questionário padrão** (template versionado): perguntas de nomeação ("com quem você troca informação para fazer seu trabalho?", "a quem você pede ajuda quando trava?"), até 5 a 10 nomes por pergunta, escolhidos de uma lista fechada de colegas.
- **Saída do questionário = duas tabelas**:
  - `pessoas.csv`: `id, area, cargo, gestor_id, unidade, respondeu` (sem nome; id pseudonimizado).
  - `ligacoes.csv`: `origem_id, destino_id, tipo, peso` (tipo = informacao, ajuda, ...; peso = frequência 1 a 5, opcional).
- **Base de exemplo:** sintética, gerada por `src/gerar_base.py` (stdlib, semente fixa), com estrutura plantada para o leitor conferir que a ferramenta acha o que deveria: 2 ou 3 pontes entre áreas, 1 área em silo, alguns isolados, um gestor fora do fluxo do próprio time e 20% de não respondentes.
- Licença: tudo sintético, MIT. Nada de dado de empregador.

### Método (métricas e como viram insight)

| Métrica | Pergunta de gestor |
|---|---|
| Grau de entrada (citações recebidas) | Quem é procurado? |
| Intermediação (betweenness) | Quem é ponte? Se sair, o que desconecta? |
| Isolados e quase isolados | Quem está fora do fluxo? |
| Comunidades (modularidade, Louvain) × área formal | Os grupos reais batem com o organograma? |
| Índice E-I por área (ligações para fora − para dentro) | Que área virou silo? |
| Reciprocidade | A troca é de mão dupla? |
| Concentração (% das ligações nas 5% mais citadas) | A rede depende de poucas pessoas? |
| Gestor × time (distância do gestor ao próprio time) | O gestor está no fluxo do time? |

Avisos que o relatório sempre mostra: taxa de resposta (rede furada em quem não respondeu), ranking individual escondido por padrão e grupo mínimo de 5 pessoas para mostrar resultado por área (regra de limite de anonimato).

### Entregáveis

**v1 (até 19/11):**
1. `questionario/` — template do questionário (texto das perguntas, instruções, layout das duas tabelas) e uma planilha-modelo.
2. `src/gerar_base.py` — gerador da base sintética.
3. `web/ona.html` — página única, sem servidor: o usuário solta os dois CSVs, a página calcula as métricas no navegador, desenha a rede (cor por área, tamanho por intermediação) e escreve o relatório de insights em português.
4. Testes do motor de métricas contra a base sintética (o que foi plantado tem que aparecer).

**v2 (semana seguinte):** visual `.pbiviz` para Power BI (TypeScript + D3), reaproveitando o motor da v1.

### O que NÃO entra na v1

Coleta online do questionário (fica como planilha/Forms), dados de e-mail ou calendário (ONA passiva), análise ao longo do tempo, ranking individual em destaque, publicação no site.

### Decisões em aberto naquele momento

- Texto das perguntas (conferir com o que já usei na prática), quais métricas ficam na tela inicial, nome do projeto e se a página vai para o site já na v1.

### Riscos

- Desenho da rede pesado no navegador com muitas pessoas: limitar o desenho a ~500 nós e mostrar só métricas acima disso.
- Louvain em JavaScript puro: implementação própria precisa de teste; plano B é uma biblioteca pequena vendorizada (ex.: graphology), conferindo a licença.
- Power BI (v2): visual customizado exige o toolkit `pbiviz` (Node); conferir se roda no Raspberry Pi ou se o empacotamento fica para o PC.
- Privacidade: mesmo processando só no navegador, o texto da página tem que deixar claro o cuidado com LGPD e com o uso do resultado (diagnóstico de rede, não avaliação de pessoa).

---

## v2 (18/11/2026): motor JavaScript revisado

Rede simetrizada, E-I com linha de base, Louvain com 20 sementes, papéis de Gould e Fernandez, Burt, "e se sair" e sensibilidade à não resposta, tudo em JavaScript sem dependências (`web/ona-motor.js`, 43 testes em Node), com a página `web/ona.html` e o arquivo único `dist/ona-de-bolso.html`. Essa versão está preservada na tag `v1-javascript`.

## v3 (20/11/2026): Python como núcleo

O método foi reescrito em Python (`ona_de_bolso/`, com pandas e networkx), que é a stack que uso no dia a dia. O comportamento foi mantido e conferido contra o motor JS na base de exemplo (`testes/test_paridade_js.py`): tudo que não depende do Louvain bate número a número, porque o Python usa o mesmo gerador mulberry32 e as mesmas regras. Entraram também a linha de comando, o relatório HTML, o notebook e o app Streamlit, que roda no navegador com stlite na demonstração do site.

## v3.1 (22/11/2026): rede interativa e resumo para o gestor

Rede do app com zoom, arrastar, destaque dos vizinhos e tooltip; o botão "Simular a saída" do painel da pessoa passou a funcionar (o multiselect da aba "E se sair" ignorava o valor novo). Resumo de uma página para o gestor (`--gestor` e botão no app). O conversor de Forms deixou de quebrar com linha sem id na tabela de pessoas e passou a juntar a mesma pergunta repetida em várias seções. O questionário ganhou as perguntas por extenso, como escrever, como aplicar e como ler o resultado.
