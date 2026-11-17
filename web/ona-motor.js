/* ona-motor.js — motor de métricas da ONA de bolso.
 * Roda no navegador (window.ONA) e no Node (module.exports), sem dependências.
 * Entrada: pessoas [{id, area, cargo, gestor_id, unidade, respondeu}] e
 *          ligacoes [{origem_id, destino_id, tipo, peso}].
 * Nada sai do computador de quem usa: tudo é calculado em memória.
 */
(function (raiz) {
  "use strict";

  var GRUPO_MINIMO = 5; // menos que isso, resultado por área não aparece (anonimato)

  // ---------- CSV ----------
  function lerCSV(texto) {
    texto = texto.replace(/^\uFEFF/, "");
    var linhas = [], campo = "", linha = [], aspas = false, i, c;
    var sep = (texto.split(/\r?\n/)[0].match(/;/g) || []).length > (texto.split(/\r?\n/)[0].match(/,/g) || []).length ? ";" : ",";
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
    if (!linhas.length) return [];
    var cab = linhas[0].map(function (h) { return h.trim().toLowerCase(); });
    return linhas.slice(1).map(function (l) {
      var o = {};
      cab.forEach(function (h, j) { o[h] = (l[j] || "").trim(); });
      return o;
    });
  }

  // ---------- validação ----------
  function validar(pessoas, ligacoes) {
    var erros = [], avisos = [];
    if (!pessoas.length) erros.push("A tabela de pessoas está vazia.");
    if (pessoas.length && !("id" in pessoas[0])) erros.push("A tabela de pessoas precisa da coluna id.");
    if (pessoas.length && !("area" in pessoas[0])) erros.push("A tabela de pessoas precisa da coluna area.");
    if (ligacoes.length && !("origem_id" in ligacoes[0] && "destino_id" in ligacoes[0]))
      erros.push("A tabela de ligações precisa das colunas origem_id e destino_id.");
    var ids = {};
    pessoas.forEach(function (p) { ids[p.id] = true; });
    var fora = 0;
    ligacoes.forEach(function (l) { if (!ids[l.origem_id] || !ids[l.destino_id]) fora++; });
    if (fora) avisos.push(fora + " ligações citam ids que não estão na tabela de pessoas e foram ignoradas.");
    return { erros: erros, avisos: avisos };
  }

  // ---------- grafo ----------
  function montar(pessoas, ligacoes, tipo) {
    var idx = {}, nos = pessoas.map(function (p, i) { idx[p.id] = i; return p; });
    var n = nos.length, saida = [], entrada = [], viz = [], arestas = {}, i;
    for (i = 0; i < n; i++) { saida.push({}); entrada.push({}); viz.push({}); }
    ligacoes.forEach(function (l) {
      if (tipo && tipo !== "todos" && l.tipo !== tipo) return;
      var o = idx[l.origem_id], d = idx[l.destino_id];
      if (o === undefined || d === undefined || o === d) return;
      var w = parseFloat(l.peso) || 1;
      saida[o][d] = (saida[o][d] || 0) + w;
      entrada[d][o] = (entrada[d][o] || 0) + w;
      viz[o][d] = (viz[o][d] || 0) + w;
      viz[d][o] = (viz[d][o] || 0) + w;
      arestas[o + ">" + d] = true;
    });
    return { nos: nos, idx: idx, n: n, saida: saida, entrada: entrada, viz: viz, arestas: arestas };
  }

  // Intermediação (Brandes), dirigida, sem peso, normalizada para 0..1
  function intermediacao(g) {
    var n = g.n, cb = new Array(n).fill(0), s, adj = g.saida.map(function (o) { return Object.keys(o).map(Number); });
    for (s = 0; s < n; s++) {
      var pilha = [], pred = [], sigma = new Array(n).fill(0), dist = new Array(n).fill(-1), fila = [s], k;
      for (k = 0; k < n; k++) pred.push([]);
      sigma[s] = 1; dist[s] = 0;
      while (fila.length) {
        var v = fila.shift(); pilha.push(v);
        adj[v].forEach(function (w) {
          if (dist[w] < 0) { dist[w] = dist[v] + 1; fila.push(w); }
          if (dist[w] === dist[v] + 1) { sigma[w] += sigma[v]; pred[w].push(v); }
        });
      }
      var delta = new Array(n).fill(0);
      while (pilha.length) {
        var w = pilha.pop();
        pred[w].forEach(function (v) { delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w]); });
        if (w !== s) cb[w] += delta[w];
      }
    }
    var norm = n > 2 ? (n - 1) * (n - 2) : 1;
    return cb.map(function (x) { return x / norm; });
  }

  // Louvain (não dirigido, ponderado), com agregação em níveis
  function louvain(g, semente) {
    var rnd = aleatorio(semente || 7);
    var adj = g.viz.map(function (o) { var c = {}; for (var k in o) c[k] = o[k]; return c; });
    var membro = []; for (var i = 0; i < g.n; i++) membro.push(i);
    var mudou = true, nivel = 0;
    while (mudou && nivel < 10) {
      nivel++;
      var r = umNivel(adj, rnd);
      mudou = r.melhorou;
      membro = membro.map(function (c) { return r.com[c]; });
      adj = agregar(adj, r.com);
    }
    // renumera por tamanho
    var cont = {}; membro.forEach(function (c) { cont[c] = (cont[c] || 0) + 1; });
    var ordem = Object.keys(cont).sort(function (a, b) { return cont[b] - cont[a]; });
    var novo = {}; ordem.forEach(function (c, j) { novo[c] = j; });
    membro = membro.map(function (c) { return novo[c]; });
    return { comunidade: membro, modularidade: modularidade(g.viz, membro) };
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
    while (passou && voltas < 50) {
      passou = false; voltas++;
      embaralhar(ordem, rnd);
      ordem.forEach(function (v) {
        var cv = com[v], pesos = {};
        for (var u in adj[v]) { if (+u === v) continue; var cu = com[u]; pesos[cu] = (pesos[cu] || 0) + adj[v][u]; }
        tot[cv] -= k[v];
        var melhor = cv, ganho = (pesos[cv] || 0) - tot[cv] * k[v] / m2;
        for (var c in pesos) {
          var gnh = pesos[c] - tot[c] * k[v] / m2;
          if (gnh > ganho + 1e-12) { ganho = gnh; melhor = +c; }
        }
        tot[melhor] += k[v];
        if (melhor !== cv) { com[v] = melhor; passou = true; melhorou = true; }
      });
    }
    var mapa = {}, prox = 0;
    com = com.map(function (c) { if (!(c in mapa)) mapa[c] = prox++; return mapa[c]; });
    return { com: com, melhorou: melhorou };
  }

  function agregar(adj, com) {
    var nc = Math.max.apply(null, com) + 1, novo = [], i;
    for (i = 0; i < nc; i++) novo.push({});
    adj.forEach(function (o, v) {
      for (var u in o) { var a = com[v], b = com[u]; novo[a][b] = (novo[a][b] || 0) + o[u]; }
    });
    return novo;
  }

  function modularidade(adj, com) {
    var m2 = 0, k = [], q = 0;
    adj.forEach(function (o, i) { var s = 0; for (var j in o) s += o[j]; k[i] = s; m2 += s; });
    if (!m2) return 0;
    var totc = {}, inc = {};
    adj.forEach(function (o, i) {
      totc[com[i]] = (totc[com[i]] || 0) + k[i];
      for (var j in o) if (com[j] === com[i]) inc[com[i]] = (inc[com[i]] || 0) + o[j];
    });
    for (var c in totc) q += (inc[c] || 0) / m2 - Math.pow(totc[c] / m2, 2);
    return q;
  }

  function aleatorio(s) { return function () { s = (s * 1103515245 + 12345) % 2147483648; return s / 2147483648; }; }
  function embaralhar(a, rnd) { for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(rnd() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t; } }

  // ---------- análise completa ----------
  function analisar(pessoas, ligacoes, opcoes) {
    opcoes = opcoes || {};
    var g = montar(pessoas, ligacoes, opcoes.tipo);
    var n = g.n, i;
    var grauEnt = g.entrada.map(function (o) { return Object.keys(o).length; });
    var grauSai = g.saida.map(function (o) { return Object.keys(o).length; });
    var grauTot = g.viz.map(function (o) { return Object.keys(o).length; });
    var btw = intermediacao(g);
    var lv = louvain(g, opcoes.semente);
    var respondeu = pessoas.map(function (p) { return !p.respondeu || !/^(nao|não|n|0|false)$/i.test(p.respondeu); });
    var nResp = respondeu.filter(Boolean).length;

    // reciprocidade: pares com ligação nos dois sentidos / pares ligados
    var pares = 0, mutuos = 0;
    for (var a in g.arestas) {
      var p = a.split(">"), o = +p[0], d = +p[1];
      if (g.arestas[d + ">" + o]) { if (o < d) { mutuos++; pares++; } }
      else pares++;
    }

    // concentração: % das citações recebidas pelas 5% mais citadas
    var totalCit = grauEnt.reduce(function (s, x) { return s + x; }, 0);
    var topN = Math.max(1, Math.round(n * 0.05));
    var topCit = grauEnt.slice().sort(function (x, y) { return y - x; }).slice(0, topN).reduce(function (s, x) { return s + x; }, 0);

    // isolados: ninguém cita e cita no máximo uma pessoa (só entre quem respondeu faz sentido olhar a saída)
    var isolados = [], quaseIsolados = [];
    for (i = 0; i < n; i++) {
      if (grauEnt[i] === 0 && grauTot[i] <= 1) isolados.push(i);
      else if (grauTot[i] <= 2) quaseIsolados.push(i);
    }

    // por área
    var areas = {};
    pessoas.forEach(function (p, j) {
      var ar = p.area || "(sem área)";
      if (!areas[ar]) areas[ar] = { area: ar, pessoas: 0, responderam: 0, interno: 0, externo: 0, comunidades: {} };
      areas[ar].pessoas++; if (respondeu[j]) areas[ar].responderam++;
      areas[ar].comunidades[lv.comunidade[j]] = (areas[ar].comunidades[lv.comunidade[j]] || 0) + 1;
    });
    for (var ar2 in g.arestas) {
      var q = ar2.split(">"), ao = pessoas[+q[0]].area || "(sem área)", ad = pessoas[+q[1]].area || "(sem área)";
      if (ao === ad) areas[ao].interno++; else { areas[ao].externo++; areas[ad].externo++; }
    }
    var listaAreas = Object.keys(areas).map(function (k) {
      var x = areas[k], tot = x.interno + x.externo;
      x.ei = tot ? (x.externo - x.interno) / tot : null; // -1 = só para dentro; +1 = só para fora
      x.oculta = x.pessoas < GRUPO_MINIMO;
      var maior = 0; for (var c in x.comunidades) maior = Math.max(maior, x.comunidades[c]);
      x.coesao = x.pessoas ? maior / x.pessoas : 0; // fração da área na mesma comunidade real
      return x;
    });

    // gestor × time
    var gestores = {};
    pessoas.forEach(function (p, j) { if (p.gestor_id && g.idx[p.gestor_id] !== undefined) (gestores[p.gestor_id] = gestores[p.gestor_id] || []).push(j); });
    var listaGestores = Object.keys(gestores).map(function (gid) {
      var gi = g.idx[gid], time = gestores[gid];
      var ligados = time.filter(function (t) { return g.viz[gi][t]; }).length;
      return { gestor: gid, area: pessoas[gi].area, time: time.length, ligados: ligados, fracao: ligados / time.length };
    });

    var porPessoa = pessoas.map(function (p, j) {
      return { id: p.id, area: p.area, cargo: p.cargo, respondeu: respondeu[j], citacoes_recebidas: grauEnt[j],
               citacoes_feitas: grauSai[j], conexoes: grauTot[j], intermediacao: btw[j], comunidade: lv.comunidade[j] };
    });
    var pontes = porPessoa.slice().sort(function (x, y) { return y.intermediacao - x.intermediacao; }).slice(0, 5)
      .filter(function (x) { return x.intermediacao > 0; });

    var r = {
      pessoas: n, ligacoes: Object.keys(g.arestas).length, tipo: opcoes.tipo || "todos",
      taxa_resposta: n ? nResp / n : 0,
      densidade: n > 1 ? Object.keys(g.arestas).length / (n * (n - 1)) : 0,
      reciprocidade: pares ? mutuos / pares : 0,
      concentracao_top5pct: totalCit ? topCit / totalCit : 0,
      comunidades: Math.max.apply(null, lv.comunidade.concat([-1])) + 1,
      modularidade: lv.modularidade,
      isolados: isolados.map(function (j) { return porPessoa[j]; }),
      quase_isolados: quaseIsolados.map(function (j) { return porPessoa[j]; }),
      pontes: pontes, areas: listaAreas, gestores: listaGestores, por_pessoa: porPessoa
    };
    r.insights = insights(r);
    return r;
  }

  function pct(x) { return (x * 100).toFixed(0).replace(".", ",") + "%"; }

  function insights(r) {
    var out = [];
    var nr = Math.round((1 - r.taxa_resposta) * r.pessoas);
    if (r.taxa_resposta < 0.999)
      out.push({ nivel: r.taxa_resposta < 0.7 ? "alerta" : "aviso", titulo: "Taxa de resposta de " + pct(r.taxa_resposta),
        texto: nr + " pessoas não responderam. Elas ainda aparecem quando são citadas, mas as ligações que fariam não existem na base, então podem parecer menos conectadas do que são. Leia isolados e pontes com isso em mente." });
    if (r.pontes.length) {
      var areasP = r.pontes.slice(0, 3).map(function (p) { return p.area; });
      out.push({ nivel: "insight", titulo: "A rede depende de poucas pontes",
        texto: "As " + Math.min(3, r.pontes.length) + " pessoas com maior intermediação estão em " + uniq(areasP).join(", ") +
          ". São elas que ligam grupos que, sem elas, quase não conversam. Vale perguntar: se uma delas sair ou mudar de função, quem assume esse papel?" });
    }
    var silos = r.areas.filter(function (a) { return !a.oculta && a.ei !== null && a.ei <= -0.9; });
    silos.forEach(function (a) {
      out.push({ nivel: "insight", titulo: a.area + " fala quase só para dentro",
        texto: "Índice E-I de " + a.ei.toFixed(2).replace(".", ",") + " (vai de -1, só ligações internas, a +1, só externas). " +
          a.externo + " de " + (a.interno + a.externo) + " ligações da área cruzam a fronteira. É o retrato de um silo: confira se isso é escolha (trabalho isolado de propósito) ou gargalo." });
    });
    if (r.isolados.length)
      out.push({ nivel: "insight", titulo: r.isolados.length + " pessoas fora do fluxo",
        texto: "Ninguém as citou e elas citaram no máximo uma pessoa. Antes de qualquer conclusão, confira se são recém-chegadas, se estão afastadas ou se não responderam. Isolamento na rede é um sinal para conversar, não um diagnóstico." });
    r.gestores.filter(function (x) { return x.time >= GRUPO_MINIMO && x.fracao < 0.2; }).forEach(function (x) {
      out.push({ nivel: "insight", titulo: "Gestor de " + x.area + " fora do fluxo do próprio time",
        texto: "Só " + x.ligados + " de " + x.time + " pessoas do time têm ligação direta com o gestor. A informação do time está passando por outro caminho; vale entender qual." });
    });
    out.push({ nivel: "info", titulo: r.comunidades + " grupos reais de conversa",
      texto: "O algoritmo de comunidades (Louvain) achou " + r.comunidades + " grupos, com modularidade de " + r.modularidade.toFixed(2).replace(".", ",") +
        " (acima de 0,3 indica grupos bem separados). Compare com o organograma: área que se divide em vários grupos ou grupos que juntam áreas diferentes dizem muito sobre como o trabalho acontece." });
    out.push({ nivel: "info", titulo: "Reciprocidade de " + pct(r.reciprocidade),
      texto: "De cada 100 pares ligados, " + Math.round(r.reciprocidade * 100) + " se citam nos dois sentidos. Reciprocidade baixa em pedidos de ajuda costuma indicar sobrecarga em quem é muito procurado." });
    out.push({ nivel: "info", titulo: "As 5% mais citadas recebem " + pct(r.concentracao_top5pct) + " das citações",
      texto: "Quanto maior esse número, mais a rede depende de poucas pessoas para funcionar." });
    return out;
  }
  function uniq(a) { return a.filter(function (x, i) { return a.indexOf(x) === i; }); }

  var ONA = { lerCSV: lerCSV, validar: validar, analisar: analisar, GRUPO_MINIMO: GRUPO_MINIMO };
  if (typeof module !== "undefined" && module.exports) module.exports = ONA;
  else raiz.ONA = ONA;
})(this);
