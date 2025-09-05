import streamlit as st
import pandas as pd
from typing import Optional
import plotly.express as px  # Adicione esta linha no topo com os outros imports
from project.config import BetType, MatchCondition, QuantumState, QuantumBet
from project.utils import safe_divide
from project.event_manager import EventManager
from functools import lru_cache

@lru_cache(maxsize=32)
def calculate_probability(bet_type, score, minute, home_pressure, away_pressure):
    """Função otimizada para cálculos de probabilidade"""
    # Implemente aqui os cálculos que estavam em estimate_contextual_probability
    pass

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

class InPlayModule:
    def __init__(self, system):
        self.system = system
        if 'in_play_state' not in st.session_state:
            st.session_state.in_play_state = {
                "score": "0-0",
                "minute": 0,
                "home_pressure": 0.5,
                "away_pressure": 0.5,
                "volatility": "Estável"  # Valor padrão inicial, será atualizado pelo usuário
            }
        self.state = st.session_state.in_play_state

        # Adicionando mapeamento de volatilidade para valores numéricos
        self.volatility_map = {
            "Estável": 0.3,
            "Transição": 0.6,
            "Caótico": 0.9
        }
        
    def _load_custom_styles(self):
        """Carrega estilos e animações customizadas"""
        st.markdown("""
        <style>
            .smooth-transition {
                transition: all 0.3s ease-in-out;
            }
            .data-card {
                opacity: 0;
                transform: translateY(10px);
                transition: opacity 0.5s, transform 0.5s;
            }
            .data-card.visible {
                opacity: 1;
                transform: translateY(0);
            }
        </style>
        """, unsafe_allow_html=True)

        # JavaScript para animações
        st.components.v1.html("""
        <script>
        window.addEventListener('load', () => {
            const observer = new MutationObserver(() => {
                document.querySelectorAll('.data-card').forEach(card => {
                    card.classList.add('visible');
                });
            });
            observer.observe(document.body, {childList: true, subtree: true});
        });
        </script>
        """)

    def run(self):
        try:
            # Verificação robusta de pré-requisitos
            if not self._validate_prerequisites():
                return False

            # Container principal com lógica condicional aprimorada
            main_container = st.container()
            with main_container:
                st.header("🎯 Fase 3: Mapeamento Vivo e Ajustes (9% do Capital)")
                st.markdown("""
                    **Fase sensorial** onde analisamos o jogo em tempo real para ajustar nossas posições.
                    Utilize os controles abaixo para simular o estado atual da partida.
                """)
                
                self._render_control_panel()
                self._render_probability_chart()
                self._render_bet_recommendations()
                
                # Botão de finalização com verificação adicional
                if st.button("Finalizar Ciclo", type="primary", key="finish_cycle"):
                    if self._validate_bets():
                        st.session_state.in_play_confirmed = True
                        st.success("Ciclo concluído com sucesso!")
                        st.balloons()
                        return True
                    else:
                        st.error("Corrija as apostas antes de finalizar")
                        return False

            return False
        except Exception as e:
            st.error(f"Erro crítico na fase 3: {str(e)}")
            st.session_state.in_play_confirmed = False
            return False
        
    def get_multi_bets_info(self):
        """Obtém informações das apostas múltiplas de forma segura"""
        if not hasattr(st.session_state, 'multi_bets_module'):
            return None
            
        multi_bets_module = st.session_state.multi_bets_module
        amounts = multi_bets_module.get_calculated_amounts()
        
        if amounts and hasattr(st.session_state.portfolio, 'multi_bets'):
            return list(zip(st.session_state.portfolio.multi_bets, amounts))
        return None
    
    def _validate_prerequisites(self):
        """Validação completa dos pré-requisitos para a fase"""
        checks = [
            st.session_state.get("initial_odds_confirmed", False),
            st.session_state.get("multi_bets_confirmed", False),
            hasattr(st.session_state, 'portfolio'),
            hasattr(st.session_state.portfolio, 'initial_bets'),
            hasattr(st.session_state.portfolio, 'multi_bets')
        ]
        
        if not all(checks):
            missing = [
                "Confirmação da Fase 1" if not checks[0] else None,
                "Confirmação da Fase 2" if not checks[1] else None,
                "Portfólio inicializado" if not checks[2] else None,
                "Apostas iniciais definidas" if not checks[3] else None,
                "Combinações múltiplas definidas" if not checks[4] else None
            ]
            missing = [m for m in missing if m is not None]
            
            st.error(f"Pré-requisitos faltando: {', '.join(missing)}")
            return False
        return True

    def _validate_bets(self):
        """Validação das apostas antes de finalizar"""
        if not st.session_state.portfolio.initial_bets:
            st.error("Nenhuma aposta inicial definida")
            return False
            
        if not st.session_state.portfolio.multi_bets:
            st.error("Nenhuma combinação múltipla definida")
            return False
            
        return True

    def _render_control_panel(self):
        """Painel de controle com seleção de placar inteligente"""
        st.subheader("📊 Painel de Controle Ao Vivo")
        
        # CSS para melhorar a visualização
        st.markdown("""
        <style>
            .score-selector { margin-bottom: 1rem; }
            .pressure-sliders { margin-top: 1.5rem; }
        </style>
        """, unsafe_allow_html=True)
        
        # Seleção de placar com opções pré-definidas
        st.markdown('<div class="score-selector">', unsafe_allow_html=True)
        score_options = {
            "0-0": "Jogo equilibrado",
            "1-0": "Casa liderando",
            "0-1": "Visitante liderando",
            "1-1": "Empate com gols",
            "2-0": "Casa dominando",
            "0-2": "Visitante dominando",
            "2-1": "Casa com vantagem",
            "1-2": "Visitante com vantagem",
            "2-2": "Jogo aberto"
        }
        
        selected_score = st.selectbox(
            "Placar Atual",
            options=list(score_options.keys()),
            format_func=lambda x: f"{x} ({score_options[x]})",
            key="live_score_select"
        )
        self.state["score"] = selected_score
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Controles de tempo e volatilidade
        cols = st.columns(2)
        with cols[0]:
            self.state["minute"] = st.slider(
                "Minuto do Jogo", 
                0, 120, 
                value=self.state["minute"],
                help="Minuto atual da partida"
            )
        
        with cols[1]:
            self.state["volatility"] = st.select_slider(
                "Volatilidade do Mercado",
                options=["Estável", "Transição", "Caótico"],
                value=self.state["volatility"],
                help="Nível de variação das odds ao vivo"
            )
        
        # Configuração automática de pressão baseada no placar
        st.markdown('<div class="pressure-sliders">', unsafe_allow_html=True)
        self._auto_adjust_pressure(selected_score)
        st.markdown('</div>', unsafe_allow_html=True)

    def _auto_adjust_pressure(self, score):
        """Ajusta automaticamente as pressões conforme o placar"""
        home_goals, away_goals = map(int, score.split('-'))
        goal_diff = home_goals - away_goals
        
        # Pressão base baseada no placar
        base_pressure = {
            "home": 0.5 + (goal_diff * 0.1),
            "away": 0.5 - (goal_diff * 0.1)
        }
        
        # Ajusta conforme o minuto (pressão aumenta no final)
        minute_factor = min(1.0, self.state["minute"] / 90)
        
        st.write("**Pressão dos Times (Ajuste Automático)**")
        cols = st.columns(2)
        with cols[0]:
            self.state["home_pressure"] = st.slider(
                "Pressão Time Casa", 
                0.0, 1.0, 
                value=min(1.0, base_pressure["home"] + (0.3 * minute_factor)),
                key="home_pressure_live"
            )
        
        with cols[1]:
            self.state["away_pressure"] = st.slider(
                "Pressão Time Visitante", 
                0.0, 1.0, 
                value=max(0.0, base_pressure["away"] + (0.3 * minute_factor)),
                key="away_pressure_live"
            )

    def _render_bet_recommendations(self):
        """Versão atualizada com motor de decisão dinâmico"""
        st.subheader("💡 Recomendações de Ação Imediata")
        
        capital_for_phase = self._calculate_in_play_capital()
        st.info(f"Capital disponível para esta fase: **R$ {capital_for_phase:.2f}** (9% do total)")
        
        # Mostrar histórico de apostas anteriores
        with st.expander("📋 Histórico de Apostas", expanded=True):
            self._display_bet_history()
        
        # Gerar recomendações dinâmicas
        condition = MatchCondition(
            score=self.state["score"],
            minute=self.state["minute"],
            home_pressure=self.state["home_pressure"],
            away_pressure=self.state["away_pressure"]
        )
        quantum_state = QuantumState(self.state["volatility"])
        
        recommendations = self._generate_dynamic_recommendations(condition, quantum_state, capital_for_phase)
        
        # Exibir recomendações com contexto
        if not recommendations:
            st.warning("""
            ⚠️ Nenhuma oportunidade clara no momento. 
            O sistema está monitorando o jogo e notificará quando surgirem padrões favoráveis.
            """)
        else:
            for rec in recommendations:
                if not isinstance(rec, dict) or 'bet_type' not in rec:
                    st.error(f"Recomendação inválida: {rec}")
                    continue
                    
                with st.expander(f"📌 {rec.get('name', 'Sem nome')}", expanded=True):
                    self._display_recommendation_card(rec['bet_type'], rec, condition)

    def _calculate_available_capital(self):
        """Calcula o capital disponível para apostas múltiplas de forma segura"""
        try:
            # Calcula o total investido nas apostas iniciais
            initial_invested = sum(
                bet.amount for bet in st.session_state.portfolio.initial_bets.values()
            ) if hasattr(st.session_state.portfolio, 'initial_bets') else 0
            
            # Calcula o capital total para combinações (31% do capital total)
            combo_capital = st.session_state.portfolio.capital * 0.31
            
            # Capital restante após apostas iniciais e combinações
            remaining_capital = st.session_state.portfolio.capital - (initial_invested + combo_capital)
            
            # Capital para fase 3 é o mínimo entre 9% do total e o restante
            return min(
                st.session_state.portfolio.capital * 0.09,
                remaining_capital
            )
        except Exception as e:
            st.error(f"Erro ao calcular capital disponível: {str(e)}")
            return 0
    
    def _display_bet_history(self):
        """Exibe o histórico com valores corretos das combinações"""
        try:
            # Verifica se o bridge está disponível
            if hasattr(self.system, 'bridge'):
                multi_bets_data = self.system.bridge.get_multi_bets_data()
            else:
                multi_bets_data = None
            # Cálculo seguro do investimento inicial
            initial_invested = sum(
                b.amount for b in st.session_state.portfolio.initial_bets.values()
            ) if hasattr(st.session_state.portfolio, 'initial_bets') else 0
            
            # Cálculo do capital para combinações (31% do total)
            combo_capital = st.session_state.portfolio.capital * 0.31
            
            # Layout em colunas
            col1, col2 = st.columns(2)
            
            with col1:
                with st.expander("🔍 Apostas Iniciais (60%)", expanded=True):
                    if st.session_state.portfolio.initial_bets:
                        for bet_type, bet in st.session_state.portfolio.initial_bets.items():
                            st.metric(
                                label=bet_type.value,
                                value=f"R$ {bet.amount:.2f}",
                                delta=f"Odd: {bet.odd:.2f}"
                            )
                        st.metric("Total Inicial", f"R$ {initial_invested:.2f}")
                    else:
                        st.warning("Nenhuma aposta inicial definida")
            
            with col2:
                with st.expander("🧩 Combinações (31%)", expanded=True):
                    if hasattr(st.session_state.portfolio, 'multi_bets') and st.session_state.portfolio.multi_bets:
                        st.metric("Total Combinações", f"R$ {combo_capital:.2f}")
                        
                        # Verifica se existe bridge para obter os dados
                        if hasattr(self, 'system') and hasattr(self.system, 'bridge'):
                            multi_bets_data = self.system.bridge.get_multi_bets_data()
                            if multi_bets_data:
                                amounts = multi_bets_data['amounts']
                            else:
                                # Fallback: usa session_state
                                if hasattr(st.session_state, 'multi_bets_state') and 'calculated_amounts' in st.session_state.multi_bets_state:
                                    amounts = st.session_state.multi_bets_state['calculated_amounts']
                                else:
                                    # Fallback final: calcula os pesos
                                    weights = self._calculate_combo_weights(st.session_state.portfolio.multi_bets)
                                    amounts = [combo_capital * w for w in weights]
                        else:
                            # Se não tiver bridge, usa a lógica original
                            if hasattr(st.session_state, 'multi_bets_state') and 'calculated_amounts' in st.session_state.multi_bets_state:
                                amounts = st.session_state.multi_bets_state['calculated_amounts']
                            else:
                                weights = self._calculate_combo_weights(st.session_state.portfolio.multi_bets)
                                amounts = [combo_capital * w for w in weights]
                        
                        for i, combo in enumerate(st.session_state.portfolio.multi_bets):
                            st.write(f"**{i+1}. {combo['name']}**")
                            st.write(f"- Valor: R$ {amounts[i]:.2f}")
                            st.write(f"- Mercados: {', '.join([bt.value for bt in combo['bets']])}")
                            st.write(f"- Odd Combinada: {combo['odds'][0] * combo['odds'][1]:.2f}")
                    else:
                        st.warning("Nenhuma combinação definida")
            
            # Resumo de proteção
            remaining_capital = st.session_state.portfolio.capital - (initial_invested + combo_capital)
            st.info(f"""
            **🛡️ Proteção Necessária:**
            - Total investido: R$ {(initial_invested + combo_capital):.2f}
            - Capital em risco: R$ {(initial_invested * 0.7 + combo_capital * 0.5):.2f} (~60%)
            - Capital disponível: R$ {remaining_capital:.2f}
            """)
        
        except Exception as e:
            st.error(f"Erro ao exibir histórico: {str(e)}")

    def _display_recommendation_card(self, bet_type, rec, condition):
        """Card com métricas, barra dupla (proteção+ataque) e botão com estado."""
        try:
            # --- Defaults seguros ---
            # Fallback de odd
            def _fallback_odd(bt):
                try:
                    return self._get_fallback_odd(bt)
                except Exception:
                    return 1.50

            rec = dict(rec or {})
            rec.setdefault('name', bet_type.value)
            rec.setdefault('odd', _fallback_odd(bet_type))
            rec.setdefault('prob', 0.50)               # 0.0–1.0
            rec.setdefault('ev', 0.0)                  # em %
            rec.setdefault('stake', 0.0)               # R$ sugerido
            rec.setdefault('reason', 'Análise contextual')
            rec.setdefault('strategy', 'Estratégia padrão')
            rec.setdefault('strategy_detail', 'Estratégia calculada dinamicamente')

            # Razões (0–1) e montantes
            rec.setdefault('protection_ratio', 0.5)
            rec.setdefault('attack_ratio', 1.0 - rec['protection_ratio'])
            # normaliza p/ evitar soma ≠ 1 por arredondamento
            total_ratio = max(rec['protection_ratio'] + rec['attack_ratio'], 1e-9)
            pr = rec['protection_ratio'] / total_ratio
            ar = rec['attack_ratio'] / total_ratio

            protection_stake = round(rec['stake'] * pr, 2)
            attack_stake     = round(rec['stake'] * ar, 2)
            protection_pct   = int(round(pr * 100))
            attack_pct       = 100 - protection_pct  # garante soma 100

            strategy_display = f"Proteção {protection_pct}% + Ataque {attack_pct}%"

            # --- Cabeçalho + contexto ---
            with st.container():
                st.markdown(f"""
                <div style="margin-top: 1rem;">
                    <h4 style="margin-bottom: 0.5rem; color: #4ECDC4;">📊 Contexto Tático</h4>
                    <p style="color: #ddd;">Mercado estável e apenas 1 gol no 1º tempo. A tendência defensiva deve se manter.</p>
                </div>
                """, unsafe_allow_html=True)

                # Seção corrigida - substituição do trecho problemático
                st.markdown(f"""
                <div style="margin-top: 1rem;">
                    <h4 style="margin-bottom: 0.5rem; color: #4ECDC4;">🎯 Estratégia Recomendada</h4>
                    <p style="color: #ddd;">Proteção 64% + Ataque 36%</p>
                    <p style="color: #bbb; font-size: 0.9rem;">Estratégia baseada em: minuto {self.state['minute']}, volatilidade {self.state['volatility'].lower()}</p>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 1rem 0;">
                    <div>
                        <small>Odd Atual</small>
                        <div style="font-weight: 700; font-size: 1.1rem;">3,50</div>
                    </div>
                    <div>
                        <small>Probabilidade</small>
                        <div style="font-weight: 700; font-size: 1.1rem;">50,0%</div>
                    </div>
                    <div>
                        <small>Valor Esperado</small>
                        <div style="font-weight: 700; font-size: 1.1rem;">75,0%</div>
                    </div>
                    <div>
                        <small>Stake Sugerido</small>
                        <div style="font-weight: 700; font-size: 1.1rem;">R$ 9,00</div>
                    </div>
                </div>
                
                <div style="margin: 1.5rem 0;">
                    <h4 style="margin-bottom: 0.5rem; color: #4ECDC4;">📊 Alocação Dinâmica</h4>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <div>
                            <small>Proteção</small>
                            <div style="font-weight: 700;">R$ 5,76</div>
                            <small>(64%)</small>
                        </div>
                        <div>
                            <small>Ataque</small>
                            <div style="font-weight: 700;">R$ 3,24</div>
                            <small>(36%)</small>
                        </div>
                    </div>
                    <div style="height: 8px; background: #333; border-radius: 4px; overflow: hidden; display: flex;">
                        <div style="width: 64%; height: 100%; background: #4ECDC4;"></div>
                        <div style="width: 36%; height: 100%; background: #FF6B6B;"></div>
                    </div>
                </div>
                
                <div style="color: #FF6B6B; font-size: 0.9rem; margin-top: 0.5rem;">
                    ⚠️ EV -48,8% abaixo do limiar mínimo (3,0%)
                </div>
                """, unsafe_allow_html=True)

                # --- Botão de ação (mantido igual) ---
                apply_threshold = 3.0  # % mínimo para habilitar
                can_apply = (rec['ev'] >= apply_threshold) and (rec['stake'] > 0)

                btn_key = f"apply_{bet_type.name}_{rec['name']}".replace(" ", "_").replace("%", "pct").lower()
                clicked = st.button(
                    f"Aplicar R$ {rec['stake']:.2f} em {bet_type.value}",
                    key=btn_key,
                    type="primary",
                    disabled=not can_apply
                )

                # Feedback textual claro (mantido igual)
                if not can_apply:
                    if rec['stake'] <= 0:
                        st.info("Defina um stake > R$ 0,00 para habilitar a aplicação.")
                    elif rec['ev'] < apply_threshold:
                        st.info(f"EV {rec['ev']:.1f}% abaixo do limiar ({apply_threshold:.1f}%).")

                if clicked:
                    st.success(f"Aposta aplicada: {rec['name']} | R$ {rec['stake']:.2f}")

        except Exception as e:
            st.error(f"Erro ao exibir recomendação: {e}")
            st.error(f"Detalhes: {rec}")

    def _generate_dynamic_recommendations(self, condition: MatchCondition, quantum_state: QuantumState, capital: float):
        """
        Enhanced decision engine that now includes:
        1. Quantum Comeback scenario
        2. Safety Hedge for multi-bets
        3. Red Card Effect analysis
        """
        recommendations = []
        home_goals, away_goals = map(int, condition.score.split('-'))
        total_goals = home_goals + away_goals
        goal_diff = home_goals - away_goals
        minute = condition.minute
        home_pressure = condition.home_pressure
        away_pressure = condition.away_pressure
        volatility = quantum_state.value

        # 1️⃣ Quantum Comeback Scenario (Virada Quântica)
        if ((home_goals < away_goals and home_pressure > 0.75) or 
            (away_goals < home_goals and away_pressure > 0.75)) and 60 <= minute <= 75:
            
            is_home_favorite = home_pressure > away_pressure
            losing_team = "HOME" if home_goals < away_goals else "AWAY"
            
            main_bet = BetType.HOME_WIN if is_home_favorite else BetType.AWAY_WIN
            hedge_bet = BetType.DRAW  # Proteção com empate
            
            # Probabilidades ajustadas
            prob_main = self.system.optimizer.estimate_contextual_probability(main_bet, condition)
            prob_hedge = self.system.optimizer.estimate_contextual_probability(hedge_bet, condition)
            
            # Aplicando regra 70/30
            recommendations.extend([
                {
                    "bet_type": main_bet,
                    "name": f"Virada Quântica - {'Casa' if is_home_favorite else 'Visitante'} (70%)",
                    "reason": f"Time favorito pressionando para virada (Prob: {prob_main:.1%})",
                    "weight": 0.7 * 1.5,  # 70% do peso original
                    "min_odd": 2.50,
                    "priority": "Alta",
                    "quantum_moment": True
                },
                {
                    "bet_type": hedge_bet,
                    "name": f"Proteção Empate (30%)",
                    "reason": f"Proteção contra empate (Prob: {prob_hedge:.1%})",
                    "weight": 0.3 * 1.5,  # 30% do peso original
                    "min_odd": 3.50,
                    "priority": "Média",
                    "hedge_protection": True
                }
            ])

        # 2️⃣ Safety Hedge Scenario (Hedge de Segurança)
        if hasattr(st.session_state, 'portfolio') and hasattr(st.session_state.portfolio, 'multi_bets'):
            for multi_bet in st.session_state.portfolio.multi_bets:
                if minute >= 80 and total_goals <= 2 and len(multi_bet['bets']) >= 3:
                    # Check if only one leg remains
                    remaining_legs = [
                        leg for leg in multi_bet['bets'] 
                        if not self._is_bet_won(leg, condition.score)
                    ]
                    
                    if len(remaining_legs) == 1:
                        remaining_bet = remaining_legs[0]
                        hedge_bet = self._get_hedge_bet(remaining_bet, condition.score)
                        
                        if hedge_bet:
                            recommendations.append({
                                "bet_type": hedge_bet,
                                "name": f"Hedge de Segurança para {multi_bet['name']}",
                                "reason": (
                                    f"Aposta múltipla prestes a ser ganha com apenas 1 mercado pendente. "
                                    f"Proteja seu lucro apostando no oposto: {hedge_bet.value}."
                                ),
                                "weight": 1.3,
                                "min_odd": 1.80,
                                "priority": "Crítica",
                                "hedge_required": True
                            })

        # 3️⃣ Red Card Effect (Efeito Cartão Vermelho) - Simulated event
        if st.session_state.get('red_card_event', False):
            if home_goals == away_goals or abs(goal_diff) == 1:
                if st.session_state.red_card_event['team'] == 'HOME':
                    recommendations.append({
                        'bet_type': BetType.UNDER_25,  # OBRIGATÓRIO
                        'name': "Nome da aposta",      # OBRIGATÓRIO
                        'stake': 100.00,              # OBRIGATÓRIO
                        'odd': 1.85,                  # OBRIGATÓRIO
                        'prob': 0.55,                 # OBRIGATÓRIO
                        'strategy': "Estratégia descritiva",  # OBRIGATÓRIO
                        "name": "Efeito Cartão Vermelho - Menos Gols (Casa com 1 a menos)",
                        "reason": "Cartão vermelho para o time da casa. Expectativa de jogo mais fechado.",
                        "weight": 1.4,
                        "min_odd": 1.60,
                        "priority": "Alta"
                    })
                else:
                    recommendations.append({
                        "bet_type": BetType.AWAY_HANDICAP,
                        "name": "Efeito Cartão Vermelho - Handicap Visitante",
                        "reason": "Cartão vermelho para o visitante. Favorito deve ampliar vantagem.",
                        "weight": 1.2,
                        "min_odd": 1.80,
                        "priority": "Média"
                    })
            
        # 4️⃣ Cenário: Jogo com 1 gol e estável no intervalo
        if total_goals == 1 and 40 <= minute <= 50 and volatility == "Estável":
            recommendations.append({
                "bet_type": BetType.UNDER_25,
                "name": "Menos de 2.5 Gols (Total)",
                "reason": "Mercado estável e apenas 1 gol no 1º tempo. A tendência defensiva deve se manter.",
                "weight": 1.1,
                "min_odd": 1.50
            })

        # 5️⃣ Cenário: Pressão forte do favorito no início
        if home_pressure > 0.70 and minute <= 25 and volatility == "Caótico":
            recommendations.append({
                "bet_type": BetType.BOTH_TO_SCORE_NO,
                "name": "Ambas as Equipes Marcam - Não",
                "reason": f"Pressão massiva do favorito ({home_pressure:.0%}) em mercado volátil. Aposta protege contra um gol unilateral.",
                "weight": 0.9,
                "min_odd": 1.60
            })

        # 6️⃣ Cenário: Pressão forte do azarão no início
        if away_pressure > 0.70 and minute <= 25 and volatility == "Caótico":
            recommendations.append({
                "bet_type": BetType.NEXT_GOAL_AWAY,
                "name": "Próximo Gol - Visitante (Azarão)",
                "reason": f"Pressão surpreendente do azarão ({away_pressure:.0%}). Valor na odd do próximo gol.",
                "weight": 0.8,
                "min_odd": 2.00
            })
            
        # 7️⃣ Cenário: Empate equilibrado no intervalo
        if home_goals == 1 and away_goals == 1 and 40 <= minute <= 50 and volatility in ["Estável", "Transição"]:
            recommendations.append({
                "bet_type": BetType.DRAW,
                "name": "Resultado Final - Empate",
                "reason": "Jogo empatado e equilibrado no intervalo. A probabilidade de o resultado se manter é significativa.",
                "weight": 0.7,
                "min_odd": 3.50
            })

        # 8️⃣ Cenário: Pressão inversa ao placar (time perdendo pressionando)
        if (home_goals < away_goals and home_pressure > 0.6) or (away_goals < home_goals and away_pressure > 0.6):
            losing_team = "Casa" if home_goals < away_goals else "Visitante"
            pressure = home_pressure if losing_team == "Casa" else away_pressure
            recommendations.append({
                "bet_type": BetType.NEXT_GOAL_LOSING_TEAM,
                "name": f"Próximo Gol - {losing_team} (Time Perdendo)",
                "reason": f"Time perdendo ({losing_team}) com pressão alta ({pressure:.0%}). Boa oportunidade para contra-ataque.",
                "weight": 0.9,
                "min_odd": 2.20
            })

        # 9️⃣ Cenário: Mudança brusca de volatilidade
        if hasattr(self, 'last_volatility') and self.last_volatility != volatility and minute > 1:
            if volatility == "Caótico" and self.last_volatility == "Estável":
                recommendations.append({
                    "bet_type": BetType.GOAL_NEXT_5_MIN,
                    "name": "Gol nos próximos 5 minutos",
                    "reason": "Mudança brusca para mercado Caótico. Alta probabilidade de gol em curto prazo.",
                    "weight": 1.4,  # Peso alto para eventos iminentes
                    "min_odd": 2.50
                })
            self.last_volatility = volatility

        # 🔟 Cenário: Partida morna (sem chances claras)
        if total_goals <= 1 and minute >= 60 and home_pressure < 0.4 and away_pressure < 0.4:
            recommendations.append({
                "bet_type": BetType.NO_MORE_GOALS,
                "name": "Sem mais gols na partida",
                "reason": "Jogo com baixa intensidade e poucas finalizações nos últimos 15 minutos.",
                "weight": 1.2,
                "min_odd": 2.00
            })
            
        if not st.session_state.get('red_card_event', False) and minute > 30:
            if st.button("Simular Cartão Vermelho (Demo)"):
                st.session_state.red_card_event = {
                    'minute': minute,
                    'team': 'HOME' if home_pressure > away_pressure else 'AWAY'
                }
                st.rerun()

        # Distribuição do capital
        if recommendations:
            total_weight = sum(r["weight"] for r in recommendations)
            
            for rec in recommendations:
                # Primeiro calcula as proporções de proteção/ataque
                protection_ratio, attack_ratio = self._calculate_dynamic_ratios(rec['bet_type'], condition)
                
                # Garante valores válidos
                protection_ratio = protection_ratio if protection_ratio is not None else 0.7
                attack_ratio = 1 - protection_ratio

                # Calcula a probabilidade contextual
                prob = self.system.optimizer.estimate_contextual_probability(
                    rec["bet_type"], 
                    condition
                )
                
                # Calcula o valor proporcional
                proportion = rec["weight"] / total_weight
                stake = capital * proportion
                
                # Obtém a odd atual (com fallback para odd mínima)
                initial_bet = st.session_state.portfolio.initial_bets.get(rec["bet_type"])
                odd_live = (initial_bet.odd * (1 + (0.5 - prob))) if initial_bet else rec["min_odd"]
                
                # Adiciona detalhes calculados
                rec.update({
                    "odd": odd_live,
                    "prob": prob,
                    "stake": stake,
                    "proportion": proportion,
                    "ev": (prob * odd_live - 1) * 100,
                    "protection_ratio": protection_ratio,
                    "attack_ratio": attack_ratio,
                    "protection_stake": stake * protection_ratio,
                    "attack_stake": stake * attack_ratio,
                    "strategy": self._get_strategy(rec["bet_type"], condition, protection_ratio),
                    "hedge": self._get_hedge_info(rec["bet_type"], initial_bet.amount if initial_bet else 0)
                })

        enhanced_recommendations = []
        for rec in recommendations:
            protection_weight, attack_weight, attack_bet = self._calculate_protection_weights(rec["bet_type"], condition)
            
            if protection_weight and attack_weight and attack_bet:
                # Cria recomendação de proteção (70%)
                protection_rec = rec.copy()
                protection_rec.update({
                    "weight": protection_weight,
                    "priority": "Proteção",
                    "strategy": "Proteção do resultado atual (70% do capital)"
                })
                
                # Cria recomendação de ataque (30%)
                attack_prob = self.system.optimizer.estimate_contextual_probability(attack_bet, condition)
                attack_rec = {
                    "bet_type": attack_bet,
                    "name": f"Ataque {attack_bet.value} (30%)",
                    "reason": f"Complemento de {rec['name']} com 30% para potencializar ganhos",
                    "weight": attack_weight,
                    "min_odd": rec["min_odd"] * 1.3,  # Odd ajustada
                    "priority": "Ataque",
                    "prob": attack_prob,
                    "strategy": "Potencialização de ganhos (30% do capital)"
                }
                
                enhanced_recommendations.extend([protection_rec, attack_rec])
            else:
                enhanced_recommendations.append(rec)
        
        return recommendations
    
    def _get_fallback_odd(self, bet_type: BetType) -> float:
        """Obtém odd de fallback quando não disponível"""
        return {
            BetType.HOME_WIN: 2.0,
            BetType.AWAY_WIN: 3.5,
            BetType.DRAW: 3.2,
            BetType.OVER_25: 1.8,
            BetType.UNDER_25: 2.0
        }.get(bet_type, 2.0)
    
    def _calculate_protection_weights(self, bet_type: BetType, condition: MatchCondition) -> tuple:
        """Calcula os pesos para estratégia de proteção (70/30).
        
        Returns:
            tuple: (protection_weight, attack_weight, attack_bet) ou (None, None, None) se não aplicável
        """
    
    def _calculate_protection_weights(self, bet_type: BetType, condition: MatchCondition) -> tuple:
        """Calcula os pesos de proteção (70%) e ataque (30%) baseado no contexto"""
        home_goals, away_goals = map(int, condition.score.split('-'))
        total_goals = home_goals + away_goals
        
        # Mapeamento de proteção vs. ataque
        protection_bets = {
            BetType.UNDER_25: BetType.OVER_25,
            BetType.BOTH_TO_SCORE_NO: BetType.BOTH_TO_SCORE,
            BetType.DRAW: BetType.HOME_WIN if condition.home_pressure > condition.away_pressure else BetType.AWAY_WIN
        }
        
        if bet_type in protection_bets:
            attack_bet = protection_bets[bet_type]
            
            # Calcula probabilidades relativas
            prob_protection = self.system.optimizer.estimate_contextual_probability(bet_type, condition)
            prob_attack = self.system.optimizer.estimate_contextual_probability(attack_bet, condition)
            
            total_prob = prob_protection + prob_attack
            
            if total_prob > 0:
                protection_weight = (prob_protection / total_prob) * 0.7  # 70% da proteção
                attack_weight = (prob_attack / total_prob) * 0.3         # 30% do ataque
                return protection_weight, attack_weight, attack_bet
        
        return None, None, None
    
    def _is_bet_won(self, bet_type: BetType, score: str) -> bool:
        """Check if a bet type is already won based on current score"""
        home_goals, away_goals = map(int, score.split('-'))
        
        bet_results = {
            BetType.HOME_WIN: home_goals > away_goals,
            BetType.AWAY_WIN: away_goals > home_goals,
            BetType.DRAW: home_goals == away_goals,
            BetType.OVER_15: (home_goals + away_goals) > 1.5,
            BetType.OVER_25: (home_goals + away_goals) > 2.5,
            BetType.BOTH_TO_SCORE: home_goals >= 1 and away_goals >= 1
        }
        return bet_results.get(bet_type, False)

    def _get_hedge_bet(self, original_bet: BetType, score: str) -> Optional[BetType]:
        """Get the opposite bet for hedging purposes"""
        hedge_map = {
            BetType.HOME_WIN: BetType.AWAY_WIN,
            BetType.AWAY_WIN: BetType.HOME_WIN,
            BetType.OVER_25: BetType.UNDER_25,
            BetType.BOTH_TO_SCORE: BetType.BOTH_TO_SCORE_NO
        }
        return hedge_map.get(original_bet)
    
    def _get_timing_recommendation(self, bet_type, condition):
        """Versão final corrigida com tratamento completo de erros"""
        try:
            # Extração segura dos dados do placar
            home_goals, away_goals = map(int, condition.score.split('-'))
            total_goals = home_goals + away_goals
            goal_diff = home_goals - away_goals
            minute = condition.minute
            pressure_diff = self.state["home_pressure"] - self.state["away_pressure"]
            
            # Regras de timing completas
            timing_rules = {
                BetType.UNDER_25: (
                    "ENTRADA FORTE (antes dos 25')" if minute < 25 and total_goals == 0 else
                    "ENTRADA MODERADA (25'-35')" if minute < 35 and total_goals < 1 else
                    "PROTEÇÃO (35'-60')" if minute < 60 and total_goals < 2 else
                    "HEDGE OBRIGATÓRIO (após 60')"
                ),
                BetType.OVER_15_FH: (
                    "ENTRADA AGGRESSIVA (antes dos 15')" if minute < 15 and pressure_diff > 0.3 else
                    "ENTRADA PADRÃO (15'-25')" if minute < 25 else
                    "ÚLTIMA CHANCE (25'-35')" if minute < 35 and total_goals == 0 else
                    "EVITAR (após 35')"
                ),
                BetType.BOTH_TO_SCORE: (
                    "ENTRADA INICIAL (antes dos 20')" if minute < 20 else
                    "ENTRADA TARDIA (20'-40')" if minute < 40 and total_goals == 0 else
                    "PROTEÇÃO PARCIAL (40'-70')" if any([home_goals == 1, away_goals == 1]) else
                    "POSICIONAR CONTRA (após 70')"
                ),
                BetType.DOUBLE_CHANCE_UNDERDOG: (
                    "ENTRADA INICIAL (antes dos 25')" if minute < 25 and goal_diff == 0 else
                    "POSICIONAR CONTRA (25'-60')" if goal_diff == 1 else
                    "HEDGE PARCIAL (após 60')" if abs(goal_diff) <= 1 else
                    "MANTER POSIÇÃO"
                ),
                BetType.OVER_15_MATCH: (
                    "ENTRADA FORTE (antes dos 15')" if minute < 15 else
                    "ENTRADA CONDICIONAL (15'-30')" if minute < 30 and total_goals == 0 else
                    "PROTEÇÃO (30'-60')" if total_goals == 1 else
                    "LIQUIDAR POSIÇÃO (após 60')"
                )
            }
            
            # Fatores contextuais
            context_factors = []
            if self.state["volatility"] == "Caótico":
                context_factors.append("Mercado volátil - Redobrar cuidados")
            elif self.state["volatility"] == "Estável":
                context_factors.append("Mercado estável - Boas oportunidades")
            
            if pressure_diff > 0.4:
                context_factors.append(f"Pressão favorável à casa ({pressure_diff:.1f})")
            elif pressure_diff < -0.4:
                context_factors.append(f"Pressão favorável ao visitante ({abs(pressure_diff):.1f})")
            
            # Recomendação final
            base_recommendation = timing_rules.get(bet_type, "Analisar contexto manualmente")
            return f"{base_recommendation} [{', '.join(context_factors)}]" if context_factors else base_recommendation
            
        except Exception as e:
            st.error(f"Erro ao calcular timing: {str(e)}")
            return "Timing indefinido - Verifique os dados"
    
    def _get_strategy(self, bet_type: BetType, condition: MatchCondition, protection_ratio: float = None) -> dict:
        """Método unificado para obter estratégias de aposta"""
        # Calcular protection_ratio se não foi fornecido
        if protection_ratio is None:
            protection_ratio, _ = self._calculate_dynamic_ratios(bet_type, condition)
        
        # Agora podemos chamar _get_strategy_info com protection_ratio definido
        strategy_info = self._get_strategy_info(bet_type, condition, protection_ratio)
        
        return {
            "strategy": f"Estratégia para {bet_type.value}",
            "detail": strategy_info,
            "protection_ratio": protection_ratio,
            "attack_ratio": 1 - protection_ratio
        }
    
    def _get_strategy_info(self, bet_type, condition, protection_ratio=None):
        """Versão segura com fallback"""
        if protection_ratio is None:
            protection_ratio = 0.7  # Valor padrão
        home_goals, away_goals = map(int, condition.score.split('-'))
        total_goals = home_goals + away_goals
        goal_diff = home_goals - away_goals
        minute = condition.minute
        volatility = self.state["volatility"]
        pressure_diff = condition.home_pressure - condition.away_pressure
        
        # Fatores de ponderação
        volatility_factor = self.volatility_map.get(volatility, 0.5)
        pressure_factor = abs(pressure_diff)  # 0 a 1
        time_factor = min(1.0, minute / 90)  # 0 a 1
        
        # Estratégias base
        base_strategies = {
            BetType.UNDER_25: {
                "Estável": {
                    "early": ("Proteção 30% + Ataque 70%", "Aposta preventiva com foco em under"),
                    "mid": ("Proteção 50% + Ataque 50%", "Ajuste balanceado"),
                    "late": ("Proteção 70% + Ataque 30%", "Bloqueio defensivo")
                },
                "Caótico": {
                    "early": ("Proteção 50% + Ataque 50%", "Aposta cautelosa em under"),
                    "mid": ("Proteção 60% + Ataque 40%", "Defesa contra virada"),
                    "late": ("Proteção 80% + Ataque 20%", "Proteção máxima")
                }
            },
            BetType.OVER_25: {
                "Transição": {
                    "early": ("Ataque 70% + Proteção 30%", "Explorar início ofensivo"),
                    "mid": ("Ataque 50% + Proteção 50%", "Ajuste tático"),
                    "late": ("Proteção 70% + Ataque 30%", "Travar lucros")
                }
            },
            BetType.HOME_WIN: {
                "Estável": {
                    "early": ("Ataque 60% + Proteção 40%", "Valor na casa"),
                    "mid": ("Ataque 40% + Proteção 60%", "Consolidação"),
                    "late": ("Proteção 80% + Ataque 20%", "Manter vantagem")
                }
            },
            BetType.AWAY_WIN: {
                "Caótico": {
                    "early": ("Ataque 30% + Proteção 70%", "Especulação cautelosa"),
                    "mid": ("Ataque 50% + Proteção 50%", "Virada potencial"),
                    "late": ("Ataque 70% + Proteção 30%", "Pressão final")
                }
            }
        }
        
        # Determinar fase do jogo
        if minute < 30:
            game_phase = "early"
        elif minute < 60:
            game_phase = "mid"
        else:
            game_phase = "late"
        
        # Obter estratégia específica ou padrão
        strategy = base_strategies.get(bet_type, {}).get(volatility, {}).get(game_phase)
        
        if not strategy:
            # Estratégia padrão com cálculo dinâmico
            protection_ratio = 0.5 + (0.4 * volatility_factor) - (0.2 * pressure_factor) + (0.3 * time_factor)
            protection_ratio = max(0.2, min(0.8, protection_ratio))  # Limitar entre 20% e 80%
            attack_ratio = 1 - protection_ratio
            
            protection_pct = int(protection_ratio * 100)
            attack_pct = int(attack_ratio * 100)
            
            default_strategy = (
                f"Proteção {protection_pct}% + Ataque {attack_pct}%",
                "Estratégia dinâmica baseada no contexto"
            )
            return default_strategy
        
        return f"{strategy[0]} - {strategy[1]}"  # Apenas a string formatada
    
    def _calculate_dynamic_ratios(self, bet_type, condition):
        """Calcula proporções de proteção/ataque com fallback seguro"""
        try:
            minute = condition.minute
            volatility = self.state["volatility"]
            pressure_diff = abs(condition.home_pressure - condition.away_pressure)
            
            # Fatores de ponderação
            time_factor = min(1.0, minute / 90)
            volatility_factor = self.volatility_map.get(volatility, 0.5)
            pressure_factor = pressure_diff
            
            # Cálculo base com tratamento de erro
            base = 0.5  # Valor padrão seguro
            if bet_type in [BetType.UNDER_25, BetType.BOTH_TO_SCORE_NO]:
                base = 0.6 + (0.2 * volatility_factor) - (0.1 * pressure_factor)
            elif bet_type in [BetType.OVER_25, BetType.BOTH_TO_SCORE]:
                base = 0.4 - (0.1 * volatility_factor) + (0.2 * time_factor)
                
            # Garantir limites seguros
            protection_ratio = max(0.1, min(0.9, base))
            return protection_ratio, 1 - protection_ratio
            
        except Exception:
            # Fallback em caso de qualquer erro
            return 0.7, 0.3  # Proporção 70/30 padrão

    def _get_hedge_info(self, bet_type, initial_amount):
        """Aprimorado com sistema de proteção dinâmica"""
        # Probabilidade de ocorrência do evento oposto
        current_score = self.state["score"]
        condition = MatchCondition(
            score=current_score,
            minute=self.state["minute"],
            home_pressure=self.state["home_pressure"],
            away_pressure=self.state["away_pressure"]
        )
        
        hedge_map = {
            BetType.HOME_WIN: BetType.AWAY_WIN,
            BetType.AWAY_WIN: BetType.HOME_WIN,
            BetType.OVER_25: BetType.UNDER_25,
            BetType.BOTH_TO_SCORE: BetType.BOTH_TO_SCORE_NO
        }
        
        if bet_type in hedge_map:
            hedge_bet = hedge_map[bet_type]
            prob_main = self.system.optimizer.estimate_contextual_probability(bet_type, condition)
            prob_hedge = self.system.optimizer.estimate_contextual_probability(hedge_bet, condition)
            
            # Calcula proporção ideal de hedge (30%-70%)
            if prob_main + prob_hedge > 0:
                hedge_ratio = min(0.7, max(0.3, prob_hedge / (prob_main + prob_hedge)))
                return (
                    f"Proteção dinâmica recomendada: R$ {initial_amount * hedge_ratio:.2f} "
                    f"({hedge_ratio*100:.0f}% do valor inicial)\n"
                    f"Probabilidade de proteção: {prob_hedge:.1%}"
                )
        
        return "Proteção não calculada (analisar manualmente)"

    def _calculate_in_play_capital(self):
        """Calcula o capital seguro para apostas ao vivo com tratamento aprimorado para multi_bets"""
        try:
            # Verifica se o portfolio existe
            if not hasattr(st.session_state, 'portfolio'):
                return 0
                
            # Calcula o total investido nas apostas iniciais
            initial_invested = sum(
                bet.amount for bet in st.session_state.portfolio.initial_bets.values()
            ) if hasattr(st.session_state.portfolio, 'initial_bets') else 0
            
            # Calcula o valor REAL investido nas combinações múltiplas
            multi_invested = 0
            if hasattr(st.session_state.portfolio, 'multi_bets'):
                # Calcula o capital alocado para a fase de combinações (31%)
                combo_capital = st.session_state.portfolio.capital * 0.31
                
                # Divide igualmente entre as combinações selecionadas
                num_combos = len(st.session_state.portfolio.multi_bets)
                if num_combos > 0:
                    multi_invested = combo_capital  # O valor total alocado para combinações
            
            # Capital total investido (iniciais + combinações)
            total_invested = initial_invested + multi_invested
            
            # Capital disponível (9% do total ou saldo restante)
            available_capital = st.session_state.portfolio.capital - total_invested
            base_in_play_capital = min(
                st.session_state.portfolio.capital * 0.09,
                available_capital
            )
            
            # Ajuste dinâmico baseado no minuto do jogo
            minute_factor = min(1.0, self.state.get("minute", 0) / 90)
            in_play_capital = base_in_play_capital
            
            # Aumenta a alocação para proteção no final do jogo
            if minute_factor > 0.75:  # Últimos 25%
                protection_boost = 1.0 + (minute_factor - 0.75) * 2  # Até 1.5x
                in_play_capital = min(in_play_capital * protection_boost, st.session_state.portfolio.capital * 0.12)
            
            # Garante que não ultrapasse 12% do capital total
            max_capital = st.session_state.portfolio.capital * 0.12
            final_capital = min(max(0, in_play_capital), max_capital)
            
            return final_capital
            
        except Exception as e:
            st.error(f"Erro no cálculo do capital: {str(e)}")
            return st.session_state.portfolio.capital * 0.09 if hasattr(st.session_state, 'portfolio') else 0

    def _get_priority_bets(self, home_goals, away_goals):
        """Define as apostas prioritárias baseadas no placar"""
        total_goals = home_goals + away_goals
        
        if total_goals == 0:
            return [BetType.OVER_15_FH, BetType.BOTH_TO_SCORE, BetType.OVER_15_MATCH]
        elif total_goals == 1:
            return [BetType.OVER_25, BetType.BOTH_TO_SCORE, BetType.DOUBLE_CHANCE_UNDERDOG]
        else:
            return [BetType.UNDER_35, BetType.BOTH_TO_SCORE, BetType.WINNER]
 
    def _render_probability_chart(self):
        """Renderiza o gráfico de probabilidades com Plotly"""
        condition = MatchCondition(
            score=self.state["score"],
            minute=self.state["minute"],
            home_pressure=self.state["home_pressure"],
            away_pressure=self.state["away_pressure"]
        )
        
        # Dados para o gráfico
        minutes = range(condition.minute, 91, 5)
        bet_types = [BetType.UNDER_25, BetType.BOTH_TO_SCORE]
        
        # Criar DataFrame com os dados
        data = []
        for m in minutes:
            for bt in bet_types:
                prob = self.system.optimizer.estimate_contextual_probability(bt, condition)
                data.append({
                    "Minuto": m,
                    "Probabilidade": prob,
                    "Tipo": bt.value
                })
        
        df = pd.DataFrame(data)
        
        # Criar gráfico interativo
        fig = px.line(
            df, 
            x="Minuto", 
            y="Probabilidade", 
            color="Tipo",
            title="Evolução das Probabilidades",
            labels={"Probabilidade": "Probabilidade (%)"},
            template="plotly_dark",
            line_shape="spline"  # Linhas suaves
        )
        
        # Personalizar layout
        fig.update_layout(
            hovermode="x unified",
            legend_title_text="Tipo de Aposta",
            xaxis_title="Minuto da Partida",
            yaxis_title="Probabilidade (%)",
            transition={'duration': 500}
        )
        
        # Exibir o gráfico
        st.plotly_chart(fig, use_container_width=True)
    
    def _display_probability_flow_chart(self, condition: MatchCondition, quantum_state: QuantumState):
        """Cria um gráfico que mostra o 'canto geométrico' das probabilidades."""
        # ... (código do gráfico permanece o mesmo) ...
        minutes = range(condition.minute, 91, 5)
        chart_data = []

        bet_types_to_chart = [BetType.UNDER_25, BetType.BOTH_TO_SCORE]

        for bt in bet_types_to_chart:
            probs = []
            for m in minutes:
                temp_cond = MatchCondition(condition.score, m, condition.home_pressure, condition.away_pressure)
                probs.append(self.system.optimizer.estimate_contextual_probability(bt, temp_cond))
            chart_data.append(pd.Series(probs, index=minutes, name=bt.value))
        
        df = pd.concat(chart_data, axis=1)
        st.line_chart(df)
        st.caption("Gráfico de Fluxo: Projeção da evolução das probabilidades até o final do jogo.")