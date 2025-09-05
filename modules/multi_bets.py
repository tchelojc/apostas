import streamlit as st
from project.config import BetType, MatchCondition, QuantumState, QuantumBet  # Adicione QuantumBet aqui
from project.utils import safe_divide
from project.event_manager import EventManager

STATE_KEYS = {
    'multi_bets': {
        'selected_combos': [],
        'manual_odds': {},
        'calculated_amounts': []
    },
    'in_play': {
        'score': '0-0',
        'minute': 0,
        'volatility': 'Estável'
    }
}

def init_state(module_name):
    if f'{module_name}_state' not in st.session_state:
        st.session_state[f'{module_name}_state'] = STATE_KEYS[module_name].copy()

class MultiBetsModule:
    def __init__(self, system):
        self.system = system
        if hasattr(system, 'bridge'):
            system.bridge.register_module('multi_bets', self)
        
        if 'multi_bets_state' not in st.session_state:
            st.session_state.multi_bets_state = {
                "selected_combos": [],
                "manual_odds": {},
                "calculated": False
            }
        self.state = st.session_state.multi_bets_state

    def run(self) -> bool:
        try:
            # Verificação robusta de pré-requisitos
            if not st.session_state.get("initial_odds_confirmed", False):
                st.error("Confirme as apostas iniciais primeiro!")
                return False
                
            with st.container():
                st.markdown("""
                <style>
                .wrap-text {
                    white-space: normal !important;
                    word-wrap: break-word !important;
                    overflow-wrap: break-word !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                st.header("Fase 2: Encontrando Combinações Harmônicas (31%)")
                
                # Verificação de apostas iniciais
                if not hasattr(st.session_state.portfolio, 'initial_bets') or not st.session_state.portfolio.initial_bets:
                    st.error("Complete a Fase 1 primeiro! Nenhuma aposta inicial definida.")
                    return False
                    
                # Obter combinações disponíveis
                available_combos = self._get_available_combinations()
                
                if not available_combos:
                    st.warning("Nenhuma combinação disponível devido a apostas iniciais faltando.")
                    return False
                    
                # Mostrar seleção de combinações
                st.subheader("Selecione as Combinações")
                selected = self._render_combo_selection(available_combos)
                
                # Mostrar detalhes das combinações selecionadas
                if selected:
                    capital_for_phase = self._calculate_available_capital()
                    self._render_combo_details(selected, capital_for_phase)
                    
                    # Botão de confirmação (agora dentro do if selected)
                    if st.button("Confirmar Combinações e Avançar", key="confirm_combos", type="primary"):
                        st.session_state.portfolio.multi_bets = selected
                        st.session_state.multi_bets_confirmed = True
                        return True

            return False
        except Exception as e:
            st.error(f"Erro na fase 2: {str(e)}")
            st.session_state.multi_bets_confirmed = False
            return False
        
    def get_calculated_amounts(self):
        """Retorna os valores calculados de forma segura"""
        if hasattr(self, 'state') and 'calculated_amounts' in self.state:
            return self.state['calculated_amounts']
        return None

    def _get_available_combinations(self):
        initial_bets = st.session_state.portfolio.initial_bets
        
        # Dicionário de nomes de apostas (resolve o erro BET_NAMES)
        BET_NAMES = {
            BetType.DOUBLE_CHANCE_UNDERDOG: "Dupla Chance Azarão",
            BetType.OVER_15_MATCH: "1,5 Gols (Partida Inteira)",
            BetType.UNDER_25: "Under 2.5 Gols",
            BetType.WINNER: "Vencedor da Partida",
            BetType.OVER_15_FH: "Mais de 1.5 Gols (1º Tempo)",
            BetType.BOTH_TO_SCORE: "Ambos Marcam"
        }

        # Verificação adaptativa das apostas obrigatórias
        mandatory_bets = {
            BetType.DOUBLE_CHANCE_UNDERDOG: "Dupla Chance Azarão",
            BetType.OVER_15_MATCH: "1,5 Gols (Partida Inteira)"
        }
        
        # Cria apostas faltantes com valor zero
        for bet, name in mandatory_bets.items():
            if bet not in initial_bets:
                odd = 2.30 if bet == BetType.DOUBLE_CHANCE_UNDERDOG else 1.70
                initial_bets[bet] = QuantumBet(bet, 0, odd, 0, 0)

        # Função para obter odds com fallback
        def get_odd(bet_type, default_odd):
            return initial_bets[bet_type].odd if bet_type in initial_bets else default_odd

        # Todas combinações possíveis
        all_combinations = [
            {
                "name": "Dupla Chance Azarão + 1,5 Gols (Partida Inteira)",
                "bets": [BetType.DOUBLE_CHANCE_UNDERDOG, BetType.OVER_15_MATCH],
                "odds": [
                    get_odd(BetType.DOUBLE_CHANCE_UNDERDOG, 2.30),
                    get_odd(BetType.OVER_15_MATCH, 1.70)
                ],
                "description": "Proteção do azarão com expectativa de gols",
                "requires_allocation": True
            },
            {
                "name": "Combo Defensivo",
                "bets": [BetType.UNDER_25, BetType.WINNER],
                "odds": [
                    get_odd(BetType.UNDER_25, 1.90),
                    get_odd(BetType.WINNER, 1.50)
                ],
                "description": "Proteção contra resultados inesperados",
                "requires_allocation": False
            },
            {
                "name": "Combo de Gols",
                "bets": [BetType.OVER_15_FH, BetType.BOTH_TO_SCORE],
                "odds": [
                    get_odd(BetType.OVER_15_FH, 2.20),
                    get_odd(BetType.BOTH_TO_SCORE, 1.80)
                ],
                "description": "Foco em jogos com alta probabilidade de gols",
                "requires_allocation": False
            }
        ]

        # Filtra combinações disponíveis
        available_combos = all_combinations
        
        # Mostra aviso se alguma combinação foi filtrada
        if len(available_combos) < len(all_combinations):
            missing = [combo["name"] for combo in all_combinations 
                    if combo not in available_combos]
            st.warning(f"Combinações não disponíveis: {', '.join(missing)} - Aloque valores nas apostas correspondentes")

        return available_combos

    def _render_combo_selection(self, combos):
        """Renderiza a seleção de combinações"""
        selected = []
        for combo in combos:
            combo_key = f"combo_{combo['name']}"
            if st.checkbox(
                f"**{combo['name']}**: {combo['description']} (Odd: {combo['odds'][0] * combo['odds'][1]:.2f})",
                key=f"combo_{combo['name']}",
                value=any(c['name'] == combo['name'] for c in self.state["selected_combos"])
            ):
                selected.append(combo)
        return selected

    def _calculate_combo_priority(self, combo):
        """Calcula a prioridade com base em regras estratégicas revisadas"""
        priority = 0.0
        initial_odds = st.session_state.initial_odds_state["initial_odds_fixed"]
        
        # 1. Mapear as odds da combinação
        combo_odds = {}
        for bet_type, odd in zip(combo['bets'], combo['odds']):
            combo_odds[bet_type] = initial_odds.get(bet_type, odd)
        
        # 2. Prioridade base para todas as combinações
        priority += 0.3  # Valor base para qualquer combinação
        
        # 3. Regra principal: Favorito vs Dupla Chance
        if BetType.DOUBLE_CHANCE_UNDERDOG in combo_odds and BetType.WINNER in combo_odds:
            odd_dc = combo_odds[BetType.DOUBLE_CHANCE_UNDERDOG]
            odd_fav = combo_odds[BetType.WINNER]
            
            # Se odd do favorito for maior, prioriza FAVORITO
            if odd_fav > odd_dc:
                priority += 0.4  # Prioridade para combinações com favorito
            else:
                priority += 0.2  # Prioridade moderada para Dupla Chance
        
        # 4. Ajuste para combinações defensivas (Under 2.5)
        if BetType.UNDER_25 in combo_odds:
            odd_under = combo_odds[BetType.UNDER_25]
            if odd_under > 2.0:
                priority += 0.3  # Prioridade média quando odd alta
            else:
                priority += 0.1  # Prioridade baixa
        
        # 5. Ajuste para combinações ofensivas (Over 1.5 FH)
        if BetType.OVER_15_FH in combo_odds:
            odd_over = combo_odds[BetType.OVER_15_FH]
            if odd_over < 2.0:
                priority += 0.25  # Prioridade quando odd baixa
        
        return min(priority, 1.0)  # Limite máximo

    def _calculate_combo_weights(self, combos):
        """Calcula pesos com distribuição mais equilibrada"""
        weights = []
        initial_odds = st.session_state.initial_odds_state["initial_odds_fixed"]
        
        # 1. Calcular prioridades base
        priorities = [self._calculate_combo_priority(c) for c in combos]
        
        # 2. Calcular valor investido inicialmente (com fallback)
        invested = []
        portfolio = getattr(st.session_state, 'portfolio', None)
        initial_bets = getattr(portfolio, 'initial_bets', {})
        
        for combo in combos:
            total = sum(
                initial_bets[bt].amount 
                for bt in combo['bets'] 
                if bt in initial_bets
            )
            invested.append(total if total > 0 else 0.1)  # Evita zero
        
        # 3. Fator de ajuste pelas odds (favorece odds menores)
        odd_factors = []
        for combo in combos:
            if len(combo['bets']) >= 2:
                odd1 = initial_odds.get(combo['bets'][0], combo['odds'][0])
                odd2 = initial_odds.get(combo['bets'][1], combo['odds'][1])
                odd_factors.append(1/(odd1 * odd2))  # Inverso do produto
            else:
                odd_factors.append(1.0)
        
        # Normalização
        total_priority = sum(priorities) or 1
        total_invested = sum(invested) or 1
        total_odd = sum(odd_factors) or 1
        
        # Combinação final (50% prioridade, 30% investimento, 20% odds)
        for p, i, o in zip(priorities, invested, odd_factors):
            weight = (0.5 * safe_divide(p, total_priority)) + \
                    (0.3 * safe_divide(i, total_invested)) + \
                    (0.2 * safe_divide(o, total_odd))
            weights.append(weight)
        
        # Garantir soma = 1
        total = sum(weights) or 1
        return [w/total for w in weights]
    
    def _render_strategy_analysis(self, combo, current_odds):
        """Mostra a análise com foco na distribuição correta"""
        initial_odds = st.session_state.initial_odds_state["initial_odds_fixed"]
        analysis = []
        
        # 1. Verificar relação Favorito/Dupla Chance
        if (BetType.DOUBLE_CHANCE_UNDERDOG in combo['bets'] and 
            BetType.WINNER in combo['bets']):
            odd_dc = initial_odds.get(BetType.DOUBLE_CHANCE_UNDERDOG)
            odd_fav = initial_odds.get(BetType.WINNER)
            
            if odd_dc and odd_fav:
                if odd_fav > odd_dc:
                    analysis.append("Prioridade: FAVORITO (odd maior)")
                    analysis.append(f"Diferença: +{odd_fav - odd_dc:.2f}")
                else:
                    analysis.append("Prioridade: DUPLA CHANCE")
        
        # 2. Verificar Under 2.5 (se aplicável)
        if BetType.UNDER_25 in combo['bets']:
            odd_under = initial_odds.get(BetType.UNDER_25)
            if odd_under:
                analysis.append(f"Under 2.5: {odd_under:.2f} (Peso secundário)")
        
        # 3. Mostrar recomendação de alocação
        priority = self._calculate_combo_priority(combo)
        if priority > 0.7:
            analysis.append("🔵 ALTA PRIORIDADE")
        elif priority > 0.4:
            analysis.append("🟢 PRIORIDADE MÉDIA")
        else:
            analysis.append("🟡 PRIORIDADE BAIXA")
        
        st.markdown('<div class="strategy-analysis">' + 
                ''.join([f'<div class="strategy-item">{item}</div>' for item in analysis]) +
                '</div>', unsafe_allow_html=True)

    def _render_combo_details(self, combos, capital):
        """Renderização com distribuição visual melhorada"""
        st.subheader("📊 Detalhes das Combinações (Distribuição Corrigida)")
        
        if capital <= 0:
            st.warning("Capital insuficiente para distribuição")
            return
        
        # Calcular pesos e valores
        weights = self._calculate_combo_weights(combos)
        amounts = [capital * w for w in weights]
        
        # Armazena os valores calculados no session_state para uso posterior
        self.state['calculated_amounts'] = amounts
        
        # Ajuste para garantir soma exata
        total = sum(amounts)
        if total != capital:
            amounts[-1] += (capital - total)
        
        # Exibir cada combinação
        for i, combo in enumerate(combos):
            with st.expander(f"🔍 {combo['name']} (Alocado: R$ {amounts[i]:.2f})", expanded=True):
                cols = st.columns([1, 1, 2])
                
                # Calcular odd combinada
                current_odds = self.state.get("manual_odds", {}).get(combo['name'], combo['odds'])
                combined_odd = current_odds[0] * current_odds[1]
                
                cols[0].metric("Odd Combinada", f"{combined_odd:.2f}")
                cols[1].metric("Valor Alocado", f"R$ {amounts[i]:.2f}")
                
                # Análise estratégica
                with cols[2]:
                    self._render_strategy_analysis(combo, current_odds)
                    
                    # Inputs para ajuste manual
                    st.markdown("🔢 Ajuste de Odds")
                    col1, col2 = st.columns(2)
                    with col1:
                        new_odd1 = st.number_input(
                            f"Odd {combo['bets'][0].value}",
                            value=float(current_odds[0]),
                            min_value=1.01,
                            step=0.01,
                            key=f"odd_{combo['name']}_1"
                        )
                    with col2:
                        new_odd2 = st.number_input(
                            f"Odd {combo['bets'][1].value}",
                            value=float(current_odds[1]),
                            min_value=1.01,
                            step=0.01,
                            key=f"odd_{combo['name']}_2"
                        )
                    
                    # Atualizar odds manuais
                    if 'manual_odds' not in self.state:
                        self.state['manual_odds'] = {}
                    self.state['manual_odds'][combo['name']] = [new_odd1, new_odd2]

    def _calculate_available_capital(self):
        """Calcula o capital disponível de forma segura"""
        initial_bets = st.session_state.portfolio.initial_bets.values()
        total_initial = sum(b.amount for b in initial_bets) if initial_bets else 0
        return min(
            st.session_state.portfolio.capital * 0.31,
            st.session_state.portfolio.capital - total_initial
        )

    def _calculate_combinations(self, capital):
        """Calcula os valores das combinações"""
        num_combos = len(self.state["selected_combos"])
        amount_per_combo = capital / num_combos
        
        st.subheader("Combinações Selecionadas")
        st.info(f"Capital alocado: R$ {capital:.2f} (R$ {amount_per_combo:.2f} por combinação)")
        
        for combo in self.state["selected_combos"]:
            st.write(f"- **{combo['name']}**: Odd Combinada: {combo['odds'][0] * combo['odds'][1]:.2f}")

    def _confirm_combinations(self):
        """Confirma as combinações selecionadas"""
        try:
            st.session_state.portfolio.multi_bets = self.state["selected_combos"]
            self.state["calculated"] = False
            st.session_state.current_phase = "in_play"  # Força a transição
            st.rerun()  # Atualiza a interface
            return True
        except Exception as e:
            st.error(f"Erro ao confirmar combinações: {str(e)}")
            return False