# project/bridge.py
class SystemBridge:
    def __init__(self):
        self.modules = {}
        
    def register_module(self, name, module):
        self.modules[name] = module
        
    def get_module(self, name):
        return self.modules.get(name)
        
    def get_multi_bets_data(self):
        if 'multi_bets' in self.modules:
            return {
                'combos': self.modules['multi_bets'].state['selected_combos'],
                'amounts': self.modules['multi_bets'].state['calculated_amounts']
            }
        return None