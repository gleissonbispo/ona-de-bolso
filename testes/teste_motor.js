// Testes do motor (node testes/teste_motor.js).
// Parte 1: redes pequenas com resposta conhecida (conferem cada algoritmo isolado).
// Parte 2: a base sintética, que tem estrutura plantada pelo gerador (o que foi plantado tem de aparecer).
const fs = require("fs");
const path = require("path");
const ONA = require("../web/ona-motor.js");
const I = ONA._int;

let falhas = 0, total = 0;
function confere(nome, ok, detalhe) {
  total++;
  console.log((ok ? "ok    " : "FALHOU") + "  " + nome + (detalhe ? "  (" + detalhe + ")" : ""));
  if (!ok) falhas++;
}
const perto = (a, b, tol) => Math.abs(a - b) < (tol || 1e-9);
const f3 = (x) => (x === null ? "null" : x.toFixed(3));
const pessoasDe = (n, area) => Array.from({ length: n }, (_, i) => ({ id: "N" + i, area: area ? area(i) : "A", respondeu: "sim" }));
const cita = (pares, tipo) => pares.map(([o, d]) => ({ origem_id: "N" + o, destino_id: "N" + d, tipo: tipo || "informacao", peso: "1" }));

console.log("Parte 1: algoritmos em redes conhecidas\n");

// gerador pseudoaleatório
const r1 = I.mulberry32(1);
confere("mulberry32 reproduz a sequência de referência", perto(r1(), 0.6270739405881613) && perto(r1(), 0.002735721180215478));
const r2 = I.mulberry32(20261116); let soma = 0, fora = 0;
for (let i = 0; i < 20000; i++) { const x = r2(); soma += x; if (x < 0 || x >= 1) fora++; }
confere("mulberry32 fica em [0,1) com média perto de 0,5", fora === 0 && perto(soma / 20000, 0.5, 0.01), "média " + (soma / 20000).toFixed(4));

// intermediação: caminho 0-1-2-3-4 (não dirigido). Centro (2) está em 4 dos 6 pares possíveis sem ele.
const cam = I.grafoDeArestas(5, [[0, 1], [1, 2], [2, 3], [3, 4]]);
const bc = I.intermediacao(cam.adjS, 5);
confere("intermediação no caminho de 5: 0,5 / 0,667 / 0,5 nas pessoas do meio", perto(bc[1], 0.5) && perto(bc[2], 4 / 6) && perto(bc[3], 0.5) && bc[0] === 0, bc.map(f3).join(" "));
// estrela: o centro está em todos os caminhos
const est = I.grafoDeArestas(5, [[0, 1], [0, 2], [0, 3], [0, 4]]);
confere("intermediação do centro de uma estrela = 1", perto(I.intermediacao(est.adjS, 5)[0], 1));

// rede simetrizada x dirigida: quem não respondeu (não cita ninguém) só vira ponte na simetrizada
// 0 e 1 (área A) citam 4; 2 e 3 (área B) citam 4; 4 não respondeu.
const ppl = pessoasDe(5, (i) => (i < 2 ? "A" : i < 4 ? "B" : "C")); ppl[4].respondeu = "nao";
const lig = cita([[0, 1], [1, 0], [2, 3], [3, 2], [0, 4], [1, 4], [2, 4], [3, 4]]);
const rs = ONA.analisar(ppl, lig, { sensibilidade: false, permutacoes: 50 });
const rd = ONA.analisar(ppl, lig, { sensibilidade: false, permutacoes: 50, rede: "dirigida" });
confere("não respondente que liga dois grupos: ponte na simetrizada, invisível na dirigida",
  rs.por_pessoa[4].intermediacao > 0.5 && rd.por_pessoa[4].intermediacao === 0, "simetrizada " + f3(rs.por_pessoa[4].intermediacao) + ", dirigida " + f3(rd.por_pessoa[4].intermediacao));

