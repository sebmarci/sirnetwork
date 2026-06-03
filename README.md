# sirnetwork
A virus spreading model utilizing SIR dynamics on a finite graph.

### Working principle

The model this code implements is a force-of-infection based connectivity matrix SIR model. The code solves the following system of ODEs:

$$\frac{dS_i}{dt} = -\lambda_i S_i(t)$$

$$\frac{dI_i}{dt} = \lambda_i S_i(t) - \mu I_i(t)$$

$$\frac{dR_i}{dt} = \mu I_i(t)$$

where

$$\lambda_i = \beta \sum_j c_{ij} \frac{I_j(t)}{N_j}$$

is the force of infection of node (city) $i$. $S_i(t), I_i(t), R_i(t)$ are the susceptible, infected and removed populations of node $i$, and the total population of node $i$ is $N_i = S_i(t) + I_i(t) + R_i(t)$. 

The parameters of the simulation:

- $\beta$: Infection rate
- $\mu$: recovery rate
- $c_{ij}$: Normalized social connectivity matrix. Infection inside cities is represented by the diagonal elements $c_{ii}$, while inter-city spread is represented by the off-diagonal elements $c_{ij}$. We remark that we use the convention $\sum_j c_{ij} = 1$ for all $i$. Then the effective contact rate matrix is $C_{ij} = \beta c_{ij}$. 

The class `Simulation` handles the ODE solving with a DOP853 explicit Runge-Kutta method (w. adaptive step size). - See `example.ipynb` for an example.