# flux_on/project/config.py
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List  # Adicione List aqui

# O resto do código permanece o mesmo

from enum import Enum

class BetType(Enum):
    """Tipos de apostas com todos os cenários cobertos."""
    # --- Core ---
    UNDER_25 = "Under 2.5 Gols"
    OVER_15_FH = "Over 1.5 Gols (1º Tempo)"
    BOTH_TO_SCORE = "Ambas Marcam"
    BOTH_TO_SCORE_NO = "Ambas Não Marcam"  # Hedge para BOTH_TO_SCORE
    WINNER = "Vencedor da Partida"
    HOME_WIN = "Casa Vence"  # Para estratégias de virada
    AWAY_WIN = "Visitante Vence"
    DRAW = "Empate"  # Critical (Quantum Comeback)
    
    # --- Hedges ---
    OVER_25 = "Over 2.5 Gols (Hedge)"
    UNDER_35 = "Under 3.5 Gols"  # Prioridade em placares altos
    NO_GOAL = "Sem Gols (Hedge)"
    
    # --- Cenários Especiais ---
    NEXT_GOAL_HOME = "Próximo Gol - Casa"
    NEXT_GOAL_AWAY = "Próximo Gol - Visitante"
    GOAL_NEXT_5_MIN = "Gol nos Próximos 5 Min"  # Volatilidade
    DOUBLE_CHANCE_UNDERDOG = "Dupla Chance Azarão"
    OVER_15_MATCH = "Mais de 1.5 Gols (Partida)"
    AWAY_HANDICAP = "Handicap Visitante"  # Red Card Effect
    NO_MORE_GOALS = "Sem Mais Gols"  # Para partidas "mornas"
    NEXT_GOAL_LOSING_TEAM = "Próximo Gol - Time Perdendo"  # Pressão inversa

    # --- Métodos auxiliares ---
    @classmethod
    def get_opposite(cls, bet_type):
        """Retorna o tipo de aposta oposto para estratégias de hedge"""
        opposites = {
            cls.HOME_WIN: cls.AWAY_WIN,
            cls.AWAY_WIN: cls.HOME_WIN,
            cls.OVER_25: cls.UNDER_25,
            cls.BOTH_TO_SCORE: cls.BOTH_TO_SCORE_NO,
            cls.UNDER_25: cls.OVER_25,
            cls.DRAW: None,  # Não tem oposto direto
            cls.NEXT_GOAL_HOME: cls.NEXT_GOAL_AWAY,
            cls.NEXT_GOAL_AWAY: cls.NEXT_GOAL_HOME
        }
        return opposites.get(bet_type)
    
    @classmethod
    def is_under_over_type(cls, bet_type):
        """Verifica se é uma aposta do tipo under/over"""
        return bet_type in [cls.UNDER_25, cls.OVER_25, cls.UNDER_35, cls.OVER_15_FH, cls.OVER_15_MATCH]
    
    @classmethod
    def is_winner_type(cls, bet_type):
        """Verifica se é uma aposta no vencedor"""
        return bet_type in [cls.HOME_WIN, cls.AWAY_WIN, cls.DRAW, cls.WINNER]

class QuantumState(Enum):
    """
    Representa o 'estado quântico' do mercado, uma medida da sua volatilidade e previsibilidade.
    - ESTAVEL: Movimento previsível, baixa volatilidade.
    - TRANSICAO: O padrão está mudando, momento de alerta e oportunidade.
    - CAOTICO: Alta volatilidade, imprevisível. Risco elevado.
    """
    ESTAVEL = "Estável"
    TRANSICAO = "Transição"
    CAOTICO = "Caótico"

@dataclass
class MatchCondition:
    """
    Representa uma fotografia do estado atual da partida.
    Agora com suporte para contexto da partida.
    """
    score: str = "0-0"
    minute: int = 0
    home_pressure: float = 0.5
    away_pressure: float = 0.5
    match_context: List[str] = field(default_factory=list)  # Novo campo adicionado

@dataclass
class QuantumBet:
    """Representa uma aposta individual com todos os seus atributos."""
    bet_type: BetType
    amount: float
    odd: float
    probability: float
    ev: float = 0.0  # Expected Value (mantido como ev para compatibilidade)

@dataclass
class BetPortfolio:
    """
    Armazena o portfólio de apostas, representando a estratégia completa.
    - initial_bets: As âncoras do sistema (60%).
    - multi_bets: As combinações harmônicas (31%).
    - in_play_bets: Os ajustes dinâmicos (9%).
    """
    capital: float
    initial_bets: Dict[BetType, QuantumBet] = field(default_factory=dict)
    multi_bets: list = field(default_factory=list)
    in_play_bets: Dict[BetType, QuantumBet] = field(default_factory=dict)
    
class CognitiveBias(Enum):
    ANCHORING = "Ancoragem"
    AVAILABILITY = "Disponibilidade"
    ILLUSORY_CONTROL = "Ilusão de Controle"

# Adicione isso em config.py
@dataclass 
class HumanBiasProfile:
    """
    Perfil de ajustes comportamentais para complementar a modelagem matemática
    """
    market_weights: Dict[BetType, float] = field(default_factory=lambda: {
        BetType.UNDER_25: 1.15,
        BetType.WINNER: 1.20,
        BetType.BOTH_TO_SCORE: 1.10,
        BetType.OVER_15_MATCH: 0.95
    })
    
    context_factors: Dict[str, Dict[BetType, float]] = field(default_factory=lambda: {
        'high_stakes': {BetType.UNDER_25: 1.25},
        'derby': {BetType.WINNER: 1.30}
    })