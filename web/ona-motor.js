/* ona-motor.js — motor de métricas da ONA de bolso.
 * https://github.com/gleissonbispo/ona-de-bolso · licença MIT
 *
 * Roda no navegador (window.ONA) e no Node (module.exports), sem dependências.
 * Entrada: pessoas [{id, area, cargo, gestor_id, unidade, respondeu}] e
 *          ligacoes [{origem_id, destino_id, tipo, peso}] (origem cita destino).
 * Nada sai do computador de quem usa: tudo é calculado em memória.
 *
 * Escolhas de método (detalhe em docs/projeto.md):
 *  - Duas redes. A dirigida (quem cita quem) mede citações recebidas e feitas, reciprocidade e os
 *    papéis de corretagem. A simetrizada (há ligação se um dos dois citou o outro) mede intermediação,
 *    comunidades, E-I, restrição de Burt, núcleo e o efeito de uma saída. Ela trata a rede como canal
 *    de informação, que corre nos dois sentidos, e evita que quem não respondeu (sem citações feitas)
 *    fique impedido de aparecer como ponte.
 *  - Gerador pseudoaleatório mulberry32 com semente fixa: o mesmo arquivo dá sempre o mesmo resultado.
 */
(function (raiz) {
  "use strict";

  var GRUPO_MINIMO = 5;       // menos que isso, resultado por área não aparece (anonimato)
  var LIMIAR_RESPOSTA = 0.7;  // abaixo disso, o relatório não conclui sobre pontes e isolados
  var LIMIAR_SILO = 0.25;     // silo: menos de 1/4 das ligações externas esperadas ao acaso...
  var ALFA_SILO = 0.01;       // ...e E-I abaixo do esperado com p < 0,01 nas permutações
  var SEMENTE = 20261116;
  var EXECUCOES_LOUVAIN = 20;
  var PERMUTACOES_EI = 1000;
  var PAPEIS = ["coordenador", "consultor", "representante", "porteiro", "ligacao"];
  var NOME_PAPEL = {
    coordenador: "coordenador", consultor: "consultor", representante: "representante",
    porteiro: "porteiro", ligacao: "ligação"
  };

  // ---------- gerador pseudoaleatório (mulberry32) ----------
  function mulberry32(a) {
    a = a >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function embaralhar(a, rnd) {
    for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(rnd() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }

  // ---------- CSV ----------
  function lerCSV(texto) {
    texto = String(texto || "").replace(/^﻿/, "");
    var primeira = texto.split(/\r?\n/)[0] || "";
    var sep = (primeira.match(/;/g) || []).length > (primeira.match(/,/g) || []).length ? ";" :
      ((primeira.match(/\t/g) || []).length > (primeira.match(/,/g) || []).length ? "\t" : ",");
    var linhas = [], campo = "", linha = [], aspas = false, i, c;
    for (i = 0; i < texto.length; i++) {
      c = texto[i];
      if (aspas) {
        if (c === '"' && texto[i + 1] === '"') { campo += '"'; i++; }
        else if (c === '"') aspas = false;
        else campo += c;
      } else if (c === '"') aspas = true;
      else if (c === sep) { linha.push(campo); campo = ""; }
      else if (c === "\n" || c === "\r") {
        if (c === "\r" && texto[i + 1] === "\n") i++;
        linha.push(campo); campo = "";
        if (linha.some(function (x) { return x.trim() !== ""; })) linhas.push(linha);
        linha = [];
      } else campo += c;
    }
    linha.push(campo);
    if (linha.some(function (x) { return x.trim() !== ""; })) linhas.push(linha);
    return deLinhas(linhas);
  }
  // Converte uma matriz (primeira linha = cabeçalho) em objetos; usado pelo CSV e pelo XLSX.
  function deLinhas(linhas) {
    if (!linhas.length) return [];
    var cab = linhas[0].map(function (h) { return normalizarCabecalho(h); });
    return linhas.slice(1).map(function (l) {
      var o = {};
      cab.forEach(function (h, j) { o[h] = String(l[j] === undefined || l[j] === null ? "" : l[j]).trim(); });
      return o;
    }).filter(function (o) { return Object.keys(o).some(function (k) { return o[k] !== ""; }); });
  }
  function normalizarCabecalho(h) {
    return String(h || "").trim().toLowerCase()
      .normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/\s+/g, "_");
  }

  // ---------- validação ----------
  function validar(pessoas, ligacoes) {
    var erros = [], avisos = [];
    if (!pessoas.length) erros.push("A tabela de pessoas está vazia.");
    if (pessoas.length && !("id" in pessoas[0])) erros.push("A tabela de pessoas precisa da coluna id.");
    if (pessoas.length && !("area" in pessoas[0])) erros.push("A tabela de pessoas precisa da coluna area.");
    if (!ligacoes.length) erros.push("A tabela de ligações está vazia.");
    if (ligacoes.length && !("origem_id" in ligacoes[0] && "destino_id" in ligacoes[0]))
      erros.push("A tabela de ligações precisa das colunas origem_id e destino_id.");
    if (erros.length) return { erros: erros, avisos: avisos };
    var ids = {}, dup = 0;
    pessoas.forEach(function (p) { if (ids[p.id]) dup++; ids[p.id] = true; });
    if (dup) avisos.push(dup + " ids repetidos na tabela de pessoas; valeu a primeira linha de cada um.");
    var fora = 0, auto = 0;
    ligacoes.forEach(function (l) {
      if (!ids[l.origem_id] || !ids[l.destino_id]) fora++;
      else if (l.origem_id === l.destino_id) auto++;
    });
    if (fora) avisos.push(fora + " ligações citam ids que não estão na tabela de pessoas e foram ignoradas.");
    if (auto) avisos.push(auto + " ligações de uma pessoa com ela mesma foram ignoradas.");
    if (!("respondeu" in pessoas[0])) avisos.push("Sem a coluna respondeu, a página considera que todo mundo respondeu.");
    return { erros: erros, avisos: avisos };
  }

  // ---------- grafo ----------
  function montar(pessoas, ligacoes, tipo) {
    var idx = {}, nos = [];
    pessoas.forEach(function (p) { if (idx[p.id] === undefined) { idx[p.id] = nos.length; nos.push(p); } });
    var n = nos.length, saida = [], entrada = [], viz = [], i;
    for (i = 0; i < n; i++) { saida.push({}); entrada.push({}); viz.push({}); }
    ligacoes.forEach(function (l) {
      if (tipo && tipo !== "todos" && l.tipo !== tipo) return;
      var o = idx[l.origem_id], d = idx[l.destino_id];
      if (o === undefined || d === undefined || o === d) return;
      var w = parseFloat(String(l.peso || "").replace(",", ".")); if (!(w > 0)) w = 1;
      saida[o][d] = (saida[o][d] || 0) + w;
      entrada[d][o] = (entrada[d][o] || 0) + w;
      viz[o][d] = (viz[o][d] || 0) + w;
      viz[d][o] = (viz[d][o] || 0) + w;
    });
    var lista = function (o) { return Object.keys(o).map(Number).sort(function (a, b) { return a - b; }); };
    return {
      nos: nos, idx: idx, n: n, saida: saida, entrada: entrada, viz: viz,
      adjS: viz.map(lista), adjOut: saida.map(lista), adjIn: entrada.map(lista)
    };
  }
  function grafoDeArestas(n, arestas) { // para testes: arestas não dirigidas [[a,b],...]
    var viz = [], i; for (i = 0; i < n; i++) viz.push({});
    arestas.forEach(function (e) { viz[e[0]][e[1]] = (viz[e[0]][e[1]] || 0) + (e[2] || 1); viz[e[1]][e[0]] = viz[e[0]][e[1]]; });
    return { n: n, viz: viz, adjS: viz.map(function (o) { return Object.keys(o).map(Number).sort(function (a, b) { return a - b; }); }) };
  }

  // ---------- intermediação (Brandes 2001), sem peso, normalizada para 0..1 ----------
  // adj: listas de vizinhos (dirigidas ou simétricas). Para a rede simétrica, Brandes conta cada par
  // nos dois sentidos; dividir por (n-1)(n-2) dá a normalização não dirigida padrão.
  function intermediacao(adj, n, ignorar) {
    var cb = new Float64Array(n), s, k;
    var sigma = new Float64Array(n), dist = new Int32Array(n), delta = new Float64Array(n);
    var fila = new Int32Array(n), pilha = new Int32Array(n), pred = [];
    for (k = 0; k < n; k++) pred.push([]);
    for (s = 0; s < n; s++) {
      if (ignorar && ignorar[s]) continue;
      for (k = 0; k < n; k++) { sigma[k] = 0; dist[k] = -1; delta[k] = 0; pred[k].length = 0; }
      sigma[s] = 1; dist[s] = 0;
      var ini = 0, fim = 0, topo = 0; fila[fim++] = s;
      while (ini < fim) {
        var v = fila[ini++]; pilha[topo++] = v;
        var viz = adj[v];
        for (var t = 0; t < viz.length; t++) {
          var w = viz[t];
          if (ignorar && ignorar[w]) continue;
          if (dist[w] < 0) { dist[w] = dist[v] + 1; fila[fim++] = w; }
          if (dist[w] === dist[v] + 1) { sigma[w] += sigma[v]; pred[w].push(v); }
        }
      }
      while (topo > 0) {
        var x = pilha[--topo], pr = pred[x];
        for (var q = 0; q < pr.length; q++) delta[pr[q]] += (sigma[pr[q]] / sigma[x]) * (1 + delta[x]);
        if (x !== s) cb[x] += delta[x];
      }
    }
    var norm = n > 2 ? (n - 1) * (n - 2) : 1, out = [];
    for (k = 0; k < n; k++) out.push(cb[k] / norm);
    return out;
  }

  // ---------- comunidades: Louvain (Blondel et al. 2008) ----------
  function louvain(viz, rnd) {
    var adj = viz.map(function (o) { var c = {}; for (var k in o) c[k] = o[k]; return c; });
    var membro = []; for (var i = 0; i < viz.length; i++) membro.push(i);
    var nivel = 0;
    while (nivel < 20) {
      nivel++;
      var r = umNivel(adj, rnd);
      membro = membro.map(function (c) { return r.com[c]; });
      if (!r.melhorou) break;
      adj = agregar(adj, r.com);
    }
    return membro;
  }
  function umNivel(adj, rnd) {
    var n = adj.length, com = [], k = [], tot = [], m2 = 0, i;
    for (i = 0; i < n; i++) {
      com.push(i);
      var s = 0; for (var j in adj[i]) s += adj[i][j];
      k.push(s); tot.push(s); m2 += s;
    }
    if (m2 === 0) return { com: com, melhorou: false };
    var ordem = []; for (i = 0; i < n; i++) ordem.push(i);
    var melhorou = false, passou = true, voltas = 0;
    while (passou && voltas < 100) {
      passou = false; voltas++;
      embaralhar(ordem, rnd);
      for (var oi = 0; oi < n; oi++) {
        var v = ordem[oi], cv = com[v], pesos = {};
        for (var u in adj[v]) { if (+u === v) continue; var cu = com[u]; pesos[cu] = (pesos[cu] || 0) + adj[v][u]; }
        tot[cv] -= k[v];
        var melhor = cv, ganho = (pesos[cv] || 0) - tot[cv] * k[v] / m2;
        for (var c in pesos) {
          var gnh = pesos[c] - tot[c] * k[v] / m2;
          if (gnh > ganho + 1e-12) { ganho = gnh; melhor = +c; }
        }
        tot[melhor] += k[v];
        if (melhor !== cv) { com[v] = melhor; passou = true; melhorou = true; }
      }
    }
    var mapa = {}, prox = 0;
    com = com.map(function (c) { if (!(c in mapa)) mapa[c] = prox++; return mapa[c]; });
    return { com: com, melhorou: melhorou };
  }
  function agregar(adj, com) {
    var nc = 0, novo = [], i;
    com.forEach(function (c) { if (c + 1 > nc) nc = c + 1; });
    for (i = 0; i < nc; i++) novo.push({});
    adj.forEach(function (o, v) {
      for (var u in o) { var a = com[v], b = com[u]; novo[a][b] = (novo[a][b] || 0) + o[u]; }
    });
    return novo;
  }
  function modularidade(viz, com) {
    var m2 = 0, k = [], q = 0;
    viz.forEach(function (o, i) { var s = 0; for (var j in o) s += o[j]; k[i] = s; m2 += s; });
    if (!m2) return 0;
    var totc = {}, inc = {};
    viz.forEach(function (o, i) {
      totc[com[i]] = (totc[com[i]] || 0) + k[i];
      for (var j in o) if (com[j] === com[i]) inc[com[i]] = (inc[com[i]] || 0) + o[j];
    });
    for (var c in totc) q += (inc[c] || 0) / m2 - Math.pow(totc[c] / m2, 2);
    return q;
  }
  // Refinamento: o Louvain pode deixar uma comunidade internamente desconectada (Traag et al. 2019).
  // Aqui cada comunidade é quebrada nos seus componentes conectados. Isso nunca reduz a modularidade:
  // entre dois pedaços sem ligação, separar só retira o termo negativo de grau esperado.
  function separarDesconexas(adjS, com) {
    var n = com.length, novo = new Array(n).fill(-1), prox = 0;
    for (var s = 0; s < n; s++) {
      if (novo[s] >= 0) continue;
      novo[s] = prox; var fila = [s];
      for (var h = 0; h < fila.length; h++) {
        var v = fila[h];
        adjS[v].forEach(function (w) { if (novo[w] < 0 && com[w] === com[s]) { novo[w] = prox; fila.push(w); } });
      }
      prox++;
    }
    return renumerar(novo);
  }
  function renumerar(com) { // por tamanho (maior = 0); empate pelo menor índice
    var cont = {}, prim = {};
    com.forEach(function (c, i) { cont[c] = (cont[c] || 0) + 1; if (!(c in prim)) prim[c] = i; });
    var ordem = Object.keys(cont).sort(function (a, b) { return cont[b] - cont[a] || prim[a] - prim[b]; });
    var mapa = {}; ordem.forEach(function (c, j) { mapa[c] = j; });
    return com.map(function (c) { return mapa[c]; });
  }
  function comunidadeConexa(adjS, com) { return contarGrupos(separarDesconexas(adjS, com)) === contarGrupos(com); }
  function contarGrupos(com) { var s = {}; com.forEach(function (c) { s[c] = 1; }); return Object.keys(s).length; }

  // Índice de Rand ajustado (Hubert e Arabie 1985): 1 = partições idênticas, 0 = concordância do acaso.
  function randAjustado(a, b) {
    var n = a.length, tab = {}, la = {}, lb = {}, i, c2 = function (x) { return x * (x - 1) / 2; };
    for (i = 0; i < n; i++) {
      var k = a[i] + "|" + b[i];
      tab[k] = (tab[k] || 0) + 1; la[a[i]] = (la[a[i]] || 0) + 1; lb[b[i]] = (lb[b[i]] || 0) + 1;
    }
    var sij = 0, sa = 0, sb = 0;
    for (k in tab) sij += c2(tab[k]);
    for (k in la) sa += c2(la[k]);
    for (k in lb) sb += c2(lb[k]);
    var esperado = sa * sb / c2(n), maximo = (sa + sb) / 2;
    if (maximo === esperado) return 1;
    return (sij - esperado) / (maximo - esperado);
  }

  // Várias execuções com sementes diferentes; fica a de maior modularidade (depois do refinamento).
  // Estabilidade = Rand ajustado médio entre a partição escolhida e as demais execuções.
  function comunidadesEstaveis(g, semente, execucoes) {
    var runs = [], melhor = -1, i;
    for (i = 0; i < execucoes; i++) {
      var bruto = louvain(g.viz, mulberry32(semente + 7919 * i));
      var antes = contarGrupos(bruto);
      var com = separarDesconexas(g.adjS, bruto);
      runs.push({ com: com, q: modularidade(g.viz, com), separadas: contarGrupos(com) - antes });
      if (melhor < 0 || runs[i].q > runs[melhor].q + 1e-12) melhor = i;
    }
    var soma = 0, cont = 0;
    for (i = 0; i < runs.length; i++) if (i !== melhor) { soma += randAjustado(runs[melhor].com, runs[i].com); cont++; }
    var qs = runs.map(function (r) { return r.q; });
    return {
      comunidade: runs[melhor].com, modularidade: runs[melhor].q,
      estabilidade: cont ? soma / cont : 1, execucoes: execucoes,
      modularidade_min: Math.min.apply(null, qs), modularidade_max: Math.max.apply(null, qs),
      pedacos_separados: runs.reduce(function (s, r) { return s + r.separadas; }, 0)
    };
  }

  // ---------- índice E-I (Krackhardt e Stern 1988) com linha de base por permutação ----------
  // Ligações = pares da rede simetrizada. Linha de base: embaralhar as áreas entre as pessoas
  // (mantendo o tamanho de cada área e a rede intacta) e recalcular o E-I.
  function eiContagem(adjS, grupo, ng) {
    var int = new Float64Array(ng), ext = new Float64Array(ng);
    for (var i = 0; i < adjS.length; i++) {
      var a = adjS[i];
      for (var t = 0; t < a.length; t++) {
        var j = a[t]; if (j <= i) continue;
        if (grupo[i] === grupo[j]) int[grupo[i]]++;
        else { ext[grupo[i]]++; ext[grupo[j]]++; }
      }
    }
    return { int: int, ext: ext };
  }
  function eiComBase(adjS, grupo, ng, permutacoes, semente) {
    var obs = eiContagem(adjS, grupo, ng), rnd = mulberry32(semente), g, p;
    var ei = function (c, k) { var tot = c.int[k] + c.ext[k]; return tot ? (c.ext[k] - c.int[k]) / tot : null; };
    var somaEI = new Float64Array(ng), somaExt = new Float64Array(ng), cont = new Float64Array(ng), menores = new Float64Array(ng);
    var perm = grupo.slice();
    for (p = 0; p < permutacoes; p++) {
      embaralhar(perm, rnd);
      var c = eiContagem(adjS, perm, ng);
      for (g = 0; g < ng; g++) {
        var tot = c.int[g] + c.ext[g]; if (!tot) continue;
        var e = (c.ext[g] - c.int[g]) / tot, eo = ei(obs, g);
        somaEI[g] += e; somaExt[g] += c.ext[g] / tot; cont[g]++;
        if (eo !== null && e <= eo + 1e-12) menores[g]++;
      }
    }
    var out = [];
    for (g = 0; g < ng; g++) {
      var o = ei(obs, g), totO = obs.int[g] + obs.ext[g];
      var esp = cont[g] ? somaEI[g] / cont[g] : null, espExt = cont[g] ? somaExt[g] / cont[g] : null;
      out.push({
        interno: obs.int[g], externo: obs.ext[g], ei: o, ei_esperado: esp,
        p_valor: cont[g] ? (menores[g] + 1) / (cont[g] + 1) : null,
        // fração das ligações externas que a área teria se as ligações ignorassem a área
        externo_vs_acaso: totO && espExt ? (obs.ext[g] / totO) / espExt : null
      });
    }
    return out;
  }
  // Fórmula fechada (todas as ligações igualmente prováveis entre quaisquer dois): referência dos testes.
  function eiEsperadoFormula(tamanho, total) {
    var int = tamanho * (tamanho - 1) / 2, ext = tamanho * (total - tamanho);
    return (ext - int) / (ext + int);
  }

  // ---------- papéis de corretagem (Gould e Fernandez 1989) ----------
  // Fluxo de informação: quem é citado passa informação a quem cita (cita = "busco com").
  // Para cada pessoa B e cada caminho A -> B -> C sem ligação direta A -> C, o papel de B depende das áreas:
  //  coordenador: A, B e C na mesma área · consultor: A e C na mesma área, B de fora
  //  representante: A e B na mesma área, C de fora (B leva a informação do grupo para fora)
  //  porteiro: B e C na mesma área, A de fora (B traz informação de fora para dentro)
  //  ligação: as três em áreas diferentes
  function papeisCorretagem(g, grupo) {
    var n = g.n, out = [], b;
    for (b = 0; b < n; b++) {
      var c = { coordenador: 0, consultor: 0, representante: 0, porteiro: 0, ligacao: 0 };
      var fontes = g.adjOut[b], destinos = g.adjIn[b]; // B cita a fonte (A -> B); o destino cita B (B -> C)
      for (var i = 0; i < fontes.length; i++) {
        var a = fontes[i];
        for (var j = 0; j < destinos.length; j++) {
          var d = destinos[j];
          if (a === d || g.saida[d][a]) continue; // C já busca direto com A
          var ga = grupo[a], gb = grupo[b], gc = grupo[d];
          if (ga === gb && gb === gc) c.coordenador++;
          else if (ga === gc) c.consultor++;
          else if (ga === gb) c.representante++;
          else if (gb === gc) c.porteiro++;
          else c.ligacao++;
        }
      }
      out.push(c);
    }
    return out;
  }
  // Papel principal de cada pessoa:
  //  1) quem concentra pelo menos metade das entradas (porteiro) ou das saídas (representante) de
  //     informação da própria área, com 5 caminhos ou mais, recebe esse papel;
  //  2) senão, entre os 20% com mais corretagem entre áreas (mínimo de 5 caminhos), vale o papel entre
  //     áreas mais frequente nos caminhos da pessoa;
  //  3) quem só faz corretagem dentro da área (5 caminhos ou mais) recebe "coordenador".
  function papelPrincipal(contagens, grupo) {
    var fora = ["ligacao", "porteiro", "representante", "consultor"];
    var tot = contagens.map(function (c) { return c.consultor + c.representante + c.porteiro + c.ligacao; });
    var ord = tot.filter(function (x) { return x > 0; }).sort(function (a, b) { return a - b; });
    var corte = Math.max(5, ord.length ? ord[Math.floor(0.8 * (ord.length - 1))] : 0);
    var ent = {}, sai = {};
    contagens.forEach(function (c, i) { ent[grupo[i]] = (ent[grupo[i]] || 0) + c.porteiro; sai[grupo[i]] = (sai[grupo[i]] || 0) + c.representante; });
    return contagens.map(function (c, i) {
      var sp = ent[grupo[i]] ? c.porteiro / ent[grupo[i]] : 0, sr = sai[grupo[i]] ? c.representante / sai[grupo[i]] : 0;
      if (c.porteiro >= 5 && sp >= 0.5 && sp >= sr) return "porteiro";
      if (c.representante >= 5 && sr >= 0.5) return "representante";
      if (tot[i] >= corte) {
        var melhor = fora[0];
        fora.forEach(function (p) { if (c[p] > c[melhor]) melhor = p; });
        return melhor;
      }
      return c.coordenador >= 5 ? "coordenador" : null;
    });
  }

  // ---------- restrição e tamanho efetivo (Burt 1992; 2004) ----------
  // Na rede simetrizada, com peso = soma dos pesos citados nos dois sentidos.
  // Restrição baixa = contatos que não se conhecem entre si (cobre buracos estruturais).
  function burt(viz) {
    var n = viz.length, rest = [], efet = [], i;
    var soma = viz.map(function (o) { var s = 0; for (var k in o) s += o[k]; return s; });
    var maximo = viz.map(function (o) { var m = 0; for (var k in o) m = Math.max(m, o[k]); return m; });
    for (i = 0; i < n; i++) {
      var vs = Object.keys(viz[i]).map(Number);
      if (!vs.length) { rest.push(null); efet.push(0); continue; }
      var p = function (a, b) { return soma[a] ? (viz[a][b] || 0) / soma[a] : 0; };
      var c = 0, ef = 0;
      vs.forEach(function (j) {
        var indireto = 0, redund = 0;
        vs.forEach(function (q) {
          if (q === j || !viz[q][j]) return;
          indireto += p(i, q) * p(q, j);
          redund += p(i, q) * (viz[j][q] / maximo[j]);
        });
        c += Math.pow(p(i, j) + indireto, 2);
        ef += 1 - redund;
      });
      rest.push(c); efet.push(ef);
    }
    return { restricao: rest, tamanho_efetivo: efet };
  }

  // ---------- núcleo (k-core, Seidman 1983) ----------
  function nucleos(adjS) {
    var n = adjS.length, grau = adjS.map(function (a) { return a.length; }), feito = new Array(n).fill(false), core = new Array(n).fill(0);
    var k = 0, restantes = n;
    while (restantes > 0) {
      var achou = true;
      while (achou) {
        achou = false;
        for (var i = 0; i < n; i++) {
          if (feito[i] || grau[i] > k) continue;
          feito[i] = true; core[i] = k; restantes--; achou = true;
          adjS[i].forEach(function (j) { if (!feito[j]) grau[j]--; });
        }
      }
      k++;
    }
    return core;
  }

  // ---------- "e se essa pessoa sair?" ----------
  // Remove as pessoas e mede, na rede simetrizada: componentes, maior componente, quem perde o caminho
  // até a maior parte da rede, eficiência global (Latora e Marchiori 2001) e distância média.
  function estruturaRede(adjS, removidos) {
    var n = adjS.length, comp = new Array(n).fill(-1), tam = [], i;
    for (i = 0; i < n; i++) {
      if (comp[i] >= 0 || (removidos && removidos[i])) continue;
      var id = tam.length, fila = [i]; comp[i] = id;
      for (var h = 0; h < fila.length; h++) adjS[fila[h]].forEach(function (w) {
        if (comp[w] < 0 && !(removidos && removidos[w])) { comp[w] = id; fila.push(w); }
      });
      tam.push(fila.length);
    }
    var maior = 0; tam.forEach(function (t, j) { if (t > tam[maior]) maior = j; });
    var dist = new Int32Array(n), soma = 0, somaD = 0, pares = 0, vivos = 0;
    for (i = 0; i < n; i++) {
      if (removidos && removidos[i]) continue;
      vivos++;
      for (var k = 0; k < n; k++) dist[k] = -1;
      dist[i] = 0; var f = [i];
      for (var q = 0; q < f.length; q++) {
        var v = f[q], a = adjS[v];
        for (var t = 0; t < a.length; t++) {
          var w = a[t]; if (dist[w] >= 0 || (removidos && removidos[w])) continue;
          dist[w] = dist[v] + 1; f.push(w); soma += 1 / dist[w]; somaD += dist[w]; pares++;
        }
      }
    }
    return {
      componente: comp, componentes: tam.filter(function (t) { return t > 1; }).length,
      sozinhos: tam.filter(function (t) { return t === 1; }).length,
      maior_componente: tam.length ? tam[maior] : 0, id_maior: maior,
      eficiencia: vivos > 1 ? soma / (vivos * (vivos - 1)) : 0,
      distancia_media: pares ? somaD / pares : 0
    };
  }
  function efeitoSaida(adjS, base, quem) {
    var n = adjS.length, rem = new Array(n).fill(false);
    quem.forEach(function (i) { rem[i] = true; });
    var depois = estruturaRede(adjS, rem), perdem = [];
    for (var i = 0; i < n; i++) {
      if (rem[i]) continue;
      var antes = base.componente[i] === base.id_maior, agora = depois.componente[i] === depois.id_maior;
      if (antes && !agora) perdem.push(i);
    }
    return {
      perdem_caminho: perdem, componentes: depois.componentes, maior_componente: depois.maior_componente,
      eficiencia: depois.eficiencia,
      queda_eficiencia: base.eficiencia ? (base.eficiencia - depois.eficiencia) / base.eficiencia : 0,
      distancia_media: depois.distancia_media
    };
  }

  // ---------- auxiliares ----------
  function respondeu(p) { return !p.respondeu || !/^(nao|não|n|no|0|false|falso)$/i.test(String(p.respondeu).trim()); }
  function topIndices(v, k, filtro) {
    var ids = []; for (var i = 0; i < v.length; i++) if (!filtro || filtro(i)) ids.push(i);
    return ids.sort(function (a, b) { return v[b] - v[a] || a - b; }).slice(0, k);
  }
  function spearman(a, b) {
    var rank = function (v) {
      var o = v.map(function (x, i) { return [x, i]; }).sort(function (x, y) { return x[0] - y[0]; }), r = new Array(v.length), i = 0;
      while (i < o.length) { var j = i; while (j + 1 < o.length && o[j + 1][0] === o[i][0]) j++; for (var k = i; k <= j; k++) r[o[k][1]] = (i + j) / 2; i = j + 1; }
      return r;
    };
    var ra = rank(a), rb = rank(b), n = a.length, ma = (n - 1) / 2, sxy = 0, sxx = 0, syy = 0;
    for (var i = 0; i < n; i++) { sxy += (ra[i] - ma) * (rb[i] - ma); sxx += Math.pow(ra[i] - ma, 2); syy += Math.pow(rb[i] - ma, 2); }
    return sxx && syy ? sxy / Math.sqrt(sxx * syy) : 1;
  }
  function sobreposicao(a, b) { if (!a.length) return 1; var s = {}; b.forEach(function (x) { s[x] = 1; }); return a.filter(function (x) { return s[x]; }).length / a.length; }

  // ---------- sensibilidade à não resposta ----------
  // (1) dirigida x simetrizada: quanto as pontes mudam quando a citação vale nos dois sentidos.
  // (2) não resposta simulada: em cada réplica, apaga as citações feitas por mais 10% de quem respondeu
  //     e confere se as pontes, os isolados, o E-I das áreas e o silo se mantêm (Borgatti, Carley e
  //     Krackhardt 2006; Kossinets 2006).
  function sensibilidade(pessoas, ligacoes, opcoes, base) {
    var n = base.n, resp = base.resp, rnd = mulberry32(opcoes.semente + 101);
    var replicas = n <= 300 ? 20 : (n <= 1000 ? 10 : 5);
    var idsResp = []; for (var i = 0; i < n; i++) if (resp[i]) idsResp.push(i);
    var cortar = Math.max(1, Math.round(0.1 * idsResp.length));
    var topBase = topIndices(base.btw, 5).filter(function (i) { return base.btw[i] > 0; });
    var mantidas = [], isol = [], varEI = [], silosIguais = 0, qs = [];
    var silosBase = JSON.stringify(base.silos);
    for (var r = 0; r < replicas; r++) {
      var sorteio = embaralhar(idsResp.slice(), rnd).slice(0, cortar), fora = {};
      sorteio.forEach(function (i) { fora[pessoas[i].id] = true; });
      var g2 = montar(pessoas, ligacoes.filter(function (l) { return !fora[l.origem_id]; }), opcoes.tipo);
      var b2 = intermediacao(g2.adjS, n);
      mantidas.push(sobreposicao(topBase, topIndices(b2, 5)));
      var ent2 = g2.adjIn.map(function (a) { return a.length; });
      isol.push(g2.adjS.filter(function (a, j) { return ent2[j] === 0 && a.length <= 1; }).length);
      var ei2 = eiContagem(g2.adjS, base.grupo, base.ng), maxd = 0, silos2 = [];
      for (var gk = 0; gk < base.ng; gk++) {
        var tot = ei2.int[gk] + ei2.ext[gk]; if (!tot || base.ei[gk].ei === null) continue;
        var e = (ei2.ext[gk] - ei2.int[gk]) / tot; maxd = Math.max(maxd, Math.abs(e - base.ei[gk].ei));
        var esp = base.ei[gk].ei_esperado, espExt = esp === null ? null : (esp + 1) / 2;
        if (!base.areaOculta[gk] && espExt && (ei2.ext[gk] / tot) / espExt <= LIMIAR_SILO && e < esp) silos2.push(base.nomesGrupo[gk]);
      }
      varEI.push(maxd);
      if (JSON.stringify(silos2.sort()) === silosBase) silosIguais++;
      qs.push(modularidade(g2.viz, separarDesconexas(g2.adjS, louvain(g2.viz, mulberry32(opcoes.semente + r)))));
    }
    var media = function (v) { return v.reduce(function (s, x) { return s + x; }, 0) / Math.max(1, v.length); };
    var topDir = topIndices(base.btwDir, 5).filter(function (i) { return base.btwDir[i] > 0; });
    var top10 = topIndices(base.btw, 10).filter(function (i) { return base.btw[i] > 0; });
    var top10Dir = topIndices(base.btwDir, 10).filter(function (i) { return base.btwDir[i] > 0; });
    return {
      replicas: replicas, pessoas_retiradas: cortar,
      pontes_mantidas: media(mantidas), pontes_mantidas_min: Math.min.apply(null, mantidas),
      isolados_min: Math.min.apply(null, isol), isolados_max: Math.max.apply(null, isol),
      ei_variacao_media: media(varEI), silo_estavel: silosIguais / replicas,
      modularidade_min: Math.min.apply(null, qs), modularidade_max: Math.max.apply(null, qs),
      dirigida_vs_simetrizada: {
        top5_em_comum: sobreposicao(topBase, topDir),
        correlacao: spearman(base.btw, base.btwDir),
        nao_respondentes_top10_simetrizada: top10.filter(function (i) { return !resp[i]; }).length,
        nao_respondentes_top10_dirigida: top10Dir.filter(function (i) { return !resp[i]; }).length
      }
    };
  }

  // ---------- análise completa ----------
  function analisar(pessoas, ligacoes, opcoes) {
    opcoes = opcoes || {};
    var semente = opcoes.semente === undefined ? SEMENTE : opcoes.semente;
    var o2 = { tipo: opcoes.tipo || "todos", semente: semente };
    var g = montar(pessoas, ligacoes, o2.tipo);
    pessoas = g.nos;
    var n = g.n, i;
    var grauEnt = g.adjIn.map(function (a) { return a.length; });
    var grauSai = g.adjOut.map(function (a) { return a.length; });
    var grauTot = g.adjS.map(function (a) { return a.length; });
    var simetrica = opcoes.rede !== "dirigida";
    var btwSim = intermediacao(g.adjS, n), btwDir = intermediacao(g.adjOut, n);
    var btw = simetrica ? btwSim : btwDir;
    // comunidades sempre na rede não dirigida (o Louvain é definido para ela)
    var cm = comunidadesEstaveis({ viz: g.viz, adjS: g.adjS }, semente, opcoes.execucoes || (n > 1500 ? 10 : EXECUCOES_LOUVAIN));
    var resp = pessoas.map(respondeu);
    var nResp = resp.filter(Boolean).length;

    // reciprocidade: só entre pares em que as duas pessoas responderam (quem não respondeu não teria como retribuir)
    var pares = 0, mutuos = 0;
    for (i = 0; i < n; i++) {
      if (!resp[i]) continue;
      g.adjOut[i].forEach(function (d) {
        if (!resp[d]) return;
        if (g.saida[d][i]) { if (i < d) { mutuos++; pares++; } } else pares++;
      });
    }
    var totalCit = grauEnt.reduce(function (s, x) { return s + x; }, 0);
    var topN = Math.max(1, Math.round(n * 0.05));
    var topCit = grauEnt.slice().sort(function (x, y) { return y - x; }).slice(0, topN).reduce(function (s, x) { return s + x; }, 0);

    // isolados: ninguém cita e há no máximo uma ligação em qualquer sentido
    var isolados = [], quaseIsolados = [];
    for (i = 0; i < n; i++) {
      if (grauEnt[i] === 0 && grauTot[i] <= 1) isolados.push(i);
      else if (grauTot[i] <= 2) quaseIsolados.push(i);
    }

    // áreas
    var nomesGrupo = [], grupoDe = {}, grupo = pessoas.map(function (p) {
      var a = p.area || "(sem área)";
      if (grupoDe[a] === undefined) { grupoDe[a] = nomesGrupo.length; nomesGrupo.push(a); }
      return grupoDe[a];
    });
    var ng = nomesGrupo.length;
    var ei = eiComBase(g.adjS, grupo, ng, opcoes.permutacoes || PERMUTACOES_EI, semente + 1);
    var tamGrupo = new Array(ng).fill(0), respGrupo = new Array(ng).fill(0);
    grupo.forEach(function (gk, j) { tamGrupo[gk]++; if (resp[j]) respGrupo[gk]++; });
    var areaOculta = tamGrupo.map(function (t) { return t < GRUPO_MINIMO; });

    var gf = papeisCorretagem(g, grupo), papel = papelPrincipal(gf, grupo);
    var bt = burt(g.viz), core = nucleos(g.adjS);
    var nucleoMax = Math.max.apply(null, core.concat([0]));

    var listaAreas = nomesGrupo.map(function (nome, gk) {
      var x = ei[gk], com = {};
      grupo.forEach(function (gg, j) { if (gg === gk) com[cm.comunidade[j]] = (com[cm.comunidade[j]] || 0) + 1; });
      var maior = 0; for (var c in com) maior = Math.max(maior, com[c]);
      // quem traz informação de fora para dentro (porteiro) e quem leva para fora (representante)
      var entradas = 0, saidas = 0, topP = -1, topR = -1;
      grupo.forEach(function (gg, j) {
        if (gg !== gk) return;
        entradas += gf[j].porteiro; saidas += gf[j].representante;
        if (topP < 0 || gf[j].porteiro > gf[topP].porteiro) topP = j;
        if (topR < 0 || gf[j].representante > gf[topR].representante) topR = j;
      });
      var silo = !areaOculta[gk] && x.ei !== null && x.p_valor !== null && x.p_valor < ALFA_SILO &&
        x.externo_vs_acaso !== null && x.externo_vs_acaso <= LIMIAR_SILO;
      return {
        area: nome, pessoas: tamGrupo[gk], responderam: respGrupo[gk], taxa_resposta: respGrupo[gk] / tamGrupo[gk],
        interno: x.interno, externo: x.externo, ei: x.ei, ei_esperado: x.ei_esperado, p_valor: x.p_valor,
        externo_vs_acaso: x.externo_vs_acaso, silo: silo, oculta: areaOculta[gk],
        coesao: tamGrupo[gk] ? maior / tamGrupo[gk] : 0,
        entradas_de_fora: entradas, saidas_para_fora: saidas,
        porteiro_principal: entradas && topP >= 0 ? pessoas[topP].id : null,
        porteiro_participacao: entradas && topP >= 0 ? gf[topP].porteiro / entradas : 0,
        representante_principal: saidas && topR >= 0 ? pessoas[topR].id : null,
        representante_participacao: saidas && topR >= 0 ? gf[topR].representante / saidas : 0
      };
    });

    // gestor x time
    var gestores = {};
    pessoas.forEach(function (p, j) { if (p.gestor_id && g.idx[p.gestor_id] !== undefined && g.idx[p.gestor_id] !== j) (gestores[p.gestor_id] = gestores[p.gestor_id] || []).push(j); });
    var listaGestores = Object.keys(gestores).map(function (gid) {
      var gi = g.idx[gid], time = gestores[gid];
      var ligados = time.filter(function (t) { return g.viz[gi][t]; }).length;
      return { gestor: gid, area: pessoas[gi].area, time: time.length, ligados: ligados, fracao: ligados / time.length };
    });

    // e se sair: as 10 maiores intermediações
    var base = estruturaRede(g.adjS);
    var riscos = topIndices(btw, 10).filter(function (j) { return btw[j] > 0; }).map(function (j) {
      var ef = efeitoSaida(g.adjS, base, [j]);
      var areasAfetadas = {};
      ef.perdem_caminho.forEach(function (k) { var a = pessoas[k].area; areasAfetadas[a] = (areasAfetadas[a] || 0) + 1; });
      return {
        id: pessoas[j].id, area: pessoas[j].area, intermediacao: btw[j],
        perdem_caminho: ef.perdem_caminho.length, areas_afetadas: areasAfetadas,
        componentes: ef.componentes, queda_eficiencia: ef.queda_eficiencia, distancia_media: ef.distancia_media
      };
    }).sort(function (a, b) { return b.perdem_caminho - a.perdem_caminho || b.queda_eficiencia - a.queda_eficiencia; });

    var porPessoa = pessoas.map(function (p, j) {
      return {
        id: p.id, area: p.area, cargo: p.cargo || "", respondeu: resp[j],
        citacoes_recebidas: grauEnt[j], citacoes_feitas: grauSai[j], conexoes: grauTot[j],
        intermediacao: btw[j], intermediacao_dirigida: btwDir[j], intermediacao_simetrizada: btwSim[j],
        restricao: bt.restricao[j], tamanho_efetivo: bt.tamanho_efetivo[j], nucleo: core[j],
        comunidade: cm.comunidade[j], papel: papel[j],
        coordenador: gf[j].coordenador, consultor: gf[j].consultor, representante: gf[j].representante,
        porteiro: gf[j].porteiro, ligacao: gf[j].ligacao
      };
    });
    var pontes = topIndices(btw, 5).filter(function (j) { return btw[j] > 0; }).map(function (j) { return porPessoa[j]; });
    var tamCom = {}; cm.comunidade.forEach(function (c) { tamCom[c] = (tamCom[c] || 0) + 1; });

    var r = {
      versao: 2, pessoas: n, ligacoes: g.adjS.reduce(function (s, a) { return s + a.length; }, 0) / 2,
      citacoes: g.adjOut.reduce(function (s, a) { return s + a.length; }, 0),
      tipo: o2.tipo, rede: simetrica ? "simetrizada" : "dirigida", semente: semente,
      taxa_resposta: n ? nResp / n : 0, responderam: nResp,
      densidade: n > 1 ? (g.adjS.reduce(function (s, a) { return s + a.length; }, 0) / 2) / (n * (n - 1) / 2) : 0,
      reciprocidade: pares ? mutuos / pares : 0,
      concentracao_top5pct: totalCit ? topCit / totalCit : 0,
      comunidades: Object.keys(tamCom).filter(function (c) { return tamCom[c] > 1; }).length,
      comunidades_total: Object.keys(tamCom).length,
      modularidade: cm.modularidade, estabilidade_comunidades: cm.estabilidade, execucoes_louvain: cm.execucoes,
      modularidade_faixa: [cm.modularidade_min, cm.modularidade_max], pedacos_separados: cm.pedacos_separados,
      eficiencia: base.eficiencia, distancia_media: base.distancia_media, maior_componente: base.maior_componente,
      componentes: base.componentes, nucleo_max: nucleoMax,
      nucleo_pessoas: core.filter(function (c) { return c === nucleoMax && nucleoMax > 0; }).length,
      isolados: isolados.map(function (j) { return porPessoa[j]; }),
      quase_isolados: quaseIsolados.map(function (j) { return porPessoa[j]; }),
      pontes: pontes, riscos: riscos, areas: listaAreas, gestores: listaGestores, por_pessoa: porPessoa
    };
    if (opcoes.sensibilidade !== false) {
      r.sensibilidade = sensibilidade(pessoas, ligacoes, o2, {
        n: n, resp: resp, btw: btwSim, btwDir: btwDir, grupo: grupo, ng: ng, ei: ei, areaOculta: areaOculta,
        nomesGrupo: nomesGrupo, silos: listaAreas.filter(function (a) { return a.silo; }).map(function (a) { return a.area; }).sort()
      });
    }
    r.confiabilidade = confiabilidade(r);
    r.insights = insights(r);
    Object.defineProperty(r, "_rede", { value: { adjS: g.adjS, base: base, idx: g.idx }, enumerable: false });
    return r;
  }

  // Simulação interativa: efeito de tirar uma ou mais pessoas (ids) da rede já analisada.
  function simularSaida(r, ids) {
    var rede = r._rede, quem = ids.map(function (id) { return rede.idx[id]; }).filter(function (x) { return x !== undefined; });
    var ef = efeitoSaida(rede.adjS, rede.base, quem);
    var areas = {};
    ef.perdem_caminho.forEach(function (k) { var a = r.por_pessoa[k].area; areas[a] = (areas[a] || 0) + 1; });
    return {
      ids: ids, perdem_caminho: ef.perdem_caminho.map(function (k) { return r.por_pessoa[k].id; }), areas_afetadas: areas,
      componentes: ef.componentes, componentes_antes: rede.base.componentes, maior_componente: ef.maior_componente,
      eficiencia: ef.eficiencia, eficiencia_antes: rede.base.eficiencia, queda_eficiencia: ef.queda_eficiencia,
      distancia_media: ef.distancia_media, distancia_media_antes: rede.base.distancia_media
    };
  }

  function confiabilidade(r) {
    var s = r.sensibilidade, motivos = [];
    if (r.taxa_resposta < LIMIAR_RESPOSTA) {
      motivos.push("menos de " + pct(LIMIAR_RESPOSTA) + " das pessoas responderam");
      return { nivel: "insuficiente", motivos: motivos };
    }
    if (r.taxa_resposta < 0.85) motivos.push("a taxa de resposta está entre " + pct(LIMIAR_RESPOSTA) + " e 85%");
    if (s && s.pontes_mantidas < 0.6) motivos.push("as maiores pontes mudam quando a resposta cai mais 10%");
    if (s && s.silo_estavel < 0.8) motivos.push("o diagnóstico de silo muda em parte das simulações");
    return { nivel: motivos.length ? "cautela" : "boa", motivos: motivos };
  }

  // ---------- texto ----------
  function pct(x) { return Math.round(x * 100) + "%"; }
  function num(x, d) { return x.toFixed(d).replace(".", ","); }
  function lista(v) { return v.length <= 1 ? v.join("") : v.slice(0, -1).join(", ") + " e " + v[v.length - 1]; }
  function uniq(a) { return a.filter(function (x, i) { return a.indexOf(x) === i; }); }

  // prioridade: 1 = ler primeiro. nivel: alerta, risco, atencao, info.
  function insights(r) {
    var out = [], s = r.sensibilidade, conf = r.confiabilidade;
    var nr = r.pessoas - r.responderam;
    var podeConcluir = conf.nivel !== "insuficiente";

    if (conf.nivel === "insuficiente")
      out.push({ prioridade: 1, nivel: "alerta", tema: "dados", titulo: "Só " + pct(r.taxa_resposta) + " responderam: não dá para concluir sobre pontes e isolados",
        texto: nr + " pessoas não responderam. Abaixo de " + pct(LIMIAR_RESPOSTA) + ", as ligações que faltam mudam quem parece ponte e quem parece isolado. Os números aparecem para orientar a próxima rodada, mas não sustentam decisão sobre pessoas ou áreas." });
    else if (r.taxa_resposta < 0.999)
      out.push({ prioridade: conf.nivel === "cautela" ? 2 : 9, nivel: conf.nivel === "cautela" ? "atencao" : "info", tema: "dados",
        titulo: "Taxa de resposta de " + pct(r.taxa_resposta) + (conf.nivel === "boa" ? ": resultado estável" : ": leia com cautela"),
        texto: nr + " pessoas não responderam. Elas aparecem quando alguém as cita, e a página conta a ligação nos dois sentidos para não apagá-las." +
          (s ? " Simulando mais 10% de não resposta (" + s.replicas + " sorteios), em média " + pct(s.pontes_mantidas) + " das cinco maiores pontes continuam no topo e o diagnóstico de silo se repete em " + pct(s.silo_estavel) + " dos sorteios." : "") +
          (conf.motivos.length ? " Ponto de atenção: " + lista(conf.motivos) + "." : "") });

    // risco de dependência
    var corte = r.riscos.filter(function (x) { return x.perdem_caminho >= Math.max(3, 0.03 * r.pessoas); });
    if (podeConcluir) corte.slice(0, 2).forEach(function (x, k) {
      var areas = Object.keys(x.areas_afetadas).sort(function (a, b) { return x.areas_afetadas[b] - x.areas_afetadas[a]; });
      out.push({ prioridade: 2 + k * 0.1, nivel: "risco", tema: "dependencia", ids: [x.id],
        titulo: "Uma saída deixaria " + x.perdem_caminho + " pessoas sem caminho até o resto da rede",
        texto: "Sem " + x.id + " (" + x.area + "), " + x.perdem_caminho + " pessoas" + (areas.length ? ", quase todas de " + areas[0] + "," : "") +
          " deixam de ter qualquer caminho de conversa com o restante da organização, e a eficiência da rede cai " + pct(x.queda_eficiencia) +
          ". É um ponto único de falha: o problema é a rede depender de uma pessoa só. Vale criar um segundo canal (rituais entre áreas, par de backup) antes que ele faça falta." });
    });
    if (podeConcluir && !corte.length && r.riscos.length) {
      var top = r.riscos.slice().sort(function (a, b) { return b.queda_eficiencia - a.queda_eficiencia; })[0];
      out.push({ prioridade: 6, nivel: "info", tema: "dependencia", ids: [top.id], titulo: "Nenhuma saída isolada parte a rede",
        texto: "Testamos tirar, uma de cada vez, as " + r.riscos.length + " pessoas com maior intermediação. A maior perda é de " + pct(top.queda_eficiencia) + " na eficiência da rede (sem " + top.id + "). Não há ponto único de falha." });
    }

    // silos (com linha de base)
    var silos = r.areas.filter(function (a) { return a.silo; });
    silos.forEach(function (a) {
      out.push({ prioridade: 3, nivel: "risco", tema: "silo", area: a.area,
        titulo: a.area + " fala quase só para dentro",
        texto: a.externo + " de " + (a.interno + a.externo) + " ligações da área cruzam a fronteira (E-I de " + num(a.ei, 2) + "). Se as conversas ignorassem a área, o esperado seria um E-I de " + num(a.ei_esperado, 2) +
          ": a área tem só " + pct(a.externo_vs_acaso) + " das ligações externas que teria ao acaso. Toda área conversa mais para dentro, e isso é normal; esta está muito abaixo das demais. Confira se é escolha (trabalho que precisa de isolamento) ou gargalo." +
          (a.porteiro_principal && a.porteiro_participacao >= 0.5 ? " E a informação de fora entra quase toda por uma pessoa: " + a.porteiro_principal + " responde por " + pct(a.porteiro_participacao) + " das entradas." : "") });
    });
    var fechadas = r.areas.filter(function (a) { return !a.oculta && !a.silo && a.p_valor !== null && a.p_valor < ALFA_SILO; });
    if (fechadas.length)
      out.push({ prioridade: 8, nivel: "info", tema: "silo", titulo: "As demais áreas conversam para dentro na medida do esperado",
        texto: lista(fechadas.map(function (a) { return a.area; })) + " têm mais ligações internas do que o acaso daria, o que é normal em qualquer empresa (as pessoas trabalham com o próprio time). Elas mantêm entre " +
          pct(Math.min.apply(null, fechadas.map(function (a) { return a.externo_vs_acaso; }))) + " e " + pct(Math.max.apply(null, fechadas.map(function (a) { return a.externo_vs_acaso; }))) + " das ligações externas que teriam ao acaso. Só chamamos de silo a área abaixo de " + pct(LIMIAR_SILO) + "." });

    // porteiros fora dos silos: dependência de uma pessoa para a informação entrar
    r.areas.filter(function (a) { return !a.oculta && !a.silo && a.porteiro_principal && a.porteiro_participacao >= 0.5 && a.entradas_de_fora >= 10; }).forEach(function (a) {
      out.push({ prioridade: 4, nivel: "atencao", tema: "porteiro", area: a.area, ids: [a.porteiro_principal],
        titulo: "Em " + a.area + ", a informação de fora entra por uma pessoa",
        texto: a.porteiro_principal + " aparece em " + pct(a.porteiro_participacao) + " dos caminhos em que algo de outra área chega ao time (papel de porteiro, Gould e Fernandez). Isso filtra ruído, mas também pode virar gargalo. Vale ver se mais gente do time tem contato direto com as áreas parceiras." });
    });

    r.gestores.filter(function (x) { return x.time >= GRUPO_MINIMO && x.fracao < 0.2; }).forEach(function (x) {
      out.push({ prioridade: 4.5, nivel: "atencao", tema: "gestor", ids: [x.gestor],
        titulo: "Gestor de " + x.area + " fora do fluxo do próprio time",
        texto: "Só " + x.ligados + " de " + x.time + " pessoas do time têm ligação direta, em qualquer sentido, com o gestor (" + x.gestor + "). A informação do time está passando por outro caminho; vale entender qual." });
    });

    if (r.pontes.length && podeConcluir) {
      var p3 = r.pontes.slice(0, 3);
      var naoResp = p3.filter(function (p) { return !p.respondeu; });
      out.push({ prioridade: 5, nivel: "atencao", tema: "pontes", ids: p3.map(function (p) { return p.id; }),
        titulo: "As três maiores pontes da rede",
        texto: lista(p3.map(function (p) { return p.id + " (" + p.area + ")"; })) + " têm as maiores intermediações: estão no caminho mais curto entre muitos pares de colegas. " +
          (naoResp.length ? lista(naoResp.map(function (p) { return p.id; })) + " não respondeu ao questionário e aparece como ponte porque os colegas a citam; na rede só com o sentido citado, isso ficaria invisível. " : "") +
          "Pergunta para o gestor: se uma delas sair ou mudar de função, quem assume esse papel?" });
    }

    var baixos = r.por_pessoa.filter(function (p) { return p.restricao !== null && p.conexoes >= 4; });
    if (baixos.length >= 10 && podeConcluir) {
      var orden = baixos.slice().sort(function (a, b) { return a.restricao - b.restricao; }).slice(0, 3);
      out.push({ prioridade: 7, nivel: "info", tema: "burt", ids: orden.map(function (p) { return p.id; }),
        titulo: "Quem cobre buracos estruturais",
        texto: lista(orden.map(function (p) { return p.id; })) + " têm a menor restrição de Burt (" + lista(orden.map(function (p) { return num(p.restricao, 2); })) +
          "): falam com grupos que não se falam entre si. Na pesquisa de Burt (2004), redes assim estão ligadas a ideias mais bem avaliadas. É um retrato de posição na rede, não de desempenho." });
    }

    if (r.isolados.length && podeConcluir) {
      var semResp = r.isolados.filter(function (p) { return !p.respondeu; }).length;
      out.push({ prioridade: 6.5, nivel: "atencao", tema: "isolados", ids: r.isolados.map(function (p) { return p.id; }),
        titulo: r.isolados.length + " pessoas fora do fluxo",
        texto: "Ninguém as citou e elas têm no máximo uma ligação. " + (semResp ? semResp + " delas não respondeu, então pode ser só falta de dado. " : "") +
          "Antes de qualquer conclusão, confira se são recém-chegadas, se estão afastadas ou se trabalham remoto. Isolamento na rede é sinal para conversar, não diagnóstico." });
    }

    out.push({ prioridade: 8.5, nivel: "info", tema: "comunidades",
      titulo: r.comunidades + " grupos reais de conversa",
      texto: "O algoritmo de comunidades (Louvain, " + r.execucoes_louvain + " execuções, fica a melhor) achou " + r.comunidades + " grupos, com modularidade de " + num(r.modularidade, 2) +
        " (acima de 0,3 indica grupos bem separados). A divisão é " + (r.estabilidade_comunidades >= 0.8 ? "estável" : "instável") + ": concordância média de " + num(r.estabilidade_comunidades, 2) +
        " entre as execuções (1 = idênticas). Compare com o organograma: área que se divide em vários grupos ou grupos que juntam áreas diferentes dizem como o trabalho acontece." });
    out.push({ prioridade: 9.5, nivel: "info", tema: "reciprocidade", titulo: "Reciprocidade de " + pct(r.reciprocidade),
      texto: "Entre pares em que as duas pessoas responderam, " + Math.round(r.reciprocidade * 100) + " em cada 100 se citam nos dois sentidos. Reciprocidade baixa em pedidos de ajuda costuma indicar sobrecarga em quem é muito procurado." });
    out.push({ prioridade: 9.6, nivel: "info", tema: "concentracao", titulo: "As 5% mais citadas recebem " + pct(r.concentracao_top5pct) + " das citações",
      texto: "Quanto maior esse número, mais a rede depende de poucas pessoas para funcionar." });
    return out.sort(function (a, b) { return a.prioridade - b.prioridade; });
  }

  var ONA = {
    lerCSV: lerCSV, deLinhas: deLinhas, validar: validar, analisar: analisar, simularSaida: simularSaida,
    GRUPO_MINIMO: GRUPO_MINIMO, LIMIAR_RESPOSTA: LIMIAR_RESPOSTA, LIMIAR_SILO: LIMIAR_SILO, NOME_PAPEL: NOME_PAPEL,
    // expostos para teste e reuso
    _int: {
      mulberry32: mulberry32, montar: montar, grafoDeArestas: grafoDeArestas, intermediacao: intermediacao,
      louvain: louvain, modularidade: modularidade, separarDesconexas: separarDesconexas, comunidadesEstaveis: comunidadesEstaveis,
      comunidadeConexa: comunidadeConexa, randAjustado: randAjustado, eiComBase: eiComBase, eiEsperadoFormula: eiEsperadoFormula,
      papeisCorretagem: papeisCorretagem, burt: burt, nucleos: nucleos, estruturaRede: estruturaRede, efeitoSaida: efeitoSaida, spearman: spearman
    }
  };
  if (typeof module !== "undefined" && module.exports) module.exports = ONA;
  else raiz.ONA = ONA;
})(this);
