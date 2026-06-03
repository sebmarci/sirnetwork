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
                    
    def _differential(self, _, state):
                
        S_curr = state[:self.n_points]
        I_curr = state[self.n_points:2*self.n_points]
        R_curr = state[2*self.n_points:3*self.n_points]
        
        force_of_infection = self.connection_matrix @ (S_curr / self.populations)
        
        S_diff = -force_of_infection * S_curr 
        I_diff = force_of_infection * S_curr - self.recovery_rate * I_diff
        R_diff = self.recovery_rate * I_diff
        
        return np.concat((S_diff, I_diff, R_diff), axis = None)
    
    def solve_system(self, t_end: float, t_eval=None):
        
        solution = solve_ivp(self._differential, (0, t_end), self.init_state, method = ODE_METHOD, max_step = 10, t_eval=t_eval)
        self.times = solution.t
        self.state_hist = solution.y
        
    def get_results(self):
        
        S = self.state_hist[:self.n_points, :]
        I = self.state_hist[self.n_points:2*self.n_points, :]
        R = self.state_hist[2*self.n_points:3*self.n_points, :]
        return (self.times, S, I, R)