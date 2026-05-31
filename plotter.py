import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np
import imageio
import os
import pandas as pd
from core import Simulation
from mpl_toolkits.mplot3d import Axes3D

def simple_plot(t, S, I, R):
    fig, ax = plt.subplots(figsize=(8, 6))
    stats = np.stack((S.T, I.T, R.T), axis=-1)
    stats_global = np.sum(stats, axis=1)
    stats_global = stats_global / np.sum(stats_global, axis=1, keepdims=True)


    labels = ["S", "I", "R"]
    colors = ["b", "r", "g"]

    for i, l in enumerate(labels):
        plt.plot(t, stats_global[:, i], label = l, color=colors[i])

    ax.set_xlabel("t [days]")
    ax.set_ylabel("Fraction of population")
    ax.legend()
    return ax

def generate_gif(time, S, I, R, eurostat_codes, gif_path = 'sir_eu_model_2x2_new.gif'):
    # ==========================================
    # 1. SETUP MAP GEOMETRY (GeoPandas 1.0 Fix)
    # ==========================================
    print("1. Downloading map geometry from Natural Earth...")
    url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
    world = gpd.read_file(url)
    world.rename(columns={'CONTINENT': 'continent', 'NAME': 'name', 'ISO_A3': 'iso_a3'}, inplace=True)

    # Patch France and Norway before filtering
    world.loc[world['name'] == 'France', 'iso_a3'] = 'FRA'
    world.loc[world['name'] == 'Norway', 'iso_a3'] = 'NOR'
    world.loc[world['name'] == 'Turkey', 'iso_a3'] = 'TUR'

    # Filter to Europe and remove missing data codes
    europe = world[(world.continent == 'Europe') | (world.iso_a3 == 'TUR')].copy()
    europe = europe[europe.iso_a3 != '-99']

    # ==========================================
    # 2. SETUP NODES AND DICTIONARY
    # ==========================================
    print("2. Setting up nodes and translating Eurostat to ISO3...")
    eurostat_to_iso3 = {
        'AT': 'AUT', 'BA': 'BIH', 'BE': 'BEL', 'BG': 'BGR', 'CH': 'CHE', 
        'CY': 'CYP', 'CZ': 'CZE', 'DE': 'DEU', 'DK': 'DNK', 'EE': 'EST', 
        'EL': 'GRC', 'ES': 'ESP', 'FI': 'FIN', 'FR': 'FRA', 'HR': 'HRV', 
        'HU': 'HUN', 'IE': 'IRL', 'IS': 'ISL', 'IT': 'ITA', 'LT': 'LTU', 
        'LU': 'LUX', 'LV': 'LVA', 'ME': 'MNE', 'MK': 'MKD', 'MT': 'MLT', 
        'NL': 'NLD', 'NO': 'NOR', 'PL': 'POL', 'PT': 'PRT', 'RO': 'ROU', 
        'RS': 'SRB', 'SE': 'SWE', 'SI': 'SVN', 'SK': 'SVK', 'TR': 'TUR'
    }

    # Translate your list
    modeled_iso3_codes = [eurostat_to_iso3[code] for code in eurostat_codes]

    # Generate Mock SIR Data (Replace this with your actual array!)
    # Shape: [30 Days, 35 Countries, 3 Compartments]
    sir_data = np.stack((S.T, I.T, R.T), axis=-1)
    sir_data = np.clip(sir_data / sir_data.sum(axis=2, keepdims=True), 0, 1)

    # ==========================================
    # 3. RENDER FRAMES TO TEMP FOLDER
    # ==========================================
    print("3. Generating frames...")
    filenames = []

    # Get the absolute path to your current working directory
    current_dir = os.getcwd()
    temp_dir = os.path.join(current_dir, 'temp_frames')

    # Create the folder safely
    os.makedirs(temp_dir, exist_ok=True)

    for t in range(len(time)):
        current_day = int(time[t])
        fig, axs = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle(f'EU Disease Spread - Day {current_day}', fontsize=16)
        
        day_data = sir_data[t, :, :]

        # Convert to fractions, strictly bound between 0 and 1
        sir_data = np.stack((S.T, I.T, R.T), axis=-1)
        sir_data = np.clip(sir_data / sir_data.sum(axis=2, keepdims=True), 0, 1)

        # --- NEW: Calculate average global trends for the stacked chart ---
        # Taking the mean across axis 1 (the nodes) gives us the continent-wide average
        global_trends = sir_data.mean(axis=1) 
        S_trend = global_trends[:, 0]
        I_trend = global_trends[:, 1]
        R_trend = global_trends[:, 2]

        # Pack this day's data into a DataFrame alongside the correct ISO3 codes
        df_day = pd.DataFrame({
            'ISO3': modeled_iso3_codes,
            'Color_S': [ (0, 0, s) for s in day_data[:, 0] ],
            'Color_I': [ (i, 0, 0) for i in day_data[:, 1] ],
            'Color_R': [ (0, r, 0) for r in day_data[:, 2] ],
        })
        
        # MERGE: Align the simulated data exactly to the map geometry
        europe_merged = europe.merge(df_day, left_on='iso_a3', right_on='ISO3', how='left')
        
        # Catch un-modeled countries (e.g. UK) and paint them light grey
        for col in ['Color_S', 'Color_I', 'Color_R']:
            europe_merged[col] = europe_merged[col].apply(
                lambda x: x if isinstance(x, tuple) else (0.9, 0.9, 0.9)
            )
        
        # Define mapping for the 4 subplots
        ax_stack = axs[1, 1]
        
        # Draw the stacked area chart
        ax_stack.stackplot(
            time, S_trend, I_trend, R_trend, 
            labels=['Susceptible', 'Infected', 'Recovered'], 
            colors=['#1f77b4', '#d62728', '#2ca02c'],
            alpha=0.7
        )
        
        # Draw the moving vertical line for the current day
        ax_stack.axvline(x=current_day, color='black', linestyle='--', linewidth=2.5)
        
        # Format the timeline chart
        ax_stack.set_title('Overall Pandemic Stage')
        ax_stack.set_xlim(time[0], time[-1])
        ax_stack.set_ylim(0, 1.0)
        ax_stack.set_xlabel('Days')
        ax_stack.set_ylabel('Fraction of Population')
        ax_stack.legend(loc='center right')

        # --- UPDATED INDENTATION & MAP FORMATTING ---
        # We only want to hide the axes and set boundaries for the 3 MAPS!
        # If we loop over axs.flat now, it will delete the axes from our new timeline chart.

        

        plot_configs = [
            (axs[0, 0], 'Color_S', 'Susceptible'),
            (axs[0, 1], 'Color_I', 'Infected'),
            (axs[1, 0], 'Color_R', 'Recovered'),
        ]
        
        
        # Draw the maps
        for ax, color_col, title in plot_configs:
            europe_merged.plot(ax=ax, color=europe_merged[color_col], edgecolor='black', linewidth=0.5)
            ax.set_title(title)
            ax.set_xlim(-25, 45)
            ax.set_ylim(35, 75)
            ax.axis('off') 
        
        # Save the frame
        filename = os.path.join(temp_dir, f'frame_{current_day:03d}.png')
        plt.tight_layout()
        plt.savefig(filename, dpi=100, bbox_inches='tight', facecolor='white')
        plt.close(fig) 
        filenames.append(filename)

    # ==========================================
    # 4. STITCH INTO GIF
    # ==========================================
    print("4. Stitching into GIF...")

    with imageio.get_writer(gif_path, mode='I', fps=5) as writer:
        for filename in filenames:
            image = imageio.imread(filename)
            writer.append_data(image)

    # Cleanup temporary PNG files
    # Cleanup temporary PNG files
    for filename in filenames:
        if os.path.exists(filename):
            os.remove(filename)
    if os.path.exists(temp_dir):
        os.rmdir(temp_dir)

    print(f"Success! GIF saved as: {gif_path}")