// Louvain: duas panelinhas de 5 ligadas por uma aresta
const ar = [];
for (let a = 0; a < 5; a++) for (let b = a + 1; b < 5; b++) { ar.push([a, b]); ar.push([a + 5, b + 5]); }
ar.push([4, 5]);
const duas = I.grafoDeArestas(10, ar);
const cm = I.comunidadesEstaveis(duas, 7, 20);
const certo = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1];
confere("Louvain separa duas panelinhas ligadas por uma ponte", I.randAjustado(cm.comunidade, certo) === 1, "Q = " + cm.modularidade.toFixed(3));
confere("20 execuções concordam (estabilidade = 1)", perto(cm.estabilidade, 1), f3(cm.estabilidade));
confere("modularidade da partição certa = 0,452 (conta à mão: 2 x (20/42 - (21/42)^2))",
  perto(I.modularidade(duas.viz, certo), 2 * (20 / 42 - Math.pow(21 / 42, 2)), 1e-9), I.modularidade(duas.viz, certo).toFixed(3));

// refinamento: uma comunidade com dois pedaços sem ligação vira duas, e a modularidade não cai
const ruim = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0].map((_, i) => (i < 3 || i >= 8 ? 0 : 1)); // {0,1,2,8,9} desconexo
const sep = I.separarDesconexas(duas.adjS, ruim);
confere("refinamento separa comunidade desconectada", !I.comunidadeConexa(duas.adjS, ruim) && I.comunidadeConexa(duas.adjS, sep) && new Set(sep).size === 3,
  "Q antes " + I.modularidade(duas.viz, ruim).toFixed(3) + ", depois " + I.modularidade(duas.viz, sep).toFixed(3));
confere("separar pedaços desconectados não reduz a modularidade", I.modularidade(duas.viz, sep) >= I.modularidade(duas.viz, ruim));

// Rand ajustado
confere("Rand ajustado: 1 para partições iguais com rótulos trocados", perto(I.randAjustado([0, 0, 1, 1], [5, 5, 3, 3]), 1));

// E-I com linha de base: num grafo completo, qualquer troca de rótulos dá o mesmo E-I (esperado = observado = fórmula)
const comp = []; for (let a = 0; a < 10; a++) for (let b = a + 1; b < 10; b++) comp.push([a, b]);
const k10 = I.grafoDeArestas(10, comp);
const grp = [0, 0, 0, 0, 1, 1, 1, 1, 1, 1];
const eik = I.eiComBase(k10.adjS, grp, 2, 200, 3);
confere("E-I no grafo completo: observado = esperado = fórmula (4 de 10: 0,6)",
  perto(eik[0].ei, 0.6) && perto(eik[0].ei_esperado, 0.6) && perto(I.eiEsperadoFormula(4, 10), 0.6) && eik[0].p_valor === 1, "p = " + eik[0].p_valor);
// duas panelinhas: E-I muito abaixo do esperado, p pequeno
const eid = I.eiComBase(duas.adjS, certo, 2, 999, 3);
confere("E-I das panelinhas fica muito abaixo do acaso (p < 0,01)", eid[0].ei < eid[0].ei_esperado - 0.5 && eid[0].p_valor < 0.01,
  "obs " + eid[0].ei.toFixed(2) + ", esperado " + eid[0].ei_esperado.toFixed(2) + ", p " + eid[0].p_valor.toFixed(3));

