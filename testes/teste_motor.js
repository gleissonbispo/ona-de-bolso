// Teste do motor contra o que o gerador plantou (node testes/teste_motor.js)
const fs = require("fs");
const path = require("path");
const ONA = require("../web/ona-motor.js");

const base = path.join(__dirname, "..", "dados", "exemplo");
const pessoas = ONA.lerCSV(fs.readFileSync(path.join(base, "pessoas.csv"), "utf8"));
const ligacoes = ONA.lerCSV(fs.readFileSync(path.join(base, "ligacoes.csv"), "utf8"));
const gab = JSON.parse(fs.readFileSync(path.join(base, "gabarito.json"), "utf8"));

let falhas = 0;
function confere(nome, ok, detalhe) {
  console.log((ok ? "ok    " : "FALHOU") + "  " + nome + (detalhe ? "  (" + detalhe + ")" : ""));
  if (!ok) falhas++;
}

const v = ONA.validar(pessoas, ligacoes);
confere("validação sem erros", v.erros.length === 0, v.erros.join("; "));

const t0 = Date.now();
const r = ONA.analisar(pessoas, ligacoes);
const ms = Date.now() - t0;

confere("pessoas e ligações lidas", r.pessoas === gab.pessoas && r.ligacoes === gab.pares_ligados, r.pessoas + " pessoas, " + r.ligacoes + " pares ligados (" + gab.ligacoes + " citações por tipo)");
const top4 = r.pontes.slice(0, 4).map(p => p.id).sort();
const esperado = gab.pontes.concat(gab.porteiros_do_silo).sort();
confere("pontes plantadas e porteiros do silo são as 4 maiores intermediações", JSON.stringify(top4) === JSON.stringify(esperado), "top 5: " + r.pontes.map(p => p.id + "=" + p.intermediacao.toFixed(3)).join(", "));
const silo = r.areas.find(a => a.area === gab.silo);
const menorEI = r.areas.filter(a => a.ei !== null).sort((a, b) => a.ei - b.ei)[0];
confere("o silo plantado tem o menor E-I", menorEI.area === gab.silo, gab.silo + " E-I = " + silo.ei.toFixed(2));
const iso = r.isolados.map(p => p.id);
confere("os isolados plantados aparecem", gab.isolados.every(x => iso.includes(x)), "achados: " + iso.join(", "));
const gf = r.gestores.find(x => x.gestor === gab.gestor_fora_do_fluxo);
confere("gestor fora do fluxo tem a menor ligação com o time", gf.fracao === Math.min(...r.gestores.map(x => x.fracao)), gf.ligados + " de " + gf.time);
confere("taxa de resposta bate", Math.abs(r.taxa_resposta - (1 - gab.nao_respondentes / gab.pessoas)) < 1e-9, (r.taxa_resposta * 100).toFixed(1) + "%");
confere("modularidade indica grupos separados (> 0,3)", r.modularidade > 0.3, "Q = " + r.modularidade.toFixed(3) + ", " + r.comunidades + " comunidades");
confere("cálculo em menos de 2 s", ms < 2000, ms + " ms");

console.log("\nInsights gerados:");
r.insights.forEach(i => console.log("- [" + i.nivel + "] " + i.titulo));
fs.writeFileSync(path.join(base, "resultado-exemplo.json"), JSON.stringify({ ...r, por_pessoa: undefined }, null, 2));
process.exit(falhas ? 1 : 0);