def social_connectivity_comp(population, init_state, C, t_end=360, infection_rate=0.1, recovery_rate=0.05,):
    # The social connectivity values (alpha) to iterate through
    alphas = [1.0, 0.8, 0.5, 0.4, 0.2, 0.1]
    subplot_labels = ['(a)', '(b)', '(c)', '(d)', '(e)', '(f)']

    # Create a 2x3 grid of subplots
    fig, axs = plt.subplots(2, 3, figsize=(18, 10))
    total_population = np.sum(population)

    for ax, alpha, label in zip(axs.flat, alphas, subplot_labels):
        # 1. Run the simulation for the current alpha
        sim = Simulation(
            populations=population,
            init_state=init_state,
            connection_matrix=C,
            infection_rate=infection_rate,       
            recovery_rate=recovery_rate, 
            social_connectivity=alpha,
        )
        
        sim.solve_system(t_end=t_end) 
        t, S, I, R = sim.get_results()
        
        # 2. Normalize to "Population Density" (Fractions 0.0 to 1.0)
        # Assuming S, I, R arrays return shape (time, nodes), sum across nodes to get the global trend
        S_density = np.sum(S, axis=0) / total_population
        I_density = np.sum(I, axis=0) / total_population
        R_density = np.sum(R, axis=0) / total_population
        
        # 3. Plot the curves matching the reference colors
        ax.plot(t, S_density, label='Susceptible', color='b', linewidth=2)
        ax.plot(t, I_density, label='Infected', color='r', linewidth=2)
        ax.plot(t, R_density, label='Recovered', color='g', linewidth=2)
        
        # 4. Format the subplot to match the academic paper style
        ax.set_title(f'{label} $\\alpha = {alpha}$', y=-0.2, fontsize=14) # Places label below X-axis
        ax.set_xlabel('Time [d]', fontsize=12)
        ax.set_ylabel('Fraction of population', fontsize=12)
        ax.legend(loc='center right')

    # Clean up spacing so labels don't overlap
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15) 
    plt.show()

