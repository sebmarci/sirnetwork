# sirnetwork
A virus spreading model utilizing SIR dynamics on a finite graph.

### Working principle

The model is based on the article: R. Goel et al. "Mobility‐based SIR model for complex networks: with case study Of COVID‐19". Social Network Analysis and Mining (2021) 11:105. DOI: https://doi.org/10.1007/s13278-021-00814-3

The code solves the following system of ODEs:

$$\frac{dS_i}{dt} = -\frac{\beta S_i(t) I_i(t)}{N_i(t)} - \frac{\alpha \beta S_i(t) \sum_j c_{ij} I_j(t) / N_j(t)}{N_i(t) + \sum_j c_{ij}}$$

$$\frac{dI_i}{dt} = \frac{\beta S_i(t) I_i(t)}{N_i(t)} + \frac{\alpha \beta S_i(t) \sum_j c_{ij} I_j(t) / N_j(t)}{N_i(t) + \sum_j c_{ij}} - \frac{\mu I_i(t)}{N_i(t)}$$

$$\frac{dR_i}{dt} = \frac{\mu I_i(t)}{N_i(t)}$$

Where $S_i(t), I_i(t), R_i(t)$ are the susceptible, infected and removed populations of node $i$, and the total population of node $i$ is $N_i = S_i(t) + I_i(t) + R_i(t)$. 

The parameters of the simulation:

- $\alpha$: Social connectivity (network coupling strength)
- $\beta$: Infection rate
- $\mu$: recovery rate
- $c_{ij}$: Social connectivity matrix. The rate of transmission from node $j$ to node $i$ is proportional to $c_{ij}$. 

The class `Simulation` handles the ODE solving with a DOP853 explicit Runge-Kutta method (w. adaptive step size). - See `example.ipynb` for an example.