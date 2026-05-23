import numpy as np
from scipy.integrate import solve_ivp

# Method for solving the system of ODEs. - 8(5)(3) order adaptive step size Runge-Kutta
ODE_METHOD = 'DOP853'

class Simulation:

    def __init__(
        self,
        populations,
        init_state,
        connection_matrix,
        infection_rate: float,
        recovery_rate: float,
        social_connectivity: float
    ):
        assert np.any(connection_matrix >= 0), 'Connection matrix should be non-negative'
        assert connection_matrix.shape[0] == connection_matrix.shape[1], 'Connection matrix should be square'
        assert (connection_matrix.shape[0]*3, ) == init_state.shape, 'Connection matrix should be NxN, no. of points = N, length of initial state = 3N'
        
        self.n_points = connection_matrix.shape[0]
        self.populations = populations
        self.init_state = init_state
        self.connection_matrix = connection_matrix
        self.infection_rate = infection_rate
        self.recovery_rate = recovery_rate
        self.social_connectivity = social_connectivity
        
        self.c_row_sums = np.sum(connection_matrix, axis = 1)
            
    def _differential(self, _, state):
                
        S_curr = state[:self.n_points]
        I_curr = state[self.n_points:2*self.n_points]
        R_curr = state[2*self.n_points:3*self.n_points]
        
        node_spread = self.infection_rate*S_curr*I_curr/self.populations
        network_spread = self.social_connectivity*self.infection_rate*S_curr/(self.populations + self.c_row_sums) * (self.connection_matrix @ (I_curr / self.populations))
        recovery = self.recovery_rate*I_curr/self.populations
        
        S_diff = -(node_spread + network_spread)
        I_diff = node_spread + network_spread - recovery
        R_diff = recovery 
        
        return np.concat((S_diff, I_diff, R_diff), axis = None)
    
    def solve_system(self, t_end: float):
        
        solution = solve_ivp(self._differential, (0, t_end), self.init_state, method = ODE_METHOD, max_step = 10)
        self.times = solution.t
        self.state_hist = solution.y
        
    def get_results(self):
        
        S = self.state_hist[:self.n_points, :]
        I = self.state_hist[self.n_points:2*self.n_points, :]
        R = self.state_hist[2*self.n_points:3*self.n_points, :]
        return (self.times, S, I, R)