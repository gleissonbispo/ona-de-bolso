"""ONA de bolso: análise de rede organizacional a partir de um questionário e duas planilhas."""

from .io import exemplo, ler_entrada, ler_pessoas_ligacoes, ler_tabelas, validar
from .metricas import Resultado, analisar, posicoes, simular_saida

__version__ = "3.0.0"
__all__ = ["Resultado", "analisar", "exemplo", "ler_entrada", "ler_pessoas_ligacoes", "ler_tabelas",
           "posicoes", "simular_saida", "validar", "__version__"]
