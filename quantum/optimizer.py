# flux_on/project/quantum/optimizer.py

import numpy as np
import math
from typing import Dict, List
from scipy.optimize import minimize
from collections import defaultdict
from project.config import BetType, QuantumState, MatchCondition, HumanBiasProfile

class QuantumOptimizer:
    """
    O motor que traduz o 'Fluxo Matemático' em estratégias de aposta.
    Ele não apenas calcula, mas interpreta os padrões subjacentes do jogo.
    """
    def __init__(self):
        self.historical_data = self._load_historical_data()
        self.quantum_factors = self._init_quantum_factors()

    def _load_historical_data(self) -> Dict[str, Dict]:
        """Dados históricos com parâmetros ajustados para todos os tipos de aposta"""
        return {
            'under_25': {
                'base_prob': 0.58, 
                'decay_rate': 0.015
            },
            'over_15_fh': {
                'base_prob': 0.42, 
                'growth_rate': 0.025
            },
            'both_to_score': {
                'base_prob': 0.53, 
                'momentum_factor': 1.2
            },
            'winner': {
                'base_prob': 0.65, 
                'pressure_sensitivity': 1.5
            },
            'double_chance_underdog': {
                'base_prob': 0.45,
                'pressure_factor': 0.15,
                'minute_adjustment': 0.02  # Novo parâmetro adicionado
            },
            'over_15_match': {
                'base_prob': 0.65, 
                'time_decay': 0.3
            }
        }

    def _init_quantum_factors(self) -> Dict[str, float]:
        """
        Fatores que representam constantes fundamentais do 'Fluxo Matemático'.
        - Razão Áurea (PHI): Modula o equilíbrio e a harmonia nas alocações.
        - Pi (PI): Influencia os ciclos e a distribuição de probabilidades.
        - Euler (E): Modela o crescimento exponencial e o momentum.
        """
        return {
            'phi': 1.618,
            'pi': 3.14159,
            'e': 2.718
        }

    def estimate_contextual_probability(self, bet_type: BetType, condition: MatchCondition) -> float:
        """
        Estima a probabilidade de um evento, ajustando a 'leitura do campo' em tempo real.
        Agora com suporte para os novos tipos de aposta.
        """
        data = self.historical_data.get(bet_type.name.lower(), {'base_prob': 0.5})
        base_prob = data['base_prob']
        
        home, away = map(int, condition.score.split('-'))
        total_goals = home + away
        
        prob = base_prob
        
        # Lógica de ajuste baseada no tipo de aposta e na condição da partida
        if bet_type == BetType.UNDER_25:
            if total_goals >= 2: return 0.01
            if total_goals == 1: prob *= 0.6
            prob -= data.get('decay_rate', 0.01) * (condition.minute / 90)
            
        elif bet_type == BetType.OVER_15_FH:
            if condition.minute > 45: return 1.0 if total_goals >= 2 else 0.0
            prob += data.get('growth_rate', 0.02) * (condition.minute / 45)
            prob *= (1 + (condition.home_pressure + condition.away_pressure - 1.0) / 2)

        elif bet_type == BetType.BOTH_TO_SCORE:
            if home > 0 and away > 0: return 0.99
            if condition.minute > 75 and (home == 0 or away == 0): prob *= 0.5
            if home > 0 or away > 0: prob *= data.get('momentum_factor', 1.1)

        # Novos tipos de aposta
        elif bet_type == BetType.DOUBLE_CHANCE_UNDERDOG:
            return self._calc_underdog_double_chance_prob(condition)
        
        elif bet_type == BetType.OVER_15_MATCH:
            return self._calc_over_15_match_prob(condition)

        return min(0.99, max(0.01, prob))

    def _calc_underdog_double_chance_prob(self, condition: MatchCondition, current_odd: float = 2.0) -> float:
        """
        Versão atualizada que considera:
        - A odd atual para ajuste fino
        - Mantém todos os ajustes contextuais
        - Limites racionais de probabilidade
        """
        # Probabilidade base ajustada pela odd
        base_prob = 0.45 * (1.5 / current_odd)  # Fator de redução progressiva
        
        # Aplicação dos ajustes contextuais existentes
        home, away = map(int, condition.score.split('-'))
        is_home_underdog = condition.home_pressure < condition.away_pressure
        underdog_winning = (home > away) if is_home_underdog else (away > home)
        is_draw = home == away
        
        if underdog_winning or is_draw:
            return min(0.99, base_prob * 1.2)  # Bonus por já estar no cenário desejado
        
        # Ajustes dinâmicos (mantidos do original)
        if ((is_home_underdog and home == away - 1) or (not is_home_underdog and away == home - 1)):
            base_prob = min(0.8, base_prob * 1.4)
        elif ((is_home_underdog and home <= away - 2) or (not is_home_underdog and away <= home - 2)):
            base_prob = max(0.1, base_prob * 0.5)
        
        if condition.minute < 30:
            base_prob = min(0.7, base_prob * 1.3)
        elif condition.minute > 75:
            base_prob = max(0.15, base_prob * 0.7)
        
        # Limites finais considerando a odd
        return min(0.6, max(0.2, base_prob))

    def _calc_over_15_match_prob(self, condition: MatchCondition) -> float:
        """Calcula a probabilidade de mais de 1,5 gols na partida inteira"""
        home, away = map(int, condition.score.split('-'))
        total_goals = home + away
        
        # Se já tem 2+ gols, probabilidade 100%
        if total_goals >= 2:
            return 0.99
        
        # Se tem exatamente 1 gol
        if total_goals == 1:
            # Chance alta de sair mais 1 gol, especialmente se o jogo não está no final
            return 0.75 - (condition.minute / 120) * 0.4
        
        # Se ainda 0-0
        base_prob = 0.65
        
        # Aumenta a probabilidade se ambos os times tem alta pressão ofensiva
        pressure_factor = (condition.home_pressure + condition.away_pressure) / 2
        adjusted_prob = base_prob * (0.7 + pressure_factor * 0.6)
        
        # Reduz probabilidade conforme o tempo passa sem gols
        time_decay = (condition.minute / 90) * 0.5
        final_prob = adjusted_prob * (1 - time_decay)
        
        return min(0.95, max(0.05, final_prob))
    
    def _check_profit_margin(self, odd: float, prob: float) -> float:
        """
        Novo método para verificação de margem de lucro
        """
        implied_prob = 1 / odd
        raw_margin = prob - implied_prob
        
        if 1.7 <= odd <= 2.5:
            return raw_margin  # Margem completa
        elif odd > 2.5:
            return raw_margin * 0.7  # Margem reduzida
        else:
            return raw_margin * 0.5  # Margem mínima

    def optimize_portfolio(self, available_bets: Dict[BetType, float], 
                        condition: MatchCondition,
                        quantum_state: QuantumState,
                        bias_profile: HumanBiasProfile = None) -> Dict[BetType, float]:
        """
        Versão aprimorada com:
        - Manutenção de todas as regras originais
        - Integração do HumanBiasProfile
        - Cálculo preservado com ajustes pós-otimização
        """
        # 1. Extração das odds (mantido igual)
        odds = {
            BetType.OVER_15_MATCH: available_bets.get(BetType.OVER_15_MATCH, 1.45),
            BetType.UNDER_25: available_bets.get(BetType.UNDER_25, 1.52),
            BetType.BOTH_TO_SCORE: available_bets.get(BetType.BOTH_TO_SCORE, 2.05),
            BetType.DOUBLE_CHANCE_UNDERDOG: available_bets.get(BetType.DOUBLE_CHANCE_UNDERDOG, 1.75),
            BetType.OVER_15_FH: available_bets.get(BetType.OVER_15_FH, 1.95),
            BetType.WINNER: available_bets.get(BetType.WINNER, 2.15)
        }

        # 2. Aplicação das regras de exclusão (mantido igual)
        selected_bets = {}
        selected_bets[BetType.OVER_15_MATCH] = {'odd': odds[BetType.OVER_15_MATCH], 'weight': 0.333}

        # Regra 2: Under 2.5 vs BTTS (menor odd)
        if odds[BetType.UNDER_25] < odds[BetType.BOTH_TO_SCORE]:
            selected_bets[BetType.UNDER_25] = {
                'odd': odds[BetType.UNDER_25],
                'weight': 0.0  # Será calculado
            }
        else:
            selected_bets[BetType.BOTH_TO_SCORE] = {
                'odd': odds[BetType.BOTH_TO_SCORE],
                'weight': 0.0
            }

        # Regra 3: Dupla Chance vs Vencedor (exclusão mútua)
        if odds[BetType.DOUBLE_CHANCE_UNDERDOG] < odds[BetType.WINNER]:
            selected_bets[BetType.DOUBLE_CHANCE_UNDERDOG] = {
                'odd': odds[BetType.DOUBLE_CHANCE_UNDERDOG],
                'weight': 0.0
            }
        else:
            selected_bets[BetType.WINNER] = {
                'odd': odds[BetType.WINNER],
                'weight': 0.0
            }

        # Regra 4: Gatilho Over 1.5 FH < 2.0
        if odds[BetType.OVER_15_FH] < 2.0:
            selected_bets[BetType.OVER_15_FH] = {
                'odd': odds[BetType.OVER_15_FH],
                'weight': 0.0
            }
            if BetType.UNDER_25 in selected_bets:
                del selected_bets[BetType.UNDER_25]

        # Define secundárias sem Over 1.5 Match (AGORA ANTES DE QUALQUER USO)
        secondary_bets = {k: v for k, v in selected_bets.items() if k != BetType.OVER_15_MATCH}

        # Aplicação dos ajustes de viés humano (MOVIDA PARA DEPOIS DA DEFINIÇÃO DE secondary_bets)
        human_bias_adjustment = {
            BetType.UNDER_25: 1.15,
            BetType.BOTH_TO_SCORE: 1.10,
            BetType.WINNER: 1.20
        }

        for bet_type in secondary_bets:
            if bet_type in human_bias_adjustment:
                selected_bets[bet_type]['weight'] *= human_bias_adjustment[bet_type]

        # 4. Cálculo original dos pesos (mantido)
        if secondary_bets:
            total_ev = 0.0
            ev_data = {}
            for bet_type, data in secondary_bets.items():
                prob = self.estimate_contextual_probability(bet_type, condition)
                ev = (prob * data['odd']) - 1
                ev_adj = ev ** 2
                ev_data[bet_type] = ev_adj
                total_ev += ev_adj

            if total_ev > 0:
                for bet_type, ev in ev_data.items():
                    selected_bets[bet_type]['weight'] = (ev / total_ev) * (1.0 - selected_bets[BetType.OVER_15_MATCH]['weight'])
            else:
                equal_weight = (1.0 - selected_bets[BetType.OVER_15_MATCH]['weight']) / len(secondary_bets)
                for bet_type in secondary_bets:
                    selected_bets[bet_type]['weight'] = equal_weight

        # 5. NOVO: Aplicação dos ajustes comportamentais (após cálculo base)
        if bias_profile:
            # Ajuste de pesos de mercado
            for bet_type in secondary_bets:
                if bet_type in bias_profile.market_weights:
                    selected_bets[bet_type]['weight'] *= bias_profile.market_weights[bet_type]
            
            # Ajustes contextuais dinâmicos
            if hasattr(condition, 'match_context'):
                for context, factors in bias_profile.context_factors.items():
                    if context in condition.match_context:
                        for bet_type, factor in factors.items():
                            if bet_type in selected_bets:
                                selected_bets[bet_type]['weight'] *= factor

        # 6. Garantias e normalização (mantido)
        min_weight = 0.05
        for bet_type in [BetType.OVER_15_FH, BetType.DOUBLE_CHANCE_UNDERDOG, BetType.WINNER]:
            if bet_type in selected_bets and selected_bets[bet_type]['weight'] < min_weight:
                selected_bets[bet_type]['weight'] = min_weight

        total_weights = sum(v['weight'] for v in selected_bets.values())
        if total_weights > 0:
            return {bt: d['weight']/total_weights for bt, d in selected_bets.items()}
        return {bt: 1.0/len(selected_bets) for bt in selected_bets}

    def calculate_kelly_stake(self, prob: float, odd: float, bankroll: float, quantum_state: QuantumState) -> float:
        """
        Critério de Kelly Fracionado e Dinâmico.
        O tamanho da aposta é 'sensível' à volatilidade (estado quântico) do mercado.
        """
        if odd <= 1.0 or prob <= 0:
            return 0.0

        # Fator de risco baseado no estado: mais estável, mais confiança; mais caótico, menos.
        risk_fraction = {
            QuantumState.ESTAVEL: 0.5,   # Meio Kelly
            QuantumState.TRANSICAO: 0.3, # Um terço de Kelly
            QuantumState.CAOTICO: 0.1,   # Apenas 10% do Kelly
        }[quantum_state]

        kelly_fraction = (prob * (odd - 1) - (1 - prob)) / (odd - 1)
        
        if kelly_fraction <= 0:
            return 0.0

        stake = bankroll * kelly_fraction * risk_fraction
        
        # Limites de segurança para proteger o capital
        return max(0.0, min(stake, bankroll * 0.1)) # Nunca apostar mais de 10% do bankroll de uma vez

    def _get_correlation_matrix(self, bet_types: List[BetType]) -> np.ndarray:
        """Matriz de correlação atualizada com os novos tipos"""
        correlations = {
            (BetType.UNDER_25, BetType.OVER_15_FH): -0.6,
            (BetType.UNDER_25, BetType.BOTH_TO_SCORE): -0.7,
            (BetType.OVER_15_FH, BetType.BOTH_TO_SCORE): 0.5,
            (BetType.DOUBLE_CHANCE_UNDERDOG, BetType.OVER_15_MATCH): 0.3,
            (BetType.DOUBLE_CHANCE_UNDERDOG, BetType.UNDER_25): 0.4,
            (BetType.OVER_15_MATCH, BetType.BOTH_TO_SCORE): 0.6,
        }
        
        size = len(bet_types)
        matrix = np.identity(size)
        
        for i in range(size):
            for j in range(i + 1, size):
                val = correlations.get((bet_types[i], bet_types[j]), 
                                    correlations.get((bet_types[j], bet_types[i]), 0.0))
                matrix[i, j] = matrix[j, i] = val
        return matrix