// Gould e Fernandez: um caminho A -> B -> C para cada papel (cita = busca com; a informação vai de quem é citado para quem cita)
function papelDe(areas) { // areas de [A, B, C]; C cita B, B cita A
  const p = areas.map((a, i) => ({ id: "N" + i, area: a, respondeu: "sim" }));
  const g = I.montar(p, cita([[2, 1], [1, 0]]));
  const grupo = areas.map((a) => a.charCodeAt(0));
  const c = I.papeisCorretagem(g, grupo)[1];
  return Object.keys(c).filter((k) => c[k] === 1).join(",");
}
const papeis = { coordenador: ["X", "X", "X"], consultor: ["X", "Y", "X"], representante: ["X", "X", "Y"], porteiro: ["Y", "X", "X"], ligacao: ["X", "Y", "Z"] };
confere("Gould e Fernandez: os cinco papéis em caminhos de três pessoas",
  Object.keys(papeis).every((k) => papelDe(papeis[k]) === k), Object.keys(papeis).map((k) => k + "=" + papelDe(papeis[k])).join(" "));
{
  const p = ["X", "X", "X"].map((a, i) => ({ id: "N" + i, area: a, respondeu: "sim" }));
  const g = I.montar(p, cita([[2, 1], [1, 0], [2, 0]]));
  const c = I.papeisCorretagem(g, [0, 0, 0])[1];
  confere("Gould e Fernandez: não conta corretagem quando C já busca direto com A", c.coordenador === 0);
}

// Burt: estrela e triângulo (valores do livro de 1992)
const bEst = I.burt(I.grafoDeArestas(4, [[0, 1], [0, 2], [0, 3]]).viz);
confere("Burt na estrela de 3: restrição do centro 0,333, tamanho efetivo 3; folha com restrição 1",
  perto(bEst.restricao[0], 1 / 3) && perto(bEst.tamanho_efetivo[0], 3) && perto(bEst.restricao[1], 1));
const bTri = I.burt(I.grafoDeArestas(3, [[0, 1], [1, 2], [0, 2]]).viz);
confere("Burt no triângulo: restrição 1,125, tamanho efetivo 1", perto(bTri.restricao[0], 1.125) && perto(bTri.tamanho_efetivo[0], 1),
  f3(bTri.restricao[0]) + " / " + f3(bTri.tamanho_efetivo[0]));

// núcleo (k-core)
const nk = I.nucleos(I.grafoDeArestas(6, [[0, 1], [1, 2], [0, 2], [2, 3], [3, 4], [4, 5]]).adjS);
confere("k-core: triângulo = 2, cauda = 1", JSON.stringify(nk) === "[2,2,2,1,1,1]", JSON.stringify(nk));

// e se sair: no caminho 0-1-2-3-4, tirar o 2 parte a rede em duas
const baseCam = I.estruturaRede(cam.adjS);
const sai2 = I.efeitoSaida(cam.adjS, baseCam, [2]);
confere("tirar o meio do caminho parte a rede (2 componentes, 2 perdem o caminho)", sai2.componentes === 2 && sai2.perdem_caminho.length === 2,
  "eficiência " + baseCam.eficiencia.toFixed(3) + " -> " + sai2.eficiencia.toFixed(3));
confere("eficiência global do caminho de 5 = 0,642 (conta à mão)", perto(baseCam.eficiencia, (2 * (4 + 3 * 0.5 + 2 / 3 + 0.25)) / 20, 1e-9));

console.log("\nParte 2: base sintética com estrutura plantada\n");

const base = path.join(__dirname, "..", "dados", "exemplo");
const pessoas = ONA.lerCSV(fs.readFileSync(path.join(base, "pessoas.csv"), "utf8"));
const ligacoes = ONA.lerCSV(fs.readFileSync(path.join(base, "ligacoes.csv"), "utf8"));
const gab = JSON.parse(fs.readFileSync(path.join(base, "gabarito.json"), "utf8"));

const v = ONA.validar(pessoas, ligacoes);
confere("validação sem erros", v.erros.length === 0, v.erros.join("; "));

const t0 = Date.now();
const r = ONA.analisar(pessoas, ligacoes);
const ms = Date.now() - t0;
const pp = Object.fromEntries(r.por_pessoa.map((p) => [p.id, p]));

confere("pessoas, citações e pares lidos", r.pessoas === gab.pessoas && r.citacoes === gab.pares_citados && r.ligacoes === gab.pares_ligados,
  r.pessoas + " pessoas, " + r.citacoes + " citações, " + r.ligacoes + " pares ligados");

const top5 = r.pontes.map((p) => p.id);
confere("pontes plantadas e porteiro do silo estão entre as 5 maiores intermediações",
  gab.pontes.concat([gab.porteiro]).every((x) => top5.includes(x)), "top 5: " + r.pontes.map((p) => p.id + "=" + p.intermediacao.toFixed(3)).join(", "));

const ranks = r.por_pessoa.slice().sort((a, b) => b.intermediacao - a.intermediacao).map((p) => p.id);
const pnr = pp[gab.ponte_nao_respondente];
confere("ponte que não respondeu: zero na rede dirigida, entre as 10 maiores na simetrizada",
  pnr.intermediacao_dirigida === 0 && ranks.indexOf(gab.ponte_nao_respondente) < 10,
  gab.ponte_nao_respondente + ": posição " + (ranks.indexOf(gab.ponte_nao_respondente) + 1) + ", " + f3(pnr.intermediacao_simetrizada));

const silo = r.areas.find((a) => a.area === gab.silo);
const silos = r.areas.filter((a) => a.silo).map((a) => a.area);
confere("só o silo plantado é chamado de silo (E-I bem abaixo do acaso)", silos.length === 1 && silos[0] === gab.silo,
  r.areas.map((a) => a.area + " " + a.ei.toFixed(2) + " vs " + a.ei_esperado.toFixed(2) + " (" + Math.round(a.externo_vs_acaso * 100) + "%)").join("; "));
confere("toda área é mais fechada que o acaso, mas as outras ficam acima do limiar de silo",
  r.areas.every((a) => a.ei < a.ei_esperado) && r.areas.filter((a) => !a.silo).every((a) => a.externo_vs_acaso > ONA.LIMIAR_SILO));

confere("porteiro plantado: papel de porteiro e responsável por toda entrada de informação no silo",
  pp[gab.porteiro].papel === "porteiro" && silo.porteiro_principal === gab.porteiro && silo.porteiro_participacao > 0.9,
  gab.porteiro + " = " + pp[gab.porteiro].papel + ", " + Math.round(silo.porteiro_participacao * 100) + "% das entradas");
confere("porteiro plantado não é representante (quem é de fora não busca com ele)", pp[gab.porteiro].representante === 0);

const risco = r.riscos[0];
confere("e se sair: a saída do ponto de corte plantado é a mais grave e isola o resto do silo",
  risco.id === gab.ponto_de_corte && risco.perdem_caminho === 15 && risco.areas_afetadas[gab.silo] === 15,
  risco.id + ": " + risco.perdem_caminho + " pessoas sem caminho, eficiência -" + Math.round(risco.queda_eficiencia * 100) + "%");
const sim = ONA.simularSaida(r, [gab.pontes[0]]);
confere("simulação interativa: tirar uma ponte não parte a rede, mas aumenta a distância média",
  sim.perdem_caminho.length === 0 && sim.distancia_media > sim.distancia_media_antes, "distância " + sim.distancia_media_antes.toFixed(2) + " -> " + sim.distancia_media.toFixed(2));

const comBurt = r.por_pessoa.filter((p) => p.restricao !== null && p.conexoes >= 4).sort((a, b) => a.restricao - b.restricao).map((p) => p.id);
confere("Burt: as pontes plantadas têm a menor restrição (cobrem buracos estruturais)", gab.pontes.every((x) => comBurt.indexOf(x) < 3),
  gab.pontes.map((x) => x + " = " + f3(pp[x].restricao) + ", tamanho efetivo " + pp[x].tamanho_efetivo.toFixed(1)).join("; "));

const iso = r.isolados.map((p) => p.id);
confere("os isolados plantados aparecem", gab.isolados.every((x) => iso.includes(x)), "achados: " + iso.join(", "));
const gf = r.gestores.find((x) => x.gestor === gab.gestor_fora_do_fluxo);
confere("gestor fora do fluxo tem a menor ligação com o time", gf.fracao === Math.min(...r.gestores.map((x) => x.fracao)), gf.ligados + " de " + gf.time);
confere("taxa de resposta bate", perto(r.taxa_resposta, 1 - gab.nao_respondentes / gab.pessoas), (r.taxa_resposta * 100).toFixed(1) + "%");

confere("comunidades: modularidade > 0,3 e estáveis entre 20 execuções (Rand ajustado >= 0,8)", r.modularidade > 0.3 && r.estabilidade_comunidades >= 0.8,
  "Q = " + r.modularidade.toFixed(3) + ", " + r.comunidades + " grupos, estabilidade " + r.estabilidade_comunidades.toFixed(3));
{
  const g = I.montar(pessoas, ligacoes);
  confere("nenhuma comunidade desconectada", I.comunidadeConexa(g.adjS, r.por_pessoa.map((p) => p.comunidade)));
  const um = I.modularidade(g.viz, I.separarDesconexas(g.adjS, I.louvain(g.viz, I.mulberry32(1))));
  confere("a melhor de 20 execuções tem modularidade >= a de uma execução isolada", r.modularidade >= um - 1e-12, um.toFixed(3) + " -> " + r.modularidade.toFixed(3));
}

const s = r.sensibilidade;
confere("sensibilidade: pontes e silo se mantêm com mais 10% de não resposta", s.pontes_mantidas >= 0.6 && s.silo_estavel >= 0.8,
  s.replicas + " sorteios; pontes mantidas " + Math.round(s.pontes_mantidas * 100) + "%, silo igual em " + Math.round(s.silo_estavel * 100) + "%, isolados " + s.isolados_min + " a " + s.isolados_max);
confere("com 80% de resposta, o relatório pede cautela e não proíbe conclusões", r.confiabilidade.nivel === "cautela");

// regra de leitura: abaixo de 70%, o relatório avisa que não dá para concluir sobre pontes e isolados
{
  const rnd = I.mulberry32(5), cortar = new Set();
  const resp = pessoas.filter((p) => p.respondeu === "sim").map((p) => p.id);
  while (cortar.size < 20) cortar.add(resp[Math.floor(rnd() * resp.length)]);
  const p2 = pessoas.map((p) => (cortar.has(p.id) ? { ...p, respondeu: "nao" } : p));
  const l2 = ligacoes.filter((l) => !cortar.has(l.origem_id));
  const r2 = ONA.analisar(p2, l2, { sensibilidade: false });
  confere("com menos de 70% de resposta, o primeiro insight é o alerta e some o de pontes",
    r2.taxa_resposta < 0.7 && r2.insights[0].nivel === "alerta" && !r2.insights.some((i) => i.tema === "pontes" || i.tema === "isolados"),
    "taxa " + Math.round(r2.taxa_resposta * 100) + "%: " + r2.insights[0].titulo);
}

const r3 = ONA.analisar(pessoas, ligacoes);
confere("resultado reprodutível (mesma entrada, mesma saída)", JSON.stringify(r3) === JSON.stringify(r));
confere("insights ordenados por prioridade e o risco de dependência vem antes das informações",
  r.insights.every((x, i) => i === 0 || r.insights[i - 1].prioridade <= x.prioridade) &&
  r.insights.findIndex((x) => x.tema === "dependencia") < r.insights.findIndex((x) => x.tema === "comunidades"));
confere("cálculo completo em menos de 3 s", ms < 3000, ms + " ms");

console.log("\nInsights gerados:");
r.insights.forEach((i) => console.log("- [" + i.nivel + "] " + i.titulo));
fs.writeFileSync(path.join(base, "resultado-exemplo.json"), JSON.stringify({ ...r, por_pessoa: undefined }, null, 2) + "\n");
console.log("\n" + (total - falhas) + " de " + total + " testes passaram.");
process.exit(falhas ? 1 : 0);
