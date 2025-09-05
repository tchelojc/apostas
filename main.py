import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from project.quantum.optimizer import QuantumOptimizer
from project.modules.initial_odds import InitialOddsModule
from project.modules.multi_bets import MultiBetsModule
from project.modules.in_play import InPlayModule
from project.config import BetPortfolio, BetType, QuantumBet
from project.utils import safe_divide

class BettingSystem:
    def __init__(self):
        self.optimizer = QuantumOptimizer()
        self.initial_odds = InitialOddsModule(self)
        self.multi_bets = MultiBetsModule(self)
        self.in_play = InPlayModule(self)
        self._phase_containers = {
            "initial_odds": st.empty(),
            "multi_bets": st.empty(),
            "in_play": st.empty()
        }
        
    def _validate_state(self):
        required_states = {
            'portfolio': None,
            'current_phase': "initial_odds",
            'initial_odds_state': {},
            'initial_odds_confirmed': False,
            'multi_bets_confirmed': False,
            'in_play_confirmed': False
        }
        
        missing_states = []
        
        for state, default_value in required_states.items():
            if state not in st.session_state:
                logger.warning(f"Estado {state} não encontrado - Inicializando com valor padrão")
                st.session_state[state] = default_value
                missing_states.append(state)
        
        if missing_states:
            logger.info(f"Estados inicializados: {missing_states}")
        
        return True

    def run_phase(self):
        # Validação inicial do estado
        self._validate_state()
        
        try:
            current_phase = st.session_state.current_phase
            
            # Limpeza segura dos containers
            for container in self._phase_containers.values():
                container.empty()

            # --- Validação Centralizada ---
            if current_phase == "multi_bets" and not st.session_state.get("initial_odds_confirmed", False):
                st.error("Complete a Fase 1 primeiro!")
                st.session_state.current_phase = "initial_odds"
                st.rerun()
                return

            if current_phase == "in_play" and not all([
                st.session_state.get("initial_odds_confirmed", False),
                st.session_state.get("multi_bets_confirmed", False)
            ]):
                st.error("Complete as fases anteriores primeiro!")
                st.session_state.current_phase = "multi_bets"
                st.rerun()
                return

            # --- Renderização da Fase Atual ---
            with self._phase_containers[current_phase]:
                phase_result = False
                
                if current_phase == "initial_odds":
                    phase_result = self.initial_odds.run()
                    if phase_result and st.session_state.get("initial_odds_confirmed"):
                        st.session_state.current_phase = "multi_bets"

                elif current_phase == "multi_bets":
                    phase_result = self.multi_bets.run()
                    if phase_result and st.session_state.get("multi_bets_confirmed"):
                        st.session_state.current_phase = "in_play"

                elif current_phase == "in_play":
                    phase_result = self.in_play.run()
                    if phase_result and st.session_state.get("in_play_confirmed"):
                        self._reset_system()

                # Transição segura
                if phase_result and current_phase != st.session_state.current_phase:
                    st.rerun()
                    
                if not self._validate_state():
                    st.error("Estado inválido - Reiniciando sistema")
                    self._reset_system()
                    return

        except Exception as e:
            st.error(f"Erro crítico: {str(e)}")
            self._reset_system()

    def _reset_system(self):
        """Reinicialização completa e segura do sistema"""
        current_capital = st.session_state.portfolio.capital
        st.session_state.clear()
        st.session_state.portfolio = BetPortfolio(capital=current_capital)
        st.session_state.current_phase = "initial_odds"
        st.session_state.system = self

    def _safe_phase_transition(self, next_phase):
        """Garante uma transição limpa entre fases"""
        st.session_state.current_phase = next_phase
        st.rerun()

def initialize_session_state():
    """Garante a inicialização correta de todos os estados com apostas obrigatórias"""
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = BetPortfolio(capital=0.0)
        
        # Inicializa com todas as apostas necessárias com valores padrão
        required_bets = [
            BetType.DOUBLE_CHANCE_UNDERDOG,  # <-- Garantir que está incluso
            BetType.OVER_15_MATCH,
            BetType.UNDER_25,
            BetType.OVER_15_FH,
            BetType.BOTH_TO_SCORE,
            BetType.WINNER
        ]
        
        st.session_state.portfolio.initial_bets = {
            bet: QuantumBet(
                bet_type=bet,
                amount=0.0,  # Valor será definido na Fase 1
                odd=1.0,     # Odd será ajustada na Fase 1
                probability=0.0,
                ev=0.0
            )
            for bet in required_bets
        }
    
    if 'current_phase' not in st.session_state:
        st.session_state.current_phase = "initial_odds"
    
    if 'system' not in st.session_state:
        st.session_state.system = BettingSystem()

def main():
    # Configuração inicial estável
    st.set_page_config(
        page_title="FLUX-ON",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS para melhorar as interações
    st.markdown("""
    <style>
    /* Aplica transição de opacidade nos blocos verticais do Streamlit */
    div[data-testid="stVerticalBlock"] {
        transition: opacity 0.25s ease-in-out;
    }

    /* Ao atualizar, mantém opacidade para evitar flash branco */
    div[data-testid="stVerticalBlock"] > * {
        opacity: 1;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Inicializa estados antes de qualquer renderização
    initialize_session_state()

    # Interface principal
    st.title("Sistema de Apostas FLUX-ON")
    st.markdown("---")

    # Sidebar com controle de estado
    with st.sidebar:
        st.header("Painel de Controle do Fluxo")
        
        # Controle de capital apenas na fase inicial
        if st.session_state.current_phase == "initial_odds" and st.session_state.portfolio.capital == 0:
            capital = st.number_input(
                "Capital Total (R$)", 
                min_value=10.0, 
                value=100.0, 
                step=10.0,
                key="capital_input"
            )
            
            if st.button("Iniciar Fluxo", key="init_flow"):
                st.session_state.portfolio.capital = capital
                st.rerun()
        
        # Exibição do estado atual
        st.metric("Capital Total", f"R$ {st.session_state.portfolio.capital:.2f}")
        st.write("---")
        st.subheader("Navegação de Fase")
        st.write(f"Fase Atual: **{st.session_state.current_phase.replace('_', ' ').title()}**")

    # Conteúdo principal condicional
    if st.session_state.portfolio.capital > 0:
        st.session_state.system.run_phase()
    else:
        st.info("Defina o Capital Total na barra lateral e clique em 'Iniciar Fluxo' para começar.")

if __name__ == "__main__":
    main()