def quarantine_plotter_3d(population, init_state, C, infection_rate, recovery_rate, t_end=360, quarantine_top=100):
    # 1. Define the "Net" (Mesh parameters)
    # Let's test 25 different quarantine levels, from 0% reduction to 95% reduction
    quarantine_pcts = np.linspace(0, 0.95, 25) 

    # Prepare empty lists to hold our Z-axis heights
    Z_S = []
    Z_I = []
    Z_R = []

    total_population = np.sum(population)

    # 2. Run the simulation for every quarantine level
    for q in quarantine_pcts:
        # A 30% quarantine (0.3) means social connectivity operates at 70% (0.7)
        current_connectivity = 1.0 - q 
        
        sim = Simulation(
            populations=population,
            init_state=init_state,
            connection_matrix=C,
            infection_rate=infection_rate,       
            recovery_rate=recovery_rate, 
            social_connectivity=current_connectivity, 
        )
        sim.solve_system(t_end=t_end, t_eval=np.linspace(0, t_end, t_end))
        t_array, S, I, R = sim.get_results()
        
        # Calculate global densities for this specific run
        Z_S.append(np.sum(S, axis=0) / total_population)
        Z_I.append(np.sum(I, axis=0) / total_population)
        Z_R.append(np.sum(R, axis=0) / total_population)

    # 3. Convert our lists into 2D matrices
    Z_S = np.array(Z_S)
    Z_I = np.array(Z_I)
    Z_R = np.array(Z_R)

    # Create the 2D meshgrid for X (Time) and Y (Quarantine %)
    # We multiply q by 100 just so the Y-axis reads cleanly as 0 to 95
    T, Q = np.meshgrid(t_array, quarantine_pcts * 100) 

    # 4. Draw the 3D Plots
    # We need a wide figure to fit three 3D plots side-by-side
    fig = plt.figure(figsize=(20, 7))

    # --- Plot 1: Susceptible ---
    # 'projection=3d' tells Matplotlib to render a 3-dimensional box
    ax1 = fig.add_subplot(1, 3, 1, projection='3d')
    # cmap adds the color gradient, alpha makes it slightly transparent
    ax1.plot_surface(T, Q, Z_S, cmap='Blues', edgecolor='none', alpha=0.8)
    ax1.set_title('Susceptible Fraction', fontsize=14)
    ax1.set_xlabel('Time (Days)')
    ax1.set_ylabel('Quarantine Reduction (%)')
    ax1.set_zlabel('Population Density')
    ax1.set_zlim(0, 1)

    # --- Plot 2: Infected ---
    ax2 = fig.add_subplot(1, 3, 2, projection='3d')
    ax2.plot_surface(T, Q, Z_I, cmap='Reds', edgecolor='none', alpha=0.8)
    ax2.set_title('Infected Fraction', fontsize=14)
    ax2.set_xlabel('Time (Days)')
    ax2.set_ylabel('Quarantine Reduction (%)')
    ax2.set_zlabel('Population Density')
    ax2.set_zlim(0, 1)

    # --- Plot 3: Recovered ---
    ax3 = fig.add_subplot(1, 3, 3, projection='3d')
    ax3.plot_surface(T, Q, Z_R, cmap='Greens', edgecolor='none', alpha=0.8)
    ax3.set_title('Recovered Fraction', fontsize=14)
    ax3.set_xlabel('Time (Days)')
    ax3.set_ylabel('Quarantine Reduction (%)')
    ax3.set_zlabel('Population Density')
    ax3.set_zlim(0, 1)

    # Adjust viewing angle for better perspective (Elevation, Azimuth)
    for ax in [ax1, ax2, ax3]:
        ax.view_init(elev=25, azim=-50)

    plt.tight_layout()
    plt.show()

def quarantine_plotter_2d(population, init_state, C, infection_rate, recovery_rate, t_end=360):

    # 1. Select a few distinct quarantine levels to compare
    # (Using too many lines makes a 2D plot impossible to read)
    quarantine_levels = [0.0, 0.25, 0.50, 0.75, 0.90]

    # Create a 1 row, 3 column grid of standard 2D plots
    fig, axs = plt.subplots(1, 3, figsize=(18, 6))
    total_population = np.sum(population)

    # 2. Loop through each quarantine level and plot its line
    for q in quarantine_levels:
        current_connectivity = 1.0 - q
        
        sim = Simulation(
            populations=population,
            init_state=init_state,
            connection_matrix=C,
            infection_rate=infection_rate,       
            recovery_rate=recovery_rate, 
            social_connectivity=current_connectivity, 
        )
        sim.solve_system(t_end=t_end)
        t_ragged, S, I, R = sim.get_results()
        
        # CRITICAL: Sum across axis=0 to combine all countries into a global trend
        S_density = np.sum(S, axis=0) / total_population
        I_density = np.sum(I, axis=0) / total_population
        R_density = np.sum(R, axis=0) / total_population
        
        # Label for the legend
        label_text = f"Quarantine {int(q*100)}%"
        
        # Plot this scenario's lines across the 3 subplots
        axs[0].plot(t_ragged, S_density, label=label_text, linewidth=2)
        axs[1].plot(t_ragged, I_density, label=label_text, linewidth=2)
        axs[2].plot(t_ragged, R_density, label=label_text, linewidth=2)

    # 3. Format each individual subplot
    axs[0].set_title('Susceptible Fraction', fontsize=14)
    axs[1].set_title('Infected Fraction (The Curve)', fontsize=14)
    axs[2].set_title('Recovered Fraction', fontsize=14)

    for ax in axs:
        ax.set_xlabel('Time (Days)', fontsize=12)
        ax.set_ylabel('Population Density', fontsize=12)
        ax.set_ylim(-0.05, 1.05)
        ax.legend(loc='best', fontsize=10)

    plt.tight_layout()
    plt.show()

def local_vs_global_quarantine(population, init_state, C, infection_rate, recovery_rate, 
                               t_end=360,
                               top_nodes_under_quarantine=5,
                               quarantine_range=np.linspace(0, 1, 10), 
                               social_connectivity_range=np.linspace(0, 1, 10), display="both"):
    
    X_alpha = []
    Y_outside = []
    Z_value = []
    Z_time = []
    
    total_population = np.sum(population)
    top_nodes_idx = np.argsort(population)[::-1]
    
    print(f"Running {len(quarantine_range) * len(social_connectivity_range)} simulations. Please wait...")

    # 1. Run the Simulations
    for alpha in social_connectivity_range:
        for q in quarantine_range:
            current_C = C.copy() 
            num_to_quarantine = top_nodes_under_quarantine
            
            if num_to_quarantine > 0:
                quarantined_indices = top_nodes_idx[:num_to_quarantine]
                current_C[quarantined_indices, :] = current_C[quarantined_indices, :] * q
                current_C[:, quarantined_indices] = current_C[:, quarantined_indices] * q
            
            sim = Simulation(
                populations=population,
                init_state=init_state,
                connection_matrix=current_C,
                infection_rate=infection_rate,
                recovery_rate=recovery_rate,
                social_connectivity=alpha,
            )
            sim.solve_system(t_end=t_end)
            t_array, S, I, R = sim.get_results()
            
            I_global = np.sum(I, axis=0) / total_population
            
            # Since performance isn't an issue, just calculate both metric lists universally
            X_alpha.append(alpha)
            Y_outside.append(q)
            Z_time.append(t_array[np.argmax(I_global)])
            Z_value.append(np.max(I_global))

    # Convert to NumPy arrays
    X_alpha = np.array(X_alpha)
    Y_outside = np.array(Y_outside)
    Z_time = np.array(Z_time)
    Z_value = np.array(Z_value)

    # ==========================================
    # Helper Function to Keep Code DRY (Don't Repeat Yourself)
    # ==========================================
    def draw_3d_scatter(ax, Z_data, z_label):
        # Main 3D Scatter
        ax.scatter(X_alpha, Y_outside, Z_data, 
                   c=Z_data, cmap='viridis', s=20, alpha=0.8, edgecolors='none')
        # The "Shadow" Floor
        ax.scatter(X_alpha, Y_outside, np.zeros_like(Z_data), 
                   c=np.zeros_like(Z_data), cmap='viridis', 
                   vmin=np.min(Z_data), vmax=np.max(Z_data), 
                   s=20, alpha=0.3, edgecolors='none')

        ax.set_xlabel(r'$\alpha$ (Social Connectivity)', fontsize=12, labelpad=8)
        ax.set_ylabel('Closing down largest airports', fontsize=12, labelpad=8)
        ax.set_zlabel(z_label, fontsize=12, labelpad=10)
        
        ax.view_init(elev=25, azim=-60)
        ax.set_box_aspect(None, zoom=0.9) 
        
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False

    # ==========================================
    # Plotting Logic
    # ==========================================
    if display == "time":
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        draw_3d_scatter(ax, Z_time, 'Time to Peak Infection (Days)')
        plt.tight_layout(pad=3.0)
        plt.show()
        
    elif display == "value":
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        draw_3d_scatter(ax, Z_value, 'Value of Peak Infection (ratio)')
        plt.tight_layout(pad=3.0)
        plt.show()
        
    else: # "both"
        fig = plt.figure(figsize=(20, 8))
        
        ax1 = fig.add_subplot(1, 2, 1, projection='3d')
        draw_3d_scatter(ax1, Z_time, 'Time to Peak Infection (Days)')
        
        ax2 = fig.add_subplot(1, 2, 2, projection='3d')
        draw_3d_scatter(ax2, Z_value, 'Value of Peak Infection (ratio)')

        # THE FIX: Explicit padding values prevent the 1x2 layout from cropping the Z labels
        plt.tight_layout(pad=4.0, w_pad=5.0)
        plt.show()