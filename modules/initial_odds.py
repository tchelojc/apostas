import streamlit as st
from typing import Dict
from project.config import BetType, MatchCondition, QuantumState, QuantumBet, HumanBiasProfile
from project.utils import safe_divide

class InitialOddsModule:
    def __init__(self, system):
        self.system = system
        # Garantir que todas as odds necessárias estão inicializadas
        if 'initial_odds_state' not in st.session_state:
            required_bets = [
                BetType.UNDER_25,
                BetType.OVER_15_FH,
                BetType.BOTH_TO_SCORE,
                BetType.WINNER,
                BetType.DOUBLE_CHANCE_UNDERDOG,
                BetType.OVER_15_MATCH
            ]
            
            st.session_state.initial_odds_state = {
                "odds": {bet: 1.85 + (i*0.1) for i, bet in enumerate(required_bets)},
                "allocations": None,
                "confirmed": False,
                "initial_odds_fixed": {bet: 1.85 + (i*0.1) for i, bet in enumerate(required_bets)}  # Adicionado
            }
            
            # Ajustes específicos para apostas obrigatórias
            st.session_state.initial_odds_state["odds"][BetType.DOUBLE_CHANCE_UNDERDOG] = 2.30
            st.session_state.initial_odds_state["odds"][BetType.OVER_15_MATCH] = 1.70
            st.session_state.initial_odds_state["initial_odds_fixed"][BetType.DOUBLE_CHANCE_UNDERDOG] = 2.30
            st.session_state.initial_odds_state["initial_odds_fixed"][BetType.OVER_15_MATCH] = 1.70

        # <-- crucial: guarde uma referência conveniente para o estado
        self.state = st.session_state.initial_odds_state

    def run(self) -> bool:
        with st.container():  # Container para estabilidade
            if st.session_state.portfolio.capital < 20.0:
                return self._run_low_capital_mode()
            return self._run_standard_mode()

    def _run_standard_mode(self) -> bool:
        """Fluxo normal de alocação de 60% para capital padrão."""
        try:
            with st.container():
                st.header("Fase 1: Definindo as Âncoras (60% do Capital)")
                
                # Verificação inicial do estado
                if not hasattr(st.session_state, 'portfolio'):
                    st.error("Erro: Portfólio não inicializado")
                    return False

                capital_for_phase = st.session_state.portfolio.capital * 0.60

                # Seção de ajuste de odds
                with st.expander("Ajustar Odds Iniciais (Pré-Jogo)", expanded=True):
                    cols = st.columns(2)
                    for i, bet_type in enumerate(self.state["odds"]):
                        with cols[i % 2]:
                            self.state["odds"][bet_type] = st.number_input(
                                f"Odd para {bet_type.value}",
                                min_value=1.01,
                                value=self.state["odds"][bet_type],
                                key=f"odd_input_{bet_type.name}_{i}",
                                format="%.2f",
                                step=0.01
                            )

                # Botão de otimização
                if st.button("Analisar e Otimizar Portfólio Inicial", key="optimize_standard"):
                    try:
                        # Criação do MatchCondition sem contextos (ou com contextos vazios)
                        match_condition = MatchCondition(
                            score="0-0",
                            minute=0,
                            home_pressure=0.5,  # Valor padrão
                            away_pressure=0.5   # Valor padrão
                        )
                        
                        # Se precisar de contextos específicos, faça depois:
                        match_condition.match_context.append('high_stakes')  # Adiciona contexto se necessário
                        
                        quantum_state = QuantumState.ESTAVEL

                        # Criando perfil de viés simplificado
                        bias_profile = HumanBiasProfile(
                            market_weights={
                                BetType.UNDER_25: 1.18,
                                BetType.WINNER: 1.15
                            }
                        )

                        self.state["allocations"] = self.system.optimizer.optimize_portfolio(
                            available_bets=self.state["odds"],
                            condition=match_condition,
                            quantum_state=quantum_state,
                            bias_profile=bias_profile
                        )
                        st.success("Portfólio otimizado com sucesso.")
                    except Exception as e:
                        st.error(f"Erro na otimização: {str(e)}")
                        return False

                # Seção de exibição dos resultados
                if self.state["allocations"]:
                    st.subheader("Portfólio Inicial Recomendado")
                    st.info(f"Capital alocado para esta fase: R$ {capital_for_phase:.2f}")
                    
                    initial_bets = {}
                    for bet_type, percentage in self.state["allocations"].items():
                        odd = self.state["odds"][bet_type]
                        amount = capital_for_phase * percentage
                        prob = self.system.optimizer.estimate_contextual_probability(bet_type, MatchCondition())
                        ev = amount * (odd - 1)

                        initial_bets[bet_type] = QuantumBet(bet_type, amount, odd, prob, ev)
                        
                        with st.container():
                            cols = st.columns(3)
                            cols[0].metric(label=f"**{bet_type.value}**", value=f"{percentage:.1%}")
                            cols[1].metric(label="Valor Alocado", value=f"R$ {amount:.2f}")
                            cols[2].metric(label="Lucro Esperado", value=f"R$ {ev:.2f}", delta=f"{(odd-1)*100:.1f}% ROI")

                    # BOTÃO DE CONFIRMAÇÃO (dentro do bloco de allocations)
                    if st.button("Confirmar Âncoras e Avançar", key="confirm_standard", type="primary"):
                        if not self.state["allocations"]:
                            st.error("Nenhuma alocação calculada!")
                            return False
                        
                        # Validação modificada para apostas obrigatórias
                        mandatory_bets = [BetType.DOUBLE_CHANCE_UNDERDOG, BetType.OVER_15_MATCH]
                        warning_shown = False
                        
                        for bet in mandatory_bets:
                            if bet not in initial_bets or initial_bets[bet].amount <= 0:
                                st.warning(f"Atenção: {bet.value} não foi alocada (pode ser intencional)")
                                warning_shown = True
                        
                        # Opção para forçar alocação mínima
                        if warning_shown:
                            force_allocation = st.checkbox("Forçar alocação mínima nas apostas obrigatórias?")
                            if force_allocation:
                                min_amount = capital_for_phase * 0.05  # 5% do capital da fase
                                for bet in mandatory_bets:
                                    if bet not in initial_bets or initial_bets[bet].amount <= 0:
                                        odd = self.state["odds"][bet]
                                        prob = self.system.optimizer.estimate_contextual_probability(bet, MatchCondition())
                                        initial_bets[bet] = QuantumBet(bet, min_amount, odd, prob, min_amount * (odd - 1))
                        
                        try:     
                            # Armazenar as odds iniciais fixas ANTES de confirmar as apostas                    
                            if not self.state.get("initial_odds_fixed"):
                                self.state["initial_odds_fixed"] = {}

                            self.state["initial_odds_fixed"] = {
                                bet_type: bet.odd for bet_type, bet in initial_bets.items()
                            }
                            
                            st.session_state.portfolio.initial_bets = initial_bets
                            st.session_state.initial_odds_confirmed = True
                            self.state["confirmed"] = True
                            return True
                        except Exception as e:
                            st.error(f"Erro ao confirmar: {str(e)}")
                            return False

            return False
        except Exception as e:
            st.error(f"Erro na fase 1: {str(e)}")
            st.session_state.initial_odds_confirmed = False
            return False

    def _run_low_capital_mode(self) -> bool:
        """Versão simplificada para capital pequeno"""
        st.warning("Modo Low-Capital: Alocação mínima de R$5,00")
        
        bet_type = BetType.UNDER_25  # Mercado mais seguro
        odd = self.state["odds"][bet_type]
        amount = min(5.0, st.session_state.portfolio.capital * 0.8)
        
        prob = self.system.optimizer.estimate_contextual_probability(bet_type, MatchCondition())
        ev = (prob * odd - 1) * amount

        st.subheader("Recomendação de Aposta Única")
        col1, col2, col3 = st.columns(3)
        col1.metric("Mercado Selecionado", bet_type.value)
        col2.metric("Odd Considerada", f"{odd:.2f}")
        col3.metric("Valor Esperado", f"R$ {ev:.2f}")

        if st.button("Confirmar Aposta Única e Avançar", key="confirm_low_capital"):
            st.session_state.portfolio.initial_bets = {
                bet_type: QuantumBet(bet_type, amount, odd, prob, ev)
            }
            return True
            
        return False