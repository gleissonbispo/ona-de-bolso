# Questionário de ONA (modelo)

Modelo para coletar a rede de uma equipe com um formulário comum (Google Forms, Microsoft Forms, Qualtrics) e transformar as respostas nas duas tabelas que a ONA de bolso lê.

## Antes de enviar

- **Diga para que serve e o que não vai acontecer.** Exemplo de texto de convite: "Queremos entender como a informação circula entre as áreas para melhorar processos e integração. As respostas não entram em avaliação de desempenho, e os resultados são mostrados por área, nunca por pessoa."
- **Base legal e transparência (LGPD).** Alinhe com o jurídico e o DPO antes de rodar: finalidade, quem vê o resultado, por quanto tempo os dados ficam guardados.
- **Lista fechada de nomes.** A pessoa escolhe colegas de uma lista (de preferência com busca), não digita nomes. Digitação livre gera erro de grafia e homônimo.
- **Taxa de resposta importa mais do que numa pesquisa de clima.** Quem não responde deixa a rede furada exatamente nas ligações que faria. Abaixo de 70%, leia isolados e pontes com cautela.

## Perguntas

Use de 2 a 4 perguntas de nomeação. Cada uma vira um `tipo` na tabela de ligações.

| tipo | Pergunta | Até quantos nomes |
|---|---|---|
| `informacao` | Nas últimas 4 semanas, com quem você trocou informação importante para fazer o seu trabalho? | 10 |
| `ajuda` | Quando você trava num problema de trabalho, a quem você costuma pedir ajuda? | 5 |
| `ideias` (opcional) | Com quem você costuma discutir ideias novas ou melhorias? | 5 |
| `energia` (opcional) | Depois de conversar com quais colegas você costuma sair com mais energia para trabalhar? | 5 |

Para cada nome escolhido, pergunte a frequência (opcional, vira o `peso`):
1 = uma vez no período · 2 = mensal · 3 = quinzenal · 4 = semanal · 5 = diária.

## As duas tabelas

**pessoas.csv** (vem do cadastro do RH, não do formulário):

| coluna | conteúdo |
|---|---|
| `id` | código pseudonimizado (não use matrícula nem nome) |
| `area` | área ou diretoria |
| `cargo` | cargo ou nível |
| `gestor_id` | `id` do gestor imediato (vazio para o topo) |
| `unidade` | site, cidade ou unidade (opcional) |
| `respondeu` | `sim` ou `nao` |

Inclua **todas** as pessoas convidadas, inclusive quem não respondeu.

**ligacoes.csv** (vem das respostas, uma linha por nome citado):

| coluna | conteúdo |
|---|---|
| `origem_id` | quem respondeu |
| `destino_id` | quem foi citado |
| `tipo` | `informacao`, `ajuda`, ... |
| `peso` | frequência de 1 a 5 (opcional) |

Separador vírgula ou ponto e vírgula, codificação UTF-8. Os arquivos de `dados/exemplo/` mostram o formato.

## Cuidados na leitura

- A rede mostra como a informação circula, não quem trabalha melhor. Não use a tabela por pessoa para avaliar ou ranquear.
- Áreas com menos de 5 pessoas ficam de fora dos resultados por área.
- "Isolado" é sinal para conversar (pessoa nova, afastada, remota, que não respondeu), não um diagnóstico.
