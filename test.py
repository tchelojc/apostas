import pytest
from quantum_betting import BettingSystem, BetPhase, BetType
from quantum_optimizer import QuantumOptimizer, MatchCondition

@pytest.fixture
def betting_system():
    system = BettingSystem()
    system._init_session_state()
    return system

def test_initial_configuration(betting_system):
    """Testa a configuração inicial com valores válidos"""
    initial_capital = 100.0
    odds = {
        BetType.UNDER_25: 1.8,
        BetType.OVER_15_FH: 2.1,
        BetType.BOTH_TO_SCORE: 1.9,
        BetType.WINNER: 1.5,
        BetType.UNDER_15: 2.5,
        BetType.NO_GOAL: 1.8
    }
    
    # Verifica se a configuração inicial é aceita
    assert betting_system.enter_initial_config(initial_capital, odds) == True
    assert betting_system.state.phase == BetPhase.PRE_MATCH
    assert betting_system.state.initial_capital == initial_capital
    assert len(betting_system.state.odds) == 6

def test_pre_match_allocation(betting_system):
    """Testa a alocação de apostas pré-jogo"""
    # Configura estado inicial
    initial_capital = 100.0
    odds = {
        BetType.UNDER_25: 1.8,
        BetType.OVER_15_FH: 2.1,
        BetType.BOTH_TO_SCORE: 1.9,
        BetType.WINNER: 1.5,
        BetType.UNDER_15: 2.5,
        BetType.NO_GOAL: 1.8
    }
    betting_system.enter_initial_config(initial_capital, odds)
    
    # Verifica alocação pré-jogo
    assert betting_system.place_pre_match_bets() == True
    assert betting_system.state.phase == BetPhase.MULTI_MATCH
    assert len(betting_system.state.active_bets) > 0
    
    # Verifica se a alocação total é ~60% do capital
    total_allocated = sum(bet.amount for bet in betting_system.state.active_bets)
    assert pytest.approx(total_allocated, 0.1) == initial_capital * 0.60

def test_multi_match_creation(betting_system):
    """Testa a criação de apostas múltiplas"""
    # Configura estado inicial
    initial_capital = 100.0
    odds = {
        BetType.UNDER_25: 1.8,
        BetType.OVER_15_FH: 2.1,
        BetType.BOTH_TO_SCORE: 1.9,
        BetType.WINNER: 1.5,
        BetType.UNDER_15: 2.5,
        BetType.NO_GOAL: 1.8
    }
    betting_system.enter_initial_config(initial_capital, odds)
    betting_system.place_pre_match_bets()
    
    # Cria combinações para múltiplas
    combinations = [{
        'matches': ["Match_A", "Match_B"],
        'bet_types': [BetType.UNDER_25, BetType.BOTH_TO_SCORE]
    }]
    
    # Verifica criação de múltiplas
    assert betting_system.create_multi_bets(combinations) == True
    assert betting_system.state.phase == BetPhase.LIVE_MONITORING
    assert len(betting_system.state.multi_bets) > 0
    
    # Verifica se a alocação total é ~31% do capital
    total_allocated = sum(bet.total_amount for bet in betting_system.state.multi_bets)
    assert pytest.approx(total_allocated, 0.1) == initial_capital * 0.31