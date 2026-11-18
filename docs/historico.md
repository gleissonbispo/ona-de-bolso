# Histórico

Registro de como o projeto começou. O estado atual está em [`projeto.md`](projeto.md) e no README.

## v1 (16/11/2026)

Projeto semanal P009, montado pelo Hermes (agente do Gleisson) a partir de uma ideia dele: juntar duas ideias do banco de projetos (ONA com métricas explicadas para RH e visual de Power BI).

Resultado da v1 na base sintética de então (114 pessoas, semente 42): 9 de 9 testes passando, intermediação dirigida apontando as duas pontes e a dupla que ligava o Financeiro ao resto, Financeiro com E-I de -0,94, modularidade 0,61 com 6 comunidades (uma execução do Louvain), 23 ms de cálculo no Pi. A página ainda não tinha sido aberta num navegador.

Limites que a v2 corrigiu:

- intermediação só na rede dirigida: quem não respondeu nunca aparecia como ponte;
- E-I sem linha de base: "silo" era só um corte fixo em -0,9;
- Louvain com uma semente, sem medida de estabilidade nem checagem de comunidades desconectadas;
- gerador pseudoaleatório linear congruente com perda de precisão (a multiplicação passava de 2^53);
- sem papéis de corretagem, restrição de Burt, simulação de saída nem análise de sensibilidade à não resposta.

O arquivo `projeto.md` da v1 era o modelo em branco do texto do site; o texto do site agora fica fora do repositório.

---

## Plano original (PLANO.md da v1)

Início: 16/11/2026 · Validar com o Gleisson até quinta, 19/11.

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

Avisos que o relatório sempre mostra: taxa de resposta (rede furada em quem não respondeu), ranking individual escondido por padrão e grupo mínimo de 5 pessoas para mostrar resultado por área (regra do artigo de limite de anonimato).

### Entregáveis

**v1 (até quinta, para validar):**
1. `questionario/` — template do questionário (texto das perguntas, instruções, layout das duas tabelas) e uma planilha-modelo.
2. `src/gerar_base.py` — gerador da base sintética.
3. `web/ona.html` — página única, sem servidor: o usuário solta os dois CSVs, a página calcula as métricas no navegador, desenha a rede (cor por área, tamanho por intermediação) e escreve o relatório de insights em português.
4. Testes do motor de métricas contra a base sintética (o que foi plantado tem que aparecer).

**v2 (semana seguinte):** visual `.pbiviz` para Power BI (TypeScript + D3), reaproveitando o motor da v1.

### O que NÃO entra na v1

Coleta online do questionário (fica como planilha/Forms), dados de e-mail ou calendário (ONA passiva), análise ao longo do tempo, ranking individual em destaque, publicação no site.

### Divisão do trabalho

- **Hermes:** template do questionário, gerador, motor de métricas em JavaScript, página, testes, README.
- **Gleisson decide:** texto das perguntas (validar com o que já usou na prática), quais métricas ficam na tela inicial, nome do projeto e do repositório, e se a página vai para o site já na v1.

### Riscos

- Desenho da rede pesado no navegador com muitas pessoas: limitar o desenho a ~500 nós e mostrar só métricas acima disso.
- Louvain em JavaScript puro: implementação própria precisa de teste; plano B é uma biblioteca pequena vendorizada (ex.: graphology), conferindo a licença.
- Power BI (v2): visual customizado exige o toolkit `pbiviz` (Node); conferir se roda no Pi ou se o empacotamento fica para o PC dele.
- Privacidade: mesmo processando só no navegador, o texto da página tem que deixar claro o cuidado com LGPD e com o uso do resultado (diagnóstico de rede, não avaliação de pessoa).
