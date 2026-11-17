---
projeto: ONA de bolso
id: P009
status: v1 montada, em validação
inicio: 2026-11-16
validar_ate: 2026-11-19
repositorio: https://github.com/gleissonbispo/ona-de-bolso (privado)
pasta: ~/projetos_portfolio/ona-de-bolso
---

# ONA de bolso — o projeto completo

## 1. A ideia

Um kit para o RH enxergar a rede real da equipe sem software caro: um questionário padrão gera duas tabelas, e uma página lê essas tabelas e devolve a rede desenhada, as métricas de ONA (Organizational Network Analysis) e um relatório de insights em português. Depois, o mesmo motor vira um visual para Power BI.

Origem: ideia do Gleisson (16/11/2026), juntando duas ideias do banco de projetos: ONA com métricas explicadas para RH e visual de Power BI.

**A pergunta de negócio:** como a informação circula de verdade na equipe? Quem conecta as áreas, quem está fora do fluxo, onde estão os silos e o organograma bate com a rede real?

## 2. Como funciona

```
questionário (Forms)  ->  pessoas.csv + ligacoes.csv  ->  página ONA de bolso (navegador)
                                                         ├─ rede desenhada
                                                         ├─ métricas e insights
                                                         └─ CSV de métricas por pessoa -> Power BI
```

**Privacidade como princípio:** a página calcula tudo no navegador de quem usa. Nenhuma tabela vai para servidor. Ids pseudonimizados, ranking individual escondido por padrão e áreas com menos de 5 pessoas fora dos resultados por área.

## 3. Entrada: o questionário e as duas tabelas

Detalhe completo em `questionario/questionario-ona.md`.

Perguntas de nomeação (cada uma vira um `tipo`):
- `informacao`: com quem você trocou informação importante para o seu trabalho nas últimas 4 semanas? (até 10 nomes)
- `ajuda`: a quem você pede ajuda quando trava? (até 5)
- opcionais: `ideias`, `energia`.
- frequência de 1 a 5 vira o `peso`.

Tabelas:
- `pessoas.csv`: `id, area, cargo, gestor_id, unidade, respondeu` (todas as pessoas convidadas, inclusive quem não respondeu).
- `ligacoes.csv`: `origem_id, destino_id, tipo, peso` (uma linha por nome citado).

## 4. Métricas e o que cada uma responde

| Métrica | Pergunta de gestor |
|---|---|
| Citações recebidas (grau de entrada) | Quem é procurado? |
| Intermediação (betweenness, Brandes) | Quem é ponte? Se sair, o que desconecta? |
| Isolados (ninguém cita e cita no máximo uma pessoa) | Quem está fora do fluxo? |
| Comunidades (Louvain) e modularidade | Os grupos reais batem com o organograma? |
| Índice E-I por área (-1 só para dentro, +1 só para fora) | Que área virou silo? |
| Coesão da área (fração na mesma comunidade) | A área conversa como um time ou está partida? |
| Reciprocidade | A troca é de mão dupla? |
| Concentração (% das citações nas 5% mais citadas) | A rede depende de poucas pessoas? |
| Gestor × time (fração do time ligada ao gestor) | O gestor está no fluxo do time? |
| Taxa de resposta | Dá para confiar no desenho? |

Avisos automáticos do relatório: taxa de resposta (rede furada em quem não respondeu), isolamento como sinal para conversar e não como diagnóstico, e nenhum uso da tabela por pessoa para avaliação.

## 5. O que está pronto (v1)

| Arquivo | O que é |
|---|---|
| `questionario/questionario-ona.md` | Perguntas, cuidados de LGPD e layout das tabelas |
| `src/gerar_base.py` | Gerador da organização fictícia (stdlib, semente 42) |
| `dados/exemplo/` | Base de exemplo, gabarito do que foi plantado e resultado do motor |
| `web/ona-motor.js` | Motor de métricas, sem dependências; roda no navegador e no Node |
| `web/ona.html` | A página (usa `ona-motor.js` e `exemplo.js`) |
| `src/montar_pagina.py` | Gera `web/exemplo.js` e `dist/ona-de-bolso.html` num arquivo só |
| `dist/ona-de-bolso.html` | Página pronta, abre com duplo clique; `#exemplo` no fim do endereço carrega a base de exemplo |
| `testes/teste_motor.js` | Confere se o motor acha o que o gerador plantou |
| `PLANO.md` | Plano original, com escopo e riscos |

### Base de exemplo (sintética)
114 pessoas em 5 áreas (Comercial 30, Operações 34, Tecnologia 22, Financeiro 16, Gente e Gestão 12). Plantados de propósito: 2 pontes (P036, P069), Financeiro como silo ligado ao resto só por uma dupla, 3 isolados, o gestor do Comercial (P001) fora do fluxo do time e 23 não respondentes (20%).

### Resultado do teste (9 de 9)
- 114 pessoas e 752 pares ligados (819 citações por tipo).
- As 4 maiores intermediações são as 2 pontes plantadas e a dupla que liga o Financeiro ao resto (P003 e P087). A dupla não foi planejada como ponte, mas é: sem ela o Financeiro fica desconectado.
- Financeiro com o menor E-I: -0,94.
- Isolados plantados encontrados (mais o gestor P001, que ninguém cita).
- Gestor do Comercial: 0 de 29 pessoas do time ligadas a ele.
- Taxa de resposta 79,8%; modularidade 0,61 com 6 comunidades; reciprocidade 15%; as 5% mais citadas recebem 11% das citações.
- Cálculo em 23 ms no Raspberry Pi.

### Limites conhecidos da v1
- A página ainda não foi aberta num navegador de verdade (o Pi não tem Chromium funcional); só a sintaxe e o motor foram testados.
- Desenho da rede em layout de força simples (O(n²)): bom até algumas centenas de pessoas.
- Intermediação sem peso e dirigida; Louvain sem peso de tipo.

## 6. Como rodar

```bash
cd ~/projetos_portfolio/ona-de-bolso
python3 src/gerar_base.py      # base de exemplo
node testes/teste_motor.js     # testes
python3 src/montar_pagina.py   # página num arquivo só em dist/
```

## 7. Próximos passos

**Validação (até 19/11), decisões do Gleisson:**
1. Perguntas do questionário batem com a prática dele?
2. Quais números ficam no topo da página?
3. Nome final do projeto e do repositório.
4. A página vai para o site já na v1?

**v2 — visual para Power BI:**
- Visual customizado `.pbiviz` (TypeScript + D3) reaproveitando `ona-motor.js`.
- Conferir se o toolkit `pbiviz` roda no Pi; se não, empacotar no PC dele.
- Entrada pelo próprio modelo do Power BI: tabela de pessoas e de ligações relacionadas por id.

**Depois:**
- Página pública no site (gleissonbispo.com.br), com o processamento só no navegador como destaque.
- Repositório público com licença MIT, README final e "O que aprendi".
- Artigo da newsletter sobre ONA (ideias I03, I06 e I61 do banco de artigos já estão prontas de fonte